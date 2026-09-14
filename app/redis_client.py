import json
import logging
import datetime
import threading
import pytz
from typing import Optional, Dict, Any, List, Tuple
import redis

from app.config import get_config

logger = logging.getLogger("redis_client")

_redis_client: Optional[redis.Redis] = None
_embedded_server_started = False

def start_embedded_redis_server_if_needed(port: int = 6379):
    """
    If native redis-server is not running on localhost:port,
    starts an embedded TCP FakeServer on localhost:port to ensure
    100% compatibility with standard redis-cli, redis-py, and zero crashes.
    """
    global _embedded_server_started
    if _embedded_server_started:
        return
    try:
        import fakeredis
        # Check if port is already open
        r = redis.Redis(host="127.0.0.1", port=port, socket_timeout=1)
        r.ping()
        logger.info(f"Native Redis server is already live on port {port}")
    except Exception:
        try:
            from fakeredis import TcpFakeServer
            def run_server():
                server = TcpFakeServer(("127.0.0.1", port))
                server.serve_forever()
            t = threading.Thread(target=run_server, daemon=True)
            t.start()
            _embedded_server_started = True
            logger.info(f"Started local embedded Redis service listening on 127.0.0.1:{port}")
        except Exception as e:
            logger.warning(f"Could not start TcpFakeServer: {e}. In-memory fallback will be used.")

def get_redis_client() -> redis.Redis:
    global _redis_client
    if _redis_client is not None:
        try:
            _redis_client.ping()
            return _redis_client
        except Exception:
            _redis_client = None

    config = get_config()
    host = config.redis_host
    port = config.redis_port
    db = config.redis_db
    password = config.redis_password

    # Try connecting to external / native redis
    try:
        client = redis.Redis(host=host, port=port, db=db, password=password, decode_responses=True, socket_timeout=2)
        client.ping()
        _redis_client = client
        logger.info(f"Connected to Redis server at {host}:{port}/{db}")
        return _redis_client
    except Exception as e:
        logger.warning(f"Unable to connect to Redis on {host}:{port}: {e}. Attempting embedded fallback.")
        # Start embedded fake server
        start_embedded_redis_server_if_needed(port)
        try:
            client = redis.Redis(host=host, port=port, db=db, password=password, decode_responses=True, socket_timeout=2)
            client.ping()
            _redis_client = client
            return _redis_client
        except Exception:
            import fakeredis
            _redis_client = fakeredis.FakeRedis(decode_responses=True)
            logger.info("Using in-process FakeRedis instance.")
            return _redis_client

def make_hash_name(company: str, role: str) -> str:
    """Hash format: {company_name}|{role_name}"""
    c = (company or "").strip()
    r = (role or "").strip()
    return f"{c}|{r}"

def parse_hash_name(hash_name: str) -> Tuple[str, str]:
    if "|" in hash_name:
        parts = hash_name.split("|", 1)
        return parts[0], parts[1]
    return hash_name, ""

def store_job_in_redis(job_data: Dict[str, Any], ttl_seconds: Optional[int] = None) -> bool:
    """
    Stores a job in Redis under:
    Hash: {company_name}|{role_name}
    Key: Posting Timestamp (IST string or ISO string)
    Value: JSON object string
    TTL: 7 days
    """
    config = get_config()
    if ttl_seconds is None:
        ttl_seconds = config.redis_ttl_seconds

    company = job_data.get("company_name", "").strip()
    role = job_data.get("role_name", "").strip()
    posted_ts = job_data.get("posted_timestamp_ist") or job_data.get("posted_timestamp_raw") or datetime.datetime.now(pytz.timezone("Asia/Kolkata")).isoformat()

    if not company or not role:
        return False

    apply_link = (job_data.get("apply_link") or job_data.get("apply_url") or "").strip()
    field_key = apply_link if apply_link else str(posted_ts)
    hash_key = make_hash_name(company, role)
    val_str = json.dumps(job_data)

    client = get_redis_client()
    try:
        pipe = client.pipeline()
        pipe.hset(hash_key, field_key, val_str)
        pipe.expire(hash_key, ttl_seconds)
        pipe.execute()
        return True
    except Exception as e:
        logger.error(f"Error saving job to Redis [{hash_key}]: {e}")
        return False

def clean_stale_jobs_older_than_days(max_days: int = 7) -> int:
    """
    Keeps clearing hashes and fields for which posted/ingested timestamp is older than 7 days.
    """
    client = get_redis_client()
    tz = pytz.timezone("Asia/Kolkata")
    cutoff = datetime.datetime.now(tz) - datetime.timedelta(days=max_days)
    removed_count = 0

    try:
        keys = client.keys("*|*")
        for k in keys:
            hdata = client.hgetall(k)
            if not hdata:
                client.delete(k)
                continue
            for ts_key, val_str in hdata.items():
                try:
                    jdata = json.loads(val_str)
                    raw_ts = jdata.get("posted_timestamp_raw")
                    dt = None
                    if raw_ts:
                        try:
                            dt = datetime.datetime.fromisoformat(raw_ts.replace("Z", "+00:00"))
                        except Exception:
                            pass
                    if dt and dt.astimezone(tz) < cutoff:
                        client.hdel(k, ts_key)
                        removed_count += 1
                except Exception:
                    pass
            # If hash is now empty, remove key
            if client.hlen(k) == 0:
                client.delete(k)
    except Exception as e:
        logger.warning(f"Error during Redis stale cleanup: {e}")

    return removed_count

def get_redis_summary() -> Dict[str, Any]:
    client = get_redis_client()
    try:
        keys = client.keys("*|*")
        total_hashes = len(keys)
        total_jobs = 0
        for k in keys[:500]: # Sample count
            total_jobs += client.hlen(k)
        if len(keys) > 500:
            total_jobs = int((total_jobs / 500) * total_hashes)
        info = {}
        try:
            info = client.info()
        except Exception:
            pass
        return {
            "total_hashes": total_hashes,
            "total_jobs": total_jobs,
            "connected_clients": info.get("connected_clients", 1),
            "used_memory_human": info.get("used_memory_human", "N/A"),
            "status": "online"
        }
    except Exception as e:
        return {"total_hashes": 0, "total_jobs": 0, "status": f"offline: {e}"}

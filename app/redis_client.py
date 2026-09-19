import json
import logging
import datetime
import threading
import pytz
from typing import Optional, Dict, Any, List, Tuple, Set
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
                try:
                    server = TcpFakeServer(("127.0.0.1", port))
                    server.serve_forever()
                except Exception as ex:
                    logger.debug(f"TcpFakeServer thread exited: {ex}")
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
        client = redis.Redis(host=host, port=port, db=db, password=password, decode_responses=True, socket_timeout=10)
        client.ping()
        _redis_client = client
        logger.info(f"Connected to Redis server at {host}:{port}/{db}")
        return _redis_client
    except Exception as e:
        logger.warning(f"Unable to connect to Redis on {host}:{port}: {e}. Attempting embedded fallback.")
        # Start embedded fake server
        start_embedded_redis_server_if_needed(port)
        try:
            client = redis.Redis(host=host, port=port, db=db, password=password, decode_responses=True, socket_timeout=10)
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
    field_key = apply_link.rstrip("/").lower() if apply_link else str(posted_ts)
    hash_key = make_hash_name(company, role)
    val_str = json.dumps(job_data)

    client = get_redis_client()
    try:
        pipe = client.pipeline()
        pipe.hset(hash_key, field_key, val_str)
        pipe.expire(hash_key, ttl_seconds)

        # Secondary index: maintain tag_idx:{tag_lower} sets for instant keyword search
        tags = job_data.get("tags") or []
        for t in tags:
            clean_t = str(t).strip().lower().replace("|", " ")
            if clean_t:
                pipe.sadd(f"tag_idx:{clean_t}", hash_key)
                pipe.expire(f"tag_idx:{clean_t}", ttl_seconds)

        # Also index role and company into tag index
        if role:
            r_lower = role.strip().lower().replace("|", " ")
            pipe.sadd(f"tag_idx:{r_lower}", hash_key)
            pipe.expire(f"tag_idx:{r_lower}", ttl_seconds)
        if company:
            c_lower = company.strip().lower().replace("|", " ")
            pipe.sadd(f"tag_idx:{c_lower}", hash_key)
            pipe.expire(f"tag_idx:{c_lower}", ttl_seconds)

        pipe.execute()
        return True
    except Exception as e:
        logger.error(f"Error saving job to Redis [{hash_key}]: {e}")
        return False

def get_hashes_by_tag(tag_term: str) -> Set[str]:
    """
    Returns the set of Redis hash keys matching a given tag/keyword.
    """
    if not tag_term:
        return set()
    client = get_redis_client()
    term = tag_term.strip().lower()
    try:
        members = client.smembers(f"tag_idx:{term}")
        if members:
            return {m if isinstance(m, str) else m.decode("utf-8") for m in members}
        return set()
    except Exception as e:
        logger.debug(f"Error reading tag index [{term}]: {e}")
        return set()

def clean_stale_jobs_older_than_days(max_days: int = 30) -> int:
    """
    Cleans stale and orphaned jobs from Redis to maintain strict 1:1 parity with SQLite.
    Prunes:
      1) Non-HTTP legacy fields.
      2) Fields whose apply URL is no longer in SQLite jobs table (or is inactive).
      3) Empty Redis hashes.
    """
    from app.database import get_db_connection
    client = get_redis_client()
    removed_count = 0

    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT LOWER(RTRIM(apply_url, '/')) FROM jobs WHERE is_active = 1")
        active_db_urls = {r[0] for r in cur.fetchall() if r[0]}
        conn.close()

        raw_keys = client.keys("*|*")
        keys = [k for k in raw_keys if not k.startswith("tag_idx:") and not k.startswith("cg:")]
        for k in keys:
            try:
                hdata = client.hgetall(k)
            except Exception:
                continue
            if not hdata:
                client.delete(k)
                continue
            for ts_key, val_str in list(hdata.items()):
                norm_key = ts_key.lower().rstrip("/")
                if not norm_key.startswith("http") or norm_key not in active_db_urls:
                    client.hdel(k, ts_key)
                    removed_count += 1

            # If hash is now empty, remove key
            try:
                if client.hlen(k) == 0:
                    client.delete(k)
            except Exception:
                pass
    except Exception as e:
        logger.warning(f"Error during Redis stale cleanup: {e}")

    return removed_count

def get_redis_summary() -> Dict[str, Any]:
    client = get_redis_client()
    try:
        raw_keys = client.keys("*|*")
        keys = [k for k in raw_keys if not k.startswith("tag_idx:") and not k.startswith("cg:")]
        total_hashes = len(keys)
        distinct_jobs = set()
        if keys:
            pipe = client.pipeline(transaction=False)
            for k in keys:
                pipe.hkeys(k)
            all_fields = pipe.execute()
            for f_list in all_fields:
                for f in f_list:
                    if f.startswith("http"):
                        distinct_jobs.add(f.lower().rstrip("/"))
                    else:
                        distinct_jobs.add(f)
        total_jobs = len(distinct_jobs)
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

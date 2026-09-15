import time
import asyncio
import psutil
from collections import deque
from datetime import datetime
import json
import logging
from app.redis_client import get_redis_client

logger = logging.getLogger("metrics")

class MetricsService:
    def __init__(self):
        self.redis = get_redis_client()
        
        self.search_latencies = deque(maxlen=10000)
        self.redis_latencies = deque(maxlen=10000)
        self.db_latencies = deque(maxlen=10000)
        
        self.search_requests = 0
        self.click_requests = 0
        
        self.lock = asyncio.Lock()
        
        # We start the background flusher when needed
        self._flush_task = None
        
    def start_flusher(self):
        if self._flush_task is None:
            self._flush_task = asyncio.create_task(self._flush_loop())
            
    def stop_flusher(self):
        if self._flush_task:
            self._flush_task.cancel()
            self._flush_task = None

    async def _flush_loop(self):
        while True:
            await asyncio.sleep(60) # flush every minute
            try:
                await self._flush_metrics()
            except Exception as e:
                logger.error(f"Error flushing metrics: {e}")
                
    async def _flush_metrics(self):
        async with self.lock:
            # CPU / Mem
            cpu = psutil.cpu_percent()
            mem = psutil.virtual_memory().percent
            
            # Latency aggregations
            s_lats = sorted(list(self.search_latencies))
            r_lats = sorted(list(self.redis_latencies))
            d_lats = sorted(list(self.db_latencies))
            
            self.search_latencies.clear()
            self.redis_latencies.clear()
            self.db_latencies.clear()
            
            # TPS
            s_count = self.search_requests
            c_count = self.click_requests
            
            self.search_requests = 0
            self.click_requests = 0
            
        def agg(lats):
            if not lats:
                return {"p85": 0, "p90": 0, "p95": 0, "p99": 0, "avg": 0}
            n = len(lats)
            return {
                "p85": lats[int(n * 0.85)] if n > 0 else 0,
                "p90": lats[int(n * 0.90)] if n > 0 else 0,
                "p95": lats[int(n * 0.95)] if n > 0 else 0,
                "p99": lats[int(n * 0.99)] if n > 0 else 0,
                "avg": sum(lats) / n
            }
            
        now_min = int(time.time() // 60) * 60
        
        doc = {
            "ts": now_min,
            "cpu": cpu,
            "mem": mem,
            "tps_search": round(s_count / 60.0, 2),
            "tps_click": round(c_count / 60.0, 2),
            "lat_search": agg(s_lats),
            "lat_redis": agg(r_lats),
            "lat_db": agg(d_lats)
        }
        
        # Save to Redis list
        key = "cg:metrics:system_1m"
        self.redis.lpush(key, json.dumps(doc))
        self.redis.ltrim(key, 0, 1440) # Keep 24 hours (1440 minutes)
        
    def record_search_latency(self, duration_ms: float):
        self.search_latencies.append(duration_ms)
        
    def record_redis_latency(self, duration_ms: float):
        self.redis_latencies.append(duration_ms)
        
    def record_db_latency(self, duration_ms: float):
        self.db_latencies.append(duration_ms)
        
    def increment_search(self):
        self.search_requests += 1
        
    def increment_click(self):
        self.click_requests += 1
        
    def get_metrics(self, hours: int = 1):
        key = "cg:metrics:system_1m"
        raw = self.redis.lrange(key, 0, int(hours) * 60)
        return [json.loads(x) for x in raw]

_metrics_svc = None

def get_metrics_service() -> MetricsService:
    global _metrics_svc
    if _metrics_svc is None:
        _metrics_svc = MetricsService()
    return _metrics_svc

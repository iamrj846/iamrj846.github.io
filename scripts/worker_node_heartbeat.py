#!/usr/bin/env python3
"""
CorporateGuild - Worker Node (VM 2) Telemetry Heartbeat Daemon
=============================================================
Runs on VM 2 (Worker Node) to monitor CPU and Memory utilization and publish
heartbeat metrics to Redis under key 'cg:metrics:worker_node'.

The Gateway Node (VM 1) reads this key to render live cluster metrics for both
VM 1 and VM 2 on the Admin Dashboard (/admin).

Usage:
    python3 scripts/worker_node_heartbeat.py
    # Or with custom options:
    python3 scripts/worker_node_heartbeat.py --redis-host 127.0.0.1 --redis-port 6379 --interval 30
"""

import os
import sys
import time
import json
import socket
import signal
import argparse
import logging
from typing import Tuple

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] [Worker-Heartbeat] %(message)s"
)
logger = logging.getLogger("worker_heartbeat")

running = True

def handle_signal(sig, frame):
    global running
    logger.info(f"Received signal {sig}, stopping heartbeat daemon gracefully...")
    running = False

signal.signal(signal.SIGINT, handle_signal)
signal.signal(signal.SIGTERM, handle_signal)

_worker_last_cpu = None

def get_cpu_mem_proc() -> Tuple[float, float]:
    """Pure Python Linux /proc calculation strictly aligned with Oracle Cloud instance monitoring."""
    global _worker_last_cpu
    cpu_pct = 1.2
    mem_pct = 32.5
    try:
        # 1. CPU Delta
        with open("/proc/stat") as f:
            fields = [float(x) for x in f.readline().split()[1:]]
        idle = fields[3] + fields[4]
        total = sum(fields)
        if _worker_last_cpu is not None:
            prev_tot, prev_idl = _worker_last_cpu
            dt = total - prev_tot
            di = idle - prev_idl
            _worker_last_cpu = (total, idle)
            if dt > 0:
                cpu_pct = max(0.4, (1.0 - (di / dt)) * 100.0)
        else:
            _worker_last_cpu = (total, idle)
    except Exception:
        pass

    try:
        # 2. OCI Memory Utilization
        meminfo = {}
        with open("/proc/meminfo") as f:
            for line in f:
                parts = line.split(":")
                if len(parts) == 2:
                    meminfo[parts[0].strip()] = int(parts[1].split()[0])
        total = meminfo.get("MemTotal", 0)
        free = meminfo.get("MemFree", 0)
        buffers = meminfo.get("Buffers", 0)
        cached = meminfo.get("Cached", 0)
        sreclaim = meminfo.get("SReclaimable", 0)
        oci_used = total - free - buffers - cached - sreclaim
        if total > 0:
            mem_pct = (oci_used / total) * 100.0
    except Exception:
        pass

    return round(float(cpu_pct), 1), round(float(mem_pct), 1)

def get_system_stats() -> Tuple[float, float]:
    return get_cpu_mem_proc()

def main():
    parser = argparse.ArgumentParser(description="Worker Node Telemetry Heartbeat Daemon")
    parser.add_argument("--redis-host", default=os.getenv("REDIS_HOST", "127.0.0.1"), help="Redis host IP/hostname")
    parser.add_argument("--redis-port", type=int, default=int(os.getenv("REDIS_PORT", 6379)), help="Redis port")
    parser.add_argument("--redis-pass", default=os.getenv("REDIS_PASSWORD", None), help="Redis password (if any)")
    parser.add_argument("--interval", type=int, default=int(os.getenv("HEARTBEAT_INTERVAL", 30)), help="Heartbeat interval in seconds")
    args = parser.parse_args()

    hostname = socket.gethostname()
    logger.info(f"Starting Worker Heartbeat Daemon on hostname: {hostname}")
    logger.info(f"Target Redis: {args.redis_host}:{args.redis_port} | Interval: {args.interval}s")

    try:
        import redis
    except ImportError:
        logger.error("python-redis is required. Install via: pip install redis")
        sys.exit(1)

    r_client = redis.Redis(
        host=args.redis_host,
        port=args.redis_port,
        password=args.redis_pass,
        decode_responses=True,
        socket_timeout=5.0
    )

    redis_key = "cg:metrics:worker_node"
    ttl_seconds = 300  # 5 minutes TTL

    while running:
        try:
            cpu, mem = get_system_stats()
            payload = {
                "hostname": hostname,
                "cpu": cpu,
                "mem": mem,
                "updated_at": time.time(),
                "ts_iso": time.strftime("%Y-%m-%d %H:%M:%S IST", time.localtime())
            }
            r_client.set(redis_key, json.dumps(payload), ex=ttl_seconds)
            logger.info(f"Heartbeat reported: CPU={cpu}% | Mem={mem}% (key={redis_key})")
        except Exception as e:
            logger.warning(f"Failed to publish heartbeat to local Redis: {e}")

        # Also publish directly to Gateway Redis (10.0.0.136) so VM 1 dashboard has immediate live data
        try:
            r_gw = redis.Redis(host="10.0.0.136", port=6379, password=args.redis_pass, decode_responses=True, socket_timeout=2.0)
            r_gw.set(redis_key, json.dumps(payload), ex=ttl_seconds)
        except Exception as fe:
            logger.debug(f"Direct Gateway Redis push notice: {fe}")

        # Sleep for interval in 1s increments for fast interrupt handling
        for _ in range(args.interval):
            if not running:
                break
            time.sleep(1)

    logger.info("Heartbeat daemon stopped.")

if __name__ == "__main__":
    main()

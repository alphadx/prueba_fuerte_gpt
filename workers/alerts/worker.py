"""Background worker for alerts queue.

Consumes JSON payloads from Redis list and prints them as processing trace.
"""

from __future__ import annotations

import json
import os
import time


def run_worker() -> None:
    redis_url = os.getenv("REDIS_URL", "redis://redis:6379/0")
    queue_name = os.getenv("ALERTS_QUEUE", "alerts_queue")
    poll_seconds = float(os.getenv("WORKER_POLL_SECONDS", "1.0"))

    import redis  # type: ignore

    client = redis.Redis.from_url(redis_url, decode_responses=True)
    print(f"[worker] listening queue={queue_name} redis={redis_url}")

    while True:
        item = client.blpop(queue_name, timeout=5)
        if item is None:
            time.sleep(poll_seconds)
            continue

        _, raw_payload = item
        payload = json.loads(raw_payload)
        print(f"[worker] processed alert payload={payload}")


if __name__ == "__main__":
    run_worker()

"""Queue abstraction for alert jobs.

Primary backend is Redis; optional in-memory fallback can be enabled for local/dev.
"""

from __future__ import annotations

import json
import logging
import os
from collections import deque
from threading import Lock
from typing import Any

logger = logging.getLogger(__name__)

_memory_queue: deque[str] = deque()
_memory_lock = Lock()


class QueueClient:
    """Queue adapter used by API to publish alert events."""

    def __init__(self) -> None:
        self.redis_url = os.getenv("REDIS_URL", "redis://redis:6379/0")
        self.queue_name = os.getenv("ALERTS_QUEUE", "alerts_queue")
        self.allow_memory_fallback = os.getenv("ALLOW_MEMORY_QUEUE_FALLBACK", "true").lower() == "true"

    def enqueue_alert(self, payload: dict[str, Any]) -> str:
        """Publish an alert payload into queue backend.

        Returns backend name ("redis" or "memory"). Raises RuntimeError if fallback is disabled
        and Redis is unavailable.
        """
        encoded = json.dumps(payload)
        try:
            import redis  # type: ignore

            client = redis.Redis.from_url(self.redis_url, decode_responses=True, socket_timeout=2)
            client.rpush(self.queue_name, encoded)
            return "redis"
        except Exception as exc:
            logger.warning("Redis queue unavailable: %s", exc)
            if not self.allow_memory_fallback:
                raise RuntimeError("Redis unavailable and in-memory fallback disabled") from exc

            with _memory_lock:
                _memory_queue.append(encoded)
            return "memory"


queue_client = QueueClient()

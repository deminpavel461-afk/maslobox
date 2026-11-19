from __future__ import annotations

import threading
import time
from collections import defaultdict, deque


class RateLimiter:
    """Simple in-memory sliding window rate limiter."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._buckets: dict[str, deque[float]] = defaultdict(deque)

    def clear(self) -> None:
        with self._lock:
            self._buckets.clear()

    def hit(self, key: str, *, limit: int, window_seconds: int, now: float | None = None) -> bool:
        """Record a hit. Returns True if allowed, False if rate exceeded."""
        ts = now if now is not None else time.time()
        with self._lock:
            bucket = self._buckets[key]
            cutoff = ts - window_seconds
            while bucket and bucket[0] < cutoff:
                bucket.popleft()
            if len(bucket) >= limit:
                return False
            bucket.append(ts)
            return True


rate_limiter = RateLimiter()

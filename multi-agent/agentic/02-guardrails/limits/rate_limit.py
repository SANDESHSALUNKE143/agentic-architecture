"""Request rate limit.

Purpose: bound how many calls one client can make in a short window.
Used by: agentic/02-guardrails/limits/guard.py. The task-size check remains agentic/02-guardrails/limits/task.py.
"""

from __future__ import annotations

import threading
import time


class SlidingWindow:
    def __init__(self) -> None:
        self._hits: dict[str, list[float]] = {}
        self._lock = threading.Lock()

    def reset(self) -> None:
        with self._lock:
            self._hits.clear()

    def allow(self, key: str, limit: int, window: float, now: float | None = None) -> tuple[bool, int]:
        moment = time.monotonic() if now is None else now
        with self._lock:
            recent = [stamp for stamp in self._hits.get(key, []) if moment - stamp < window]
            if len(recent) >= max(1, limit):
                self._hits[key] = recent
                retry = max(1, int(window - (moment - recent[0])) + 1)
                return False, retry
            recent.append(moment)
            if len(self._hits) > 2000:
                self._hits = {item: stamps for item, stamps in self._hits.items() if stamps}
            self._hits[key] = recent
            return True, 0

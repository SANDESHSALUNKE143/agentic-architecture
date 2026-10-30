"""Short cache for a repeated read.

Purpose: reuse a successful read so the same tool arguments do not call the merchant again.
Used by: agentic/05-tools/mcp/tool-gateway/gateway.py. Writes, failures, and the brief are not stored.
"""

from __future__ import annotations

import copy
import threading
import time
from typing import Any

from agentic.platform.config import setting

_OMIT = {"task", "question", "text"}


class ReadCache:
    def __init__(self) -> None:
        self._rows: dict[str, tuple[float, dict[str, Any]]] = {}
        self._lock = threading.Lock()

    def get(self, key: str) -> dict[str, Any] | None:
        if self._size() <= 0:
            return None
        with self._lock:
            row = self._rows.get(key)
            if row is None:
                return None
            stored_at, payload = row
            if time.monotonic() - stored_at > self._ttl():
                self._rows.pop(key, None)
                return None
            return copy.deepcopy(payload)

    def put(self, key: str, result: dict[str, Any]) -> None:
        limit = self._size()
        if limit <= 0:
            return
        payload = {field: value for field, value in result.items() if field not in _OMIT}
        with self._lock:
            self._rows[key] = (time.monotonic(), payload)
            overflow = len(self._rows) - limit
            if overflow > 0:
                for old in list(self._rows)[:overflow]:
                    self._rows.pop(old, None)

    def _ttl(self) -> float:
        try:
            return max(0.0, float(setting("PLATFORM_READ_CACHE_TTL", "30") or "30"))
        except ValueError:
            return 30.0

    def _size(self) -> int:
        try:
            return max(0, int(setting("PLATFORM_READ_CACHE_SIZE", "128") or "128"))
        except ValueError:
            return 128

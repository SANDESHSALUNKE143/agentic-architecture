"""Background writer for observability records.

Purpose: the request enqueues a trace, a score, or feedback. This worker is the only code that stores them.
Used by: observability trace and evaluation logs. Runs inside the API process.
"""

from __future__ import annotations

import logging
import queue
import threading
from typing import Any

from agentic.platform.config import data_dir

_QUEUE: queue.Queue = queue.Queue()
_LOGGER = logging.getLogger("agentic.trace")
_READY = False
_LOCK = threading.Lock()
_FIELDS = ("run_id", "stage", "agent_id", "tool", "status", "duration_ms", "harness")


def submit(kind: str, store: list, record: dict[str, Any]) -> None:
    _ensure()
    _QUEUE.put((kind, store, record))


def flush() -> None:
    _ensure()
    _QUEUE.join()


def _ensure() -> None:
    global _READY
    with _LOCK:
        if _READY:
            return
        path = data_dir() / "traces.log"
        handler = logging.FileHandler(path)
        handler.setFormatter(logging.Formatter("%(message)s"))
        _LOGGER.setLevel(logging.INFO)
        _LOGGER.addHandler(handler)
        threading.Thread(target=_loop, name="observability-writer", daemon=True).start()
        _READY = True


def _loop() -> None:
    while True:
        kind, store, record = _QUEUE.get()
        try:
            store.append(record)
            if kind == "trace":
                _LOGGER.info(_line(record))
        finally:
            _QUEUE.task_done()


def _line(record: dict[str, Any]) -> str:
    parts = [f"{key}={record[key]}" for key in _FIELDS if record.get(key) not in (None, "")]
    return " ".join(parts)

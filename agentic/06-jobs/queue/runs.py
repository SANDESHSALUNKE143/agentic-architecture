"""Bounded queue for agent runs.

Purpose: accept work onto a few workers so the request thread does not run the plan.
Used by: the run routes. The observability writer is a separate worker.
"""

from __future__ import annotations

import queue
import threading
from collections.abc import Callable

WORKERS = 2
CAP = 32
BACKGROUND = "Working in the background. This page will update when the run finishes."


class RunQueue:
    def __init__(self, workers: int = WORKERS, cap: int = CAP) -> None:
        self._queue: queue.Queue = queue.Queue(maxsize=cap)
        for number in range(workers):
            threading.Thread(target=self._loop, name=f"run-worker-{number}", daemon=True).start()

    def submit(self, work: Callable[[], None]) -> bool:
        try:
            self._queue.put(work, block=False)
        except queue.Full:
            return False
        return True

    def _loop(self) -> None:
        while True:
            work = self._queue.get()
            try:
                work()
            finally:
                self._queue.task_done()

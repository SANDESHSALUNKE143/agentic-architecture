"""
Jobs — register work, run it on one leader, inline when no queue exists.

An agent may need a periodic task: refresh a fixture, prune a cache,
recheck a dependency. The SDK does not ship a memory scheduler or a
required Redis. The agent registers a callable. When this process holds
the leader lock, due jobs run on the calling thread. When the lock is
held elsewhere, this process skips the tick.

Usage:
    jobs = JobRunner()
    jobs.register("refresh", 60, refresh)
    jobs.run_due()
"""

from __future__ import annotations

import threading
import time
from dataclasses import dataclass

# ── Lock and runner ───────────────────────────────────────────────────


class InMemoryLock:
    """A lock this process always owns. Use it when no shared database is configured."""

    def acquire(self) -> bool:
        """Return True. A single process is its own leader."""
        return True

    def release(self) -> None:
        """No shared lock to drop."""


@dataclass
class _Job:
    name: str
    interval_s: float
    fn: object
    last_run: float = 0.0


class JobRunner:
    """Run registered callables when their interval has elapsed and this process leads.

    ``run_due`` executes due jobs inline on the caller thread. There is no
    background thread and no queue. A shared lock can return False from
    ``acquire`` so a second replica does not double-run the same job.
    """

    def __init__(self, lock=None):
        self.lock = lock or InMemoryLock()
        self._jobs: dict[str, _Job] = {}
        self._guard = threading.Lock()

    def register(self, name: str, interval_s: float, fn) -> None:
        """Add or replace a named job. The interval is seconds and must be positive."""
        if not name or interval_s <= 0 or not callable(fn):
            raise ValueError("a job needs a name, a positive interval, and a callable")
        with self._guard:
            self._jobs[name] = _Job(name, interval_s, fn)

    def run_due(self, now: float | None = None) -> list[str]:
        """Run each due job when this process acquires the leader lock.

        1. Ask the lock. A refusal means another replica is the leader.
        2. Call each job whose interval has elapsed.
        3. Release the lock and return the names that ran.
        """
        if not self.lock.acquire():
            return []
        clock = time.monotonic() if now is None else now
        ran: list[str] = []
        try:
            with self._guard:
                due = [
                    job
                    for job in self._jobs.values()
                    if job.last_run == 0.0 or clock - job.last_run >= job.interval_s
                ]
            for job in due:
                job.fn()
                job.last_run = clock
                ran.append(job.name)
        finally:
            self.lock.release()
        return ran

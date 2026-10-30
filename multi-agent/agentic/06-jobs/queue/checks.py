"""Named checks inside this process.

Purpose: run a due check without a second service or a queue.
Used by: agentic/platform/composition.py. Tests call JobRunner directly.
"""

from __future__ import annotations

from datetime import datetime, timezone


class JobRunner:
    def __init__(self) -> None:
        self.ran: list[str] = []

    def run_due(self, name: str, when: datetime | None = None) -> dict:
        when = when or datetime.now(timezone.utc)
        self.ran.append(name)
        return {"name": name, "ran_at": when.isoformat(), "status": "completed"}

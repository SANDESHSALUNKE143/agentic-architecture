"""Scheduled checks. They run in this process, not as a second service."""

from __future__ import annotations

from datetime import datetime, timezone


class JobRunner:
    def __init__(self) -> None:
        self.ran: list[str] = []

    def run_due(self, name: str, when: datetime | None = None) -> dict:
        when = when or datetime.now(timezone.utc)
        self.ran.append(name)
        return {"name": name, "ran_at": when.isoformat(), "status": "completed"}

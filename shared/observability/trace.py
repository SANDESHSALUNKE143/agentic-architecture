"""Redacted traces. The raw task is not stored."""

from __future__ import annotations

import json
from typing import Any


class TraceLog:
    def __init__(self) -> None:
        self.events: list[dict[str, Any]] = []

    def add(self, run_id: str, stage: str, **fields: Any) -> dict[str, Any]:
        event = {"run_id": run_id, "stage": stage, **fields}
        self.events.append(event)
        return event

    def for_run(self, run_id: str) -> list[dict[str, Any]]:
        return [event for event in self.events if event["run_id"] == run_id]

    def export(self, run_id: str) -> str:
        return json.dumps(self.for_run(run_id))

"""Operational trace.

Purpose: record the agent, the tool name, the status, and the duration. The raw question and secrets are omitted.
Used by: agentic/04-loops/runtime/runtime.py while a run is in progress. The console shows the trace for the open run.
"""

from __future__ import annotations

import json
from typing import Any

from jobs.workers.writer import submit


class TraceLog:
    def __init__(self) -> None:
        self.events: list[dict[str, Any]] = []

    def add(self, run_id: str, stage: str, **fields: Any) -> dict[str, Any]:
        event = {"run_id": run_id, "stage": stage}
        for key, value in fields.items():
            if key not in {"task", "question", "text"}:
                event[key] = value
        submit("trace", self.events, event)
        return event

    def for_run(self, run_id: str) -> list[dict[str, Any]]:
        return [event for event in self.events if event["run_id"] == run_id]

    def export(self, run_id: str) -> str:
        return json.dumps(self.for_run(run_id))

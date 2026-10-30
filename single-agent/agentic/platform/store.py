"""In-process runs.

Purpose: keep one run until the process stops.
Used by: agentic/platform/composition.py.
"""

from __future__ import annotations


class RunStore:
    def __init__(self) -> None:
        self.runs: dict[str, dict] = {}

    def create(self, run: dict) -> dict:
        self.runs[run["request_id"]] = run
        return run

    def get(self, run_id: str) -> dict | None:
        return self.runs.get(run_id)

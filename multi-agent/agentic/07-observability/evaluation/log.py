"""Scores for a finished run.

Purpose: record status, tool names, and duration. Feedback is stored here. Model weights stay unchanged.
Used by: the runtime after a response, and POST /agent-runs/{run_id}/feedback.
"""

from __future__ import annotations

from jobs.workers.writer import flush, submit


class EvaluationLog:
    def __init__(self) -> None:
        self.records: list[dict] = []
        self.feedback: list[dict] = []

    def record(self, run_id: str, agent_id: str, status: str, tools: list[str], duration_ms: int) -> None:
        submit(
            "score",
            self.records,
            {"run_id": run_id, "agent_id": agent_id, "status": status, "tools": tools, "duration_ms": duration_ms},
        )

    def add_feedback(self, run_id: str, helpful: bool, note: str = "") -> None:
        submit("feedback", self.feedback, {"run_id": run_id, "helpful": helpful, "note": note[:240]})
        flush()

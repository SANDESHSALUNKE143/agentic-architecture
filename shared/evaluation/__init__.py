"""Evaluation records status, tool names, and duration. It does not change model weights."""

from __future__ import annotations


class EvaluationLog:
    def __init__(self) -> None:
        self.records: list[dict] = []
        self.feedback: list[dict] = []

    def record(self, run_id: str, agent_id: str, status: str, tools: list[str], duration_ms: int) -> None:
        self.records.append(
            {"run_id": run_id, "agent_id": agent_id, "status": status, "tools": tools, "duration_ms": duration_ms}
        )

    def add_feedback(self, run_id: str, helpful: bool, note: str = "") -> None:
        self.feedback.append({"run_id": run_id, "helpful": helpful, "note": note[:240]})

"""Shared agent shape. Folders under agents/ fill this in."""

from __future__ import annotations

from typing import Any, Callable


class Agent:
    """One specialist: instructions, an allowlist, and a handle function."""

    def __init__(
        self,
        *,
        id: str,
        display_name: str,
        description: str,
        instructions: str,
        allowed_tools: tuple[str, ...],
        permissions: tuple[str, ...],
        approval_policy: str,
        sample_task: str,
        read_only: bool = True,
        max_steps: int = 2,
    ) -> None:
        self.id = id
        self.display_name = display_name
        self.description = description
        self.instructions = instructions
        self.allowed_tools = allowed_tools
        self.permissions = permissions
        self.approval_policy = approval_policy
        self.sample_task = sample_task
        self.read_only = read_only
        self.max_steps = max_steps
        self.handler: Callable | None = None

    def definition(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "display_name": self.display_name,
            "description": self.description,
            "instructions": self.instructions,
            "allowed_tools": list(self.allowed_tools),
            "permissions": list(self.permissions),
            "execution_limits": {"max_steps": self.max_steps, "max_hops": 6},
            "approval_policy": self.approval_policy,
            "sample_task": self.sample_task,
            "read_only": self.read_only,
        }


def validate_output(outcome: dict[str, Any]) -> str | None:
    """Return a problem statement when a handler result is not the shared shape."""
    if not isinstance(outcome, dict):
        return "Agent output must be an object."
    if outcome.get("status") not in {"completed", "needs_approval", "failed", "not_implemented"}:
        return "Agent status is not allowed."
    summary = outcome.get("summary")
    if not isinstance(summary, str) or not summary.strip():
        return "Agent summary must be a non-empty string."
    data = outcome.get("data", {})
    if data is not None and not isinstance(data, dict):
        return "Agent data must be an object."
    citations = outcome.get("citations") or []
    if not isinstance(citations, list):
        return "Agent citations must be a list."
    for row in citations:
        if not isinstance(row, dict) or not str(row.get("source_id") or "").strip():
            return "Each citation needs a source_id."
        if not isinstance(row.get("location"), str):
            return "Each citation needs a location."
    return None


def finish(
    summary: str,
    data: dict[str, Any] | None = None,
    *,
    status: str = "completed",
    citations: list | None = None,
    pending_tool: dict | None = None,
    requires_qualified_review: bool = False,
) -> dict[str, Any]:
    """Standard handler result. done=True ends the agent loop."""
    return {
        "done": True,
        "status": status,
        "summary": summary,
        "data": data or {},
        "citations": citations or [],
        "pending_tool": pending_tool,
        "requires_qualified_review": requires_qualified_review,
    }

"""Typed records shared by the API, the engine, and the dashboard."""

from __future__ import annotations

import hashlib
import json
import uuid
from dataclasses import asdict, dataclass, field
from typing import Any

STATUSES = ("completed", "needs_approval", "failed", "not_implemented")
TRACE_STAGES = ("router", "planner", "guardrail", "agent", "tool", "approval", "n8n", "memory")
TRACE_STATUSES = ("started", "ok", "failed", "blocked", "needs_approval")
ERROR_CODES = (
    "unknown_agent",
    "delegation_denied",
    "tool_denied",
    "schema_invalid",
    "timeout",
    "step_limit",
    "loop_detected",
    "approval_required",
    "approval_stale",
    "approval_rejected",
    "tool_error",
    "provider_error",
    "not_implemented",
    "ambiguous_intent",
    "cancelled",
)


def new_id(prefix: str) -> str:
    """Short correlation id. prefix keeps runs, approvals, and notes apart."""
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


def digest(payload: Any) -> str:
    """Stable hash so a changed approval payload becomes stale."""
    raw = json.dumps(payload, sort_keys=True, default=str).encode()
    return hashlib.sha256(raw).hexdigest()


@dataclass
class RunRequest:
    """One task from the dashboard, CLI, n8n, or a framework sample."""

    task: str
    user_id: str = "local-development-user"
    request_id: str = ""
    context: dict[str, Any] = field(default_factory=dict)
    mode: str = "mock"
    workflow: str | None = None
    agents: list[str] | None = None
    example_id: str | None = None
    session_id: str = ""

    def __post_init__(self) -> None:
        if not self.request_id:
            self.request_id = new_id("run")
        if not self.session_id:
            self.session_id = new_id("ses")


@dataclass
class Handoff:
    """Structured output one agent passes to the next. No credentials, no instructions."""

    from_agent: str
    to_agent: str
    summary: str
    data: dict[str, Any]
    tool_calls: list[dict[str, Any]]
    citations: list[dict[str, Any]]

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class TraceEvent:
    """One visible step. Summaries are redacted before they are stored."""

    sequence: int
    time: str
    stage: str
    status: str
    message: str
    agent_id: str = ""
    tool_name: str = ""
    duration_ms: float = 0
    error_code: str = ""
    input_summary: str = ""
    output_summary: str = ""
    tokens: int | None = None
    cost: float | None = None
    model: str = ""

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


def public_dict(record: Any) -> dict[str, Any]:
    """JSON-ready mapping for a dataclass."""
    return asdict(record)

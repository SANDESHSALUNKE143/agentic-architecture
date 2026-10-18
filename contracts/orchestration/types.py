"""Async decision/result contracts and run-event observer interfaces."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Protocol

from agentic_sdk.contracts import Context


class ExecutionError(RuntimeError):
    """A run rejected because a model action, tool result or execution policy is invalid."""

    pass


@dataclass(frozen=True)
class ModelReply:
    """One tool/final decision plus provider-reported token counts for that decision."""

    action: Mapping[str, Any]
    input_tokens: int = 0
    output_tokens: int = 0


class DecisionModel(Protocol):
    """Async decision port receiving bounded instructions, evidence and visible tool metadata."""

    async def decide(
        self,
        instruction: str,
        question: str,
        observations: list[dict],
        tools: list[dict],
        max_output_tokens: int,
    ) -> ModelReply:
        """Return a JSON-shaped tool or final action and usage; tool results are untrusted data."""
        ...


@dataclass(frozen=True)
class RunResult:
    """Completed run metadata and answer; no mutable execution state is exposed."""

    run_id: str
    answer: str
    steps: int
    tools_used: tuple[str, ...]
    input_tokens: int
    output_tokens: int


class RunObserver(Protocol):
    """Sink for scoped, content-free run lifecycle metadata."""

    def emit(self, ctx: Context, run_id: str, event: str, fields: dict):
        """Record the event for the trusted context and run ID; do not add prompt or tool payloads."""
        ...


class NullObserver:
    """No-op observer for applications that explicitly disable run event recording."""

    def emit(self, ctx, run_id, event, fields):
        """Discard the event without performing I/O."""
        pass

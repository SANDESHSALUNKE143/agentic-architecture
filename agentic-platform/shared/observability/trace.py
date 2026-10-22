"""Ordered trace for one run. Failures stay in the list with the steps that worked."""

from __future__ import annotations

import json
import logging
import time
from datetime import datetime, timezone

from shared.contracts import TraceEvent
from shared.security.redact import summarize

log = logging.getLogger("agentic.platform")


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


class TraceLog:
    """Append-only events for a single request id."""

    def __init__(self, request_id: str) -> None:
        self.request_id = request_id
        self.events: list[TraceEvent] = []

    def add(
        self,
        stage: str,
        status: str,
        message: str,
        *,
        agent_id: str = "",
        tool_name: str = "",
        duration_ms: float = 0,
        error_code: str = "",
        input_summary: object = "",
        output_summary: object = "",
        tokens: int | None = None,
        cost: float | None = None,
        model: str = "",
    ) -> TraceEvent:
        event = TraceEvent(
            sequence=len(self.events) + 1,
            time=_now(),
            stage=stage,
            status=status,
            message=message,
            agent_id=agent_id,
            tool_name=tool_name,
            duration_ms=round(duration_ms, 2),
            error_code=error_code,
            input_summary=summarize(input_summary)
            if not isinstance(input_summary, str)
            else summarize(input_summary),
            output_summary=summarize(output_summary) if output_summary != "" else "",
            tokens=tokens,
            cost=cost,
            model=model,
        )
        if isinstance(input_summary, str):
            event.input_summary = summarize(input_summary)
        self.events.append(event)
        log.info(
            json.dumps(
                {
                    "request_id": self.request_id,
                    "agent_id": agent_id,
                    "tool": tool_name,
                    "stage": stage,
                    "status": status,
                    "duration_ms": event.duration_ms,
                    "error_code": error_code,
                    "message": message,
                    "tokens": tokens,
                    "cost": cost,
                    "model": model,
                }
            )
        )
        return event

    def errors(self) -> list[dict]:
        """Failed, blocked, and approval-waiting events, in order."""
        wanted = {"failed", "blocked", "needs_approval"}
        return [event.as_dict() for event in self.events if event.status in wanted]

    def as_list(self) -> list[dict]:
        return [event.as_dict() for event in self.events]


class Timer:
    """Wall time for one span, in milliseconds."""

    def __init__(self) -> None:
        self.started = time.perf_counter()

    def elapsed_ms(self) -> float:
        return (time.perf_counter() - self.started) * 1000

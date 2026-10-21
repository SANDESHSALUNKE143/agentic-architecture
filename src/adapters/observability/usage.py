"""
Model usage — one row per completion, with no prompt and no answer.

A provider call should leave a receipt the operator can add up: which
provider, which model, how many tokens, how long it took, and the cost
when the provider returned one. The text of the call stays in the
provider. This log keeps the numbers.

Usage:
    log = UsageLog()
    log.record(context, provider="openai", model="gpt", input_tokens=10,
               output_tokens=4, latency_ms=80)
    log.summary(context)
"""

from __future__ import annotations

import threading
import time
from dataclasses import dataclass

from agentic_sdk.core.context.identity import Context

# ── Receipt ───────────────────────────────────────────────────────────


@dataclass(frozen=True)
class UsageRecord:
    """Content-free receipt for one model call."""

    tenant_id: str
    agent_id: str
    provider: str
    model: str
    input_tokens: int
    output_tokens: int
    latency_ms: float
    cost: float | None
    recorded_at: float


class UsageLog:
    """In-process list of usage receipts.

    Restarting the process clears the list. The shape is small enough for
    a table later: one row, no prompt column."""

    def __init__(self) -> None:
        self._rows: list[UsageRecord] = []
        self._lock = threading.Lock()

    def record(
        self,
        ctx: Context,
        *,
        provider: str,
        model: str,
        input_tokens: int,
        output_tokens: int,
        latency_ms: float,
        cost: float | None = None,
    ) -> UsageRecord:
        """Append one receipt. Token counts below zero are rejected."""
        if input_tokens < 0 or output_tokens < 0:
            raise ValueError("token counts cannot be negative")
        row = UsageRecord(
            ctx.tenant_id,
            ctx.agent_id,
            provider,
            model,
            input_tokens,
            output_tokens,
            round(latency_ms, 2),
            cost,
            time.time(),
        )
        with self._lock:
            self._rows.append(row)
        return row

    def summary(self, ctx: Context) -> dict[str, int | float]:
        """Sum receipts for one tenant and agent. Prompts are not available here."""
        rows = [
            row
            for row in self._rows
            if row.tenant_id == ctx.tenant_id and row.agent_id == ctx.agent_id
        ]
        costs = [row.cost for row in rows if row.cost is not None]
        return {
            "calls": len(rows),
            "input_tokens": sum(row.input_tokens for row in rows),
            "output_tokens": sum(row.output_tokens for row in rows),
            "latency_ms": round(sum(row.latency_ms for row in rows), 2),
            "cost": round(sum(costs), 6) if costs else 0,
        }

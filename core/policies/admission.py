"""
Request admission — rate, body size, and token quota.

The harness already stops one run when its own budget is gone. This gate
stops a tenant from opening too many runs, sending an oversized question,
or spending the day's token allowance. Counts stay in the process. A later
shared store can replace the dictionaries without changing the call.

Usage:
    gate = RequestGate(per_minute=30, daily_tokens=50_000)
    gate.admit(context, question)
    gate.charge(context, input_tokens + output_tokens)
"""

from __future__ import annotations

import threading
import time
from dataclasses import dataclass

from agentic_sdk.contracts.orchestration.types import ExecutionError
from agentic_sdk.core.context.identity import Context

# ── Gate ──────────────────────────────────────────────────────────────


@dataclass
class RequestGate:
    """In-process sliding window, body cap, and daily or monthly token quota.

    The key is the tenant and the agent. Another replica does not see these
    counts. That is acceptable for one process and wrong for a fleet; swap
    the dictionaries for a shared counter when more than one process serves
    the same agent."""

    per_minute: int = 60
    max_body_bytes: int = 8000
    daily_tokens: int = 100_000
    monthly_tokens: int = 2_000_000

    def __post_init__(self) -> None:
        if min(self.per_minute, self.max_body_bytes, self.daily_tokens, self.monthly_tokens) < 1:
            raise ValueError("admission limits must be positive")
        self._lock = threading.Lock()
        self._hits: dict[tuple[str, str], list[float]] = {}
        self._day: dict[tuple[str, str, str], int] = {}
        self._month: dict[tuple[str, str, str], int] = {}

    def admit(self, ctx: Context, question: str) -> None:
        """Reject an oversized body, a burst, or a tenant that already spent the quota.

        1. Measure the question in bytes.
        2. Drop hits older than sixty seconds and count what remains.
        3. Compare charged tokens with the daily and monthly ceilings.
        """
        size = len(question.encode())
        if size > self.max_body_bytes:
            raise ExecutionError("request body exceeds the cap")
        now = time.monotonic()
        key = (ctx.tenant_id, ctx.agent_id)
        with self._lock:
            recent = [stamp for stamp in self._hits.get(key, []) if now - stamp < 60]
            if len(recent) >= self.per_minute:
                self._hits[key] = recent
                raise ExecutionError("request rate exceeded")
            recent.append(now)
            self._hits[key] = recent
            if self._spent(self._day, key, time.strftime("%Y-%m-%d")) >= self.daily_tokens:
                raise ExecutionError("daily token quota exceeded")
            if self._spent(self._month, key, time.strftime("%Y-%m")) >= self.monthly_tokens:
                raise ExecutionError("monthly token quota exceeded")

    def charge(self, ctx: Context, tokens: int) -> None:
        """Add the tokens a finished run reported. Zero and negative values are ignored."""
        if tokens <= 0:
            return
        key = (ctx.tenant_id, ctx.agent_id)
        with self._lock:
            self._add(self._day, key, time.strftime("%Y-%m-%d"), tokens)
            self._add(self._month, key, time.strftime("%Y-%m"), tokens)

    def public(self) -> dict[str, int]:
        """Return the configured ceilings. Counts and tenant names stay out."""
        return {
            "request_rate_per_minute": self.per_minute,
            "max_body_bytes": self.max_body_bytes,
            "daily_tokens": self.daily_tokens,
            "monthly_tokens": self.monthly_tokens,
        }

    def _spent(self, bucket: dict, key: tuple[str, str], period: str) -> int:
        return bucket.get((*key, period), 0)

    def _add(self, bucket: dict, key: tuple[str, str], period: str, tokens: int) -> None:
        stamp = (*key, period)
        bucket[stamp] = bucket.get(stamp, 0) + tokens


def assert_secret_strength(name: str, value: str, *, minimum: int = 32) -> None:
    """Refuse a blank, short, or well-known secret before a process serves traffic.

    The check looks at length and a small denylist. It does not store the
    secret and it does not decide which environment variable an agent uses.
    """
    blocked = {"password", "changeme", "secret", "token", "admin", "test"}
    if not isinstance(value, str) or len(value) < minimum or value.strip().lower() in blocked:
        raise ValueError(f"{name} is too weak for a shared deployment")

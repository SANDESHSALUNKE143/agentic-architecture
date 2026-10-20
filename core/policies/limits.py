"""
Per-run limits for the harness.

These are the bounds that apply when a request-rate limit is not configured:
step count, output tokens, token budget, timeout, context bytes, and tool
result bytes. Values outside the allowed ranges are rejected at construction.

Usage:
    limits = RunLimits(max_steps=8, timeout_seconds=60)
"""

from __future__ import annotations

from dataclasses import dataclass


# ── Bounds ────────────────────────────────────────────────────────────


@dataclass(frozen=True)
class RunLimits:
    """Validated per-run bounds for steps, output, context, tool results and deadline.

    Token reservation uses conservative serialized bytes rather than provider-specific
    tokenization. The timeout is in seconds; byte limits apply to UTF-8 payloads."""

    max_steps: int = 8
    max_output_tokens: int = 1024
    token_budget: int = 100000
    timeout_seconds: float = 60
    max_context_bytes: int = 60000
    max_tool_result_bytes: int = 24000

    def __post_init__(self):
        bounds = {
            "max_steps": (1, 32),
            "max_output_tokens": (64, 8192),
            "token_budget": (100, 10000000),
            "max_context_bytes": (1000, 1000000),
            "max_tool_result_bytes": (1000, 1000000),
        }
        for name, (low, high) in bounds.items():
            value = getattr(self, name)
            if type(value) is not int or not low <= value <= high:
                raise ValueError("invalid limit: " + name)
        if isinstance(self.timeout_seconds, bool) or not 0 < self.timeout_seconds <= 300:
            raise ValueError("timeout must be in (0,300]")

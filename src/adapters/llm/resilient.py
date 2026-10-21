"""
Resilient completion — retry, one fallback, a circuit, and JSON extract.

A provider blip should not fail the run on the first try. After a few
failures the circuit opens and the next calls go to the fallback, or
fail closed when no fallback was configured. Structured extract asks for
a JSON object and checks that the required keys are present.

The prompt is never written to the usage log.

Usage:
    model = ResilientLLM(primary, fallback, usage=log, provider="primary", model="demo")
    completion = model.complete(prompt, 256)
    fields = model.extract_structured(prompt, ("city", "direction"))
"""

from __future__ import annotations

import json
import time

from agentic_sdk.contracts.models.types import Completion
from agentic_sdk.contracts.orchestration.types import ExecutionError

# ── Wrapper ───────────────────────────────────────────────────────────


class ResilientLLM:
    """Retry a primary completion port, then one fallback, and record usage.

    The circuit opens after repeated failures and stays open until
    ``open_seconds`` have passed. A successful call closes it.
    """

    def __init__(
        self,
        primary,
        fallback=None,
        *,
        attempts: int = 3,
        usage=None,
        provider: str = "primary",
        model: str = "unspecified",
        failures_before_open: int = 3,
        open_seconds: float = 30,
        context=None,
    ):
        if attempts < 1 or failures_before_open < 1 or open_seconds <= 0:
            raise ValueError("retry and circuit settings must be positive")
        self.primary = primary
        self.fallback = fallback
        self.attempts = attempts
        self.usage = usage
        self.provider = provider
        self.model = model
        self.failures_before_open = failures_before_open
        self.open_seconds = open_seconds
        self.context = context
        self._failures = 0
        self._open_until = 0.0

    def complete(self, prompt: str, max_tokens: int) -> Completion:
        """Try the primary, then the fallback. Record tokens and latency, not text.

        1. If the circuit is open, skip the primary.
        2. Retry the primary until an attempt succeeds or the attempts run out.
        3. Call the fallback once when the primary did not return.
        """
        if time.monotonic() < self._open_until:
            return self._fallback_or_raise(prompt, max_tokens)
        last_error: Exception | None = None
        for _ in range(self.attempts):
            started = time.monotonic()
            try:
                result = self.primary.complete(prompt, max_tokens)
            except Exception as exc:  # provider failures vary; the circuit counts all of them
                last_error = exc
                self._failures += 1
                if self._failures >= self.failures_before_open:
                    self._open_until = time.monotonic() + self.open_seconds
                continue
            self._failures = 0
            self._open_until = 0.0
            self._record(result, started)
            return result
        if self.fallback is not None:
            return self._call(self.fallback, prompt, max_tokens, "fallback")
        raise ExecutionError("model provider failed") from last_error

    def extract_structured(self, prompt: str, required: tuple[str, ...]) -> dict:
        """Complete a prompt and require a JSON object that contains every named field."""
        instruction = prompt + "\nReturn only a JSON object."
        result = self.complete(instruction, 512)
        try:
            body = json.loads(result.text)
        except (ValueError, TypeError) as exc:
            raise ExecutionError("model did not return a JSON object") from exc
        if not isinstance(body, dict) or any(name not in body for name in required):
            raise ExecutionError("structured result is missing required fields")
        return body

    def _fallback_or_raise(self, prompt: str, max_tokens: int) -> Completion:
        if self.fallback is None:
            raise ExecutionError("model circuit is open")
        return self._call(self.fallback, prompt, max_tokens, "fallback")

    def _call(self, port, prompt: str, max_tokens: int, provider: str) -> Completion:
        started = time.monotonic()
        result = port.complete(prompt, max_tokens)
        self._record(result, started, provider)
        return result

    def _record(self, result: Completion, started: float, provider: str | None = None) -> None:
        if self.usage is None or self.context is None:
            return
        cost = getattr(result, "cost", None)
        self.usage.record(
            self.context,
            provider=provider or self.provider,
            model=self.model,
            input_tokens=result.input_tokens,
            output_tokens=result.output_tokens,
            latency_ms=(time.monotonic() - started) * 1000,
            cost=cost,
        )

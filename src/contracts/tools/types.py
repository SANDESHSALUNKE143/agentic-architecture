"""Synchronous tool contract with caller-managed idempotency identity."""

from typing import Mapping, Protocol

from agentic_sdk.core.context.identity import Context


class Tool(Protocol):
    """Synchronous tool port for explicit arguments and a caller-managed idempotency key."""

    def invoke(
        self, ctx: Context, arguments: Mapping[str, object], idempotency_key: str
    ) -> Mapping[str, object]:
        """Invoke within the context scope; the adapter defines idempotency/reconciliation behavior."""
        ...

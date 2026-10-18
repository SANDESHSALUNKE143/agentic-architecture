"""Content-free telemetry recording contract."""

from typing import Mapping, Protocol

from agentic_sdk.core.context.identity import Context


class Telemetry(Protocol):
    """Port for recording scoped non-content telemetry fields."""

    def record(self, ctx: Context, event: str, fields: Mapping[str, str | int | float]) -> None:
        """Record an event with bounded metadata; adapters should allowlist fields."""
        ...

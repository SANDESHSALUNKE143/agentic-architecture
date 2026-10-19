"""Read-only SQL contract. Callers name an allowlisted table, never a connection."""

from typing import Protocol

from agentic_sdk.core.context.identity import Context


class SqlRead(Protocol):
    """Bounded read of one operator-allowlisted table."""

    def query(self, ctx: Context, table: str, limit: int) -> dict:
        """Return at most limit rows. Reject unknown tables and limits above the cap."""
        ...

"""
SQL read contract.

Agents name an allowlisted table and a row limit. The connection, the
schema, and the credentials stay in the agent. Adapters implement query().

Usage:
    class SqlRead implementation: query(context, table, limit) -> dict
"""

from typing import Protocol

from agentic_sdk.core.context.identity import Context

# ── Port ──────────────────────────────────────────────────────────────


class SqlRead(Protocol):
    """Bounded read of one operator-allowlisted table."""

    def query(self, ctx: Context, table: str, limit: int) -> dict:
        """Return at most limit rows. Reject unknown tables and limits above the cap."""
        ...

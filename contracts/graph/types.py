"""
Graph RAG contract.

Agents name an entity. The adapter owns the query language and the neighbor
cap. The model does not send Cypher or a connection string.

Usage:
    class GraphRag implementation: expand(context, entity) -> dict
"""

from typing import Protocol

from agentic_sdk.core.context.identity import Context

# ── Port ──────────────────────────────────────────────────────────────


class GraphRag(Protocol):
    """One-hop expansion of a single entity, with bounded passages."""

    def expand(self, ctx: Context, entity: str) -> dict:
        """Return neighbors and passages for the entity. Cap the neighborhood in the adapter."""
        ...

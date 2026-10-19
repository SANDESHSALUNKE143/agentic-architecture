"""Graph RAG contract. Agents name an entity. Adapters own the query language."""

from typing import Protocol

from agentic_sdk.core.context.identity import Context


class GraphRag(Protocol):
    """One-hop expansion of a single entity, with bounded passages."""

    def expand(self, ctx: Context, entity: str) -> dict:
        """Return neighbors and passages for the entity. Cap the neighborhood in the adapter."""
        ...

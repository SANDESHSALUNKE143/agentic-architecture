"""
Retrieval policy — a cache key, a rank hook, and delete or restrict.

The vector store still owns similarity. These helpers sit in front of it.
The cache key names the tenant, the agent, the embedding profile, and a
hash of the query so two agents never share a result page. Ranking can
reorder hits when the caller supplies a key function. Delete and restrict
hide a document from later searches without teaching the store a business
schema.

Usage:
    cache = RetrievalCache()
    key = cache.key(context, store.profile.fingerprint, digest)
    governed = GovernedStore(store)
    governed.delete(context, document_id)
"""

from __future__ import annotations

import hashlib

from agentic_sdk.contracts.orchestration.types import ExecutionError
from agentic_sdk.core.context.identity import Context

# ── Cache, rank, and visibility ───────────────────────────────────────


class RetrievalCache:
    """Small result cache keyed by scope, profile fingerprint, and query hash."""

    def __init__(self) -> None:
        self._rows: dict[str, list] = {}

    @staticmethod
    def key(ctx: Context, fingerprint: str, query_hash: str) -> str:
        """Build a cache key. The query hash is a digest, not the question text."""
        return "\0".join((ctx.tenant_id, ctx.agent_id, fingerprint, query_hash))

    def get(self, key: str):
        """Return a cached hit list, or None on a miss."""
        return self._rows.get(key)

    def put(self, key: str, hits: list) -> None:
        """Store a hit list under a key from ``key``."""
        self._rows[key] = hits


def query_hash(text: str) -> str:
    """Hash query text for a cache key. The text itself is not the key."""
    return hashlib.sha256(text.encode()).hexdigest()


def rank_hits(hits: list, key):
    """Return hits ordered by ``key`` descending. The store order is the tie break.

    ``key`` receives a Hit. A constant key leaves the store order in place
    aside from a stable sort.
    """
    return sorted(hits, key=key, reverse=True)


class GovernedStore:
    """Hide deleted or restricted documents from an inner vector store.

    The inner store may still hold the vector. Search results drop hidden
    ids. Writes require knowledge:write. Reads require knowledge:read,
    which the inner store also enforces.
    """

    def __init__(self, inner):
        self.inner = inner
        self.profile = inner.profile
        self._hidden: set[tuple[str, str, str]] = set()

    def upsert(self, ctx: Context, doc, vector: list[float]) -> None:
        """Insert through the inner store and clear a prior hide for this id."""
        self.inner.upsert(ctx, doc, vector)
        self._hidden.discard((ctx.tenant_id, ctx.agent_id, doc.id))

    def search(self, ctx: Context, vector: list[float], limit: int) -> list:
        """Search the inner store and drop hidden documents for this tenant and agent."""
        hits = self.inner.search(ctx, vector, limit)
        return [
            hit
            for hit in hits
            if (ctx.tenant_id, ctx.agent_id, hit.document.id) not in self._hidden
        ]

    def delete(self, ctx: Context, document_id: str) -> None:
        """Hide a document from later searches in this scope."""
        ctx.require("knowledge:write")
        if not document_id:
            raise ExecutionError("a document id is required")
        self._hidden.add((ctx.tenant_id, ctx.agent_id, document_id))

    def restrict(self, ctx: Context, document_id: str) -> None:
        """Apply the same hide as delete. The agent decides what restrict means in its domain."""
        self.delete(ctx, document_id)

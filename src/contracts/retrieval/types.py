"""Document, retrieval hit and scope-aware vector-store contracts."""

from dataclasses import dataclass
from typing import Protocol

from agentic_sdk.contracts.embeddings.types import EmbeddingProfile
from agentic_sdk.core.context.identity import Context


@dataclass(frozen=True)
class Document:
    """A caller-chunked text item identified by a stable document/version key.

    Document-level ACLs and src/page metadata are not represented by this type."""

    id: str
    text: str


@dataclass(frozen=True)
class Hit:
    """A retrieved document and its store-specific similarity score."""

    document: Document
    score: float


class VectorStore(Protocol):
    """Storage port whose profile and tenant/agent isolation must match the embedder."""

    profile: EmbeddingProfile

    def upsert(self, ctx: Context, doc: Document, vector: list[float]) -> None:
        """Insert or replace the document vector within the trusted context scope."""
        ...

    def search(self, ctx: Context, vector: list[float], limit: int) -> list[Hit]:
        """Return up to limit scoped matches for a vector using the store profile."""
        ...

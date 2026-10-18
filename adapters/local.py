"""Deterministic demonstration adapters; not production semantic models."""

import hashlib
import re

from agentic_sdk.contracts import (
    Completion,
    Context,
    Document,
    EmbeddingProfile,
    Hit,
    validate_vector,
)


class HashEmbedder:
    """Deterministic hashed-token embedding for tests; not a semantic language model."""

    def __init__(self):
        self.profile = EmbeddingProfile("hash-demo", "1", 64)

    def embed(self, text: str) -> list[float]:
        """Hash normalized tokens into a 64-dimensional unit vector, including an empty-text sentinel."""
        vector = [0.0] * self.profile.dimensions
        for token in re.findall(r"[a-z0-9]+", text.lower()):
            vector[
                int.from_bytes(hashlib.sha256(token.encode()).digest()[:4], "big") % len(vector)
            ] += 1
        if not any(vector):
            vector[0] = 1
        return validate_vector(vector, self.profile)


class MemoryStore:
    """In-process reference vector store keyed by tenant, agent and document ID."""

    def __init__(self, profile: EmbeddingProfile):
        self.profile = profile
        self._rows = {}

    def upsert(self, ctx: Context, doc: Document, vector: list[float]) -> None:
        """Validate the vector and replace only the document in the supplied scope."""
        ctx.require("knowledge:write")
        self._rows[(ctx.tenant_id, ctx.agent_id, doc.id)] = (
            doc,
            validate_vector(vector, self.profile),
        )

    def search(self, ctx: Context, vector: list[float], limit: int) -> list[Hit]:
        """Authorize retrieval and return the highest cosine scores from the same scope."""
        ctx.require("knowledge:read")
        if not 1 <= limit <= 20:
            raise ValueError("limit must be 1..20")
        vector = validate_vector(vector, self.profile)
        hits = [
            Hit(doc, sum(a * b for a, b in zip(vector, v)))
            for (tenant, agent, _), (doc, v) in self._rows.items()
            if (tenant, agent) == (ctx.tenant_id, ctx.agent_id)
        ]
        return sorted(hits, key=lambda h: h.score, reverse=True)[:limit]


class EchoLLM:
    """Deterministic bounded echo completion used to test plumbing without paid inference."""

    def complete(self, prompt: str, max_tokens: int) -> Completion:
        """Return a DEMO-prefixed prompt slice; demo usage is measured in UTF-8 bytes."""
        answer = ("DEMO: " + prompt).encode()[:max_tokens].decode(errors="ignore")
        return Completion(answer, len(prompt.encode()), len(answer.encode()))


class SafeTelemetry:
    """Content-free events. In-process metadata is NOT an authentication boundary."""

    ALLOWED = {"duration_ms", "input_tokens", "output_tokens", "hits", "status"}

    def __init__(self):
        self.events = []

    def record(self, ctx, event, fields):
        """Append only allowlisted fields and trusted scope labels to the in-memory event list."""
        self.events.append(
            {
                "tenant_id": ctx.tenant_id,
                "agent_id": ctx.agent_id,
                "event": event,
                **{k: v for k, v in fields.items() if k in self.ALLOWED},
            }
        )

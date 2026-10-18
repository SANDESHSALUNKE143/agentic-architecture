"""Operator-configured PostgreSQL, embedding and Qdrant composition."""

from __future__ import annotations

import os

from agentic_sdk.adapters.local import HashEmbedder
from agentic_sdk.adapters.persistence.postgres import Database
from agentic_sdk.adapters.qdrant import QdrantStore


def components():
    """Construct PostgreSQL, embedding and Qdrant adapters from trusted environment settings.

    API and worker must use the same embedding profile. Operators own secret
    provisioning and external endpoint approval."""
    from qdrant_client import QdrantClient

    db = Database(os.environ["DATABASE_URL"])
    embedder = HashEmbedder()
    # Local smoke profile is explicit. Changing a semantic model requires a new profile/index.
    if os.getenv("EMBEDDING_MODE", "demo") != "demo":
        from agentic_sdk.adapters.providers import CompatibleEmbedder, client
        from agentic_sdk.contracts import EmbeddingProfile

        profile = EmbeddingProfile(
            os.environ["EMBEDDING_MODEL"],
            os.environ["EMBEDDING_REVISION"],
            int(os.environ["EMBEDDING_DIMENSIONS"]),
        )
        embedder = CompatibleEmbedder(
            client(os.environ["MODEL_BASE_URL"], "MODEL_API_KEY"),
            os.environ["EMBEDDING_DEPLOYMENT"],
            profile,
        )
    store = QdrantStore(
        QdrantClient(
            url=os.environ["QDRANT_URL"],
            api_key=os.environ["QDRANT_API_KEY"],
            timeout=10,
        ),
        embedder.profile,
    )
    return db, embedder, store

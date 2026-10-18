"""Collection-per-agent/profile adapter; provisioning is an administrator operation.
Profile is encoded into the collection name; external provisioning must honor it.
"""

import hashlib
import uuid

from agentic_sdk.contracts import Document, Hit, validate_vector


class QdrantStore:
    """Qdrant adapter using one collection per tenant, agent and embedding profile.

    Provisioning is an explicit index:admin operation. Callers own client lifecycle;
    collection naming isolates scopes but does not replace Qdrant network credentials."""

    def __init__(self, client, profile):
        self.client, self.profile = client, profile

    def collection(self, ctx):
        """Derive a collection name from tenant/agent scope and the complete embedding profile."""
        scope = hashlib.sha256((ctx.tenant_id + "\0" + ctx.agent_id).encode()).hexdigest()
        return "a_" + scope + "_" + self.profile.fingerprint

    def provision(self, ctx):
        """Require index:admin, create a missing collection and reject incompatible vector settings."""
        from qdrant_client import models

        ctx.require("index:admin")
        name = self.collection(ctx)
        if not self.client.collection_exists(name):
            self.client.create_collection(
                name,
                vectors_config=models.VectorParams(
                    size=self.profile.dimensions, distance=models.Distance.COSINE
                ),
            )
        params = self.client.get_collection(name).config.params.vectors
        if params.size != self.profile.dimensions or params.distance != models.Distance.COSINE:
            raise ValueError("incompatible collection")

    def upsert(self, ctx, doc, vector):
        """Require knowledge:write and upsert a normalized vector under a deterministic document UUID."""
        from qdrant_client import models

        ctx.require("knowledge:write")
        self.client.upsert(
            self.collection(ctx),
            wait=True,
            points=[
                models.PointStruct(
                    id=str(uuid.uuid5(uuid.NAMESPACE_URL, doc.id)),
                    vector=validate_vector(vector, self.profile),
                    payload={"id": doc.id, "text": doc.text},
                )
            ],
        )

    def search(self, ctx, vector, limit):
        """Require knowledge:read and retrieve 1..20 matches only from the scoped profile collection."""
        ctx.require("knowledge:read")
        if not 1 <= limit <= 20:
            raise ValueError("limit must be 1..20")
        points = self.client.query_points(
            self.collection(ctx),
            query=validate_vector(vector, self.profile),
            limit=limit,
            with_payload=True,
        ).points
        return [Hit(Document(p.payload["id"], p.payload["text"]), p.score) for p in points]

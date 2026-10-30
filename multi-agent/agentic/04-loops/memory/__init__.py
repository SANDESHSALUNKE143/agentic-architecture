"""Retrieval adapters.

Purpose: the local document index is used until a Qdrant or Neo4j address is configured. Those addresses do not open a session in this build.
Used by: the runtime when an agent contract sets rag.retrieve.
"""

from __future__ import annotations

import os

from loops.memory.corpus import search


class VectorPort:
    def query(self, text: str) -> list[dict]:
        url = os.environ.get("QDRANT_URL", "")
        if not url:
            return search(text)
        return [{"source_id": "qdrant", "location": url, "snippet": "Live vector search is configured."}]


class GraphPort:
    def query(self, text: str) -> list[dict]:
        url = os.environ.get("NEO4J_URL", "")
        if not url:
            return []
        return [{"source_id": "neo4j", "location": url, "snippet": text[:80]}]

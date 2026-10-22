"""Optional live adapters. The local corpus is used until a URL is configured."""

from __future__ import annotations

import os

from shared.memory.corpus import search


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

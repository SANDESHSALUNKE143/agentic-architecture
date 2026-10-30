"""Local documents and a small entity graph.

Purpose: keyword search over the fixture corpus. Citations must be ids this module returned.
Used by: agentic/04-loops/memory/service.py and agentic/05-tools/mcp/tool-gateway/ports.py through search_documents.
"""

from __future__ import annotations

import hashlib
import re

DOCUMENTS = [
    {
        "source_id": "doc-jackets",
        "location": "products/jackets.md",
        "text": "Blue trail jacket is waterproof and listed at 129. Product id p-jacket-blue.",
    },
    {
        "source_id": "doc-returns",
        "location": "policy/returns.md",
        "text": "Returns are accepted within 30 days when the order is still open.",
    },
]

GRAPH = {
    "Jacket": [{"relation": "documented_by", "target": "doc-jackets"}],
    "Returns": [{"relation": "documented_by", "target": "doc-returns"}],
}

KNOWN_SOURCES = {item["source_id"] for item in DOCUMENTS}


def embed(text: str) -> list[float]:
    digest = hashlib.sha256(text.encode()).digest()
    return [byte / 255 for byte in digest[:8]]


STOP = {"the", "and", "for", "what", "does", "say", "about", "with", "from", "that", "this", "are", "was", "how"}


def search(query: str, limit: int = 3) -> list[dict]:
    tokens = []
    for token in re.findall(r"[a-z0-9]+", query.lower()):
        if len(token) > 2 and token not in STOP and token not in tokens:
            tokens.append(token)
    ranked = []
    for document in DOCUMENTS:
        text = document["text"].lower()
        score = sum(1 for token in tokens if token in text)
        if score:
            ranked.append((score, document))
    ranked.sort(key=lambda item: item[0], reverse=True)
    return [
        {
            "source_id": document["source_id"],
            "location": document["location"],
            "snippet": document["text"],
            "embedding": embed(document["text"]),
        }
        for _, document in ranked[:limit]
    ]


def graph_search(query: str) -> list[dict]:
    hits = []
    for name, edges in GRAPH.items():
        if name.lower() in query.lower():
            for edge in edges:
                hits.append({"source_id": f"graph:{name}:{edge['target']}", "location": edge["relation"], "snippet": name})
    return hits


def accept_citations(citations: list[dict]) -> list[dict]:
    kept = []
    for citation in citations:
        source_id = str(citation.get("source_id", ""))
        if source_id in KNOWN_SOURCES or source_id.startswith(("graph:", "product:", "dataset:", "web:")):
            kept.append(citation)
    return kept

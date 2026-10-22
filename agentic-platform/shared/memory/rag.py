"""Classic, hybrid, graph, corrective, agentic, and multi-hop retrieval.

Answers cite only rows this module returned. Empty retrieval does not invent a fact.
"""

from __future__ import annotations

import math
import re
from typing import Any

from agentic_sdk.adapters.local import HashEmbedder

from shared.memory.corpus import DOCUMENTS, GRAPH
from shared.security.redact import strip_untrusted

_EMBEDDER = HashEmbedder()
MAX_NEIGHBORS = 8


def _tokens(text: str) -> set[str]:
    return set(re.findall(r"[a-z0-9]+", text.lower()))


def _cosine(left: list[float], right: list[float]) -> float:
    dot = sum(a * b for a, b in zip(left, right))
    left_n = math.sqrt(sum(a * a for a in left)) or 1.0
    right_n = math.sqrt(sum(b * b for b in right)) or 1.0
    return dot / (left_n * right_n)


def _keyword_score(query: str, text: str) -> float:
    q = _tokens(query)
    if not q:
        return 0.0
    overlap = q & _tokens(text)
    return len(overlap) / len(q)


def _chunk(doc: dict[str, str]) -> dict[str, Any]:
    safe = strip_untrusted(doc["text"])
    return {
        "source_id": doc["id"],
        "title": doc["title"],
        "location": "chunk:0",
        "entity": doc["entity"],
        "text": safe,
        "simulated": True,
    }


class Retrieval:
    """Local retrieval. Qdrant and Neo4j replace this only when configured."""

    def __init__(self) -> None:
        self.embedder = _EMBEDDER
        self.docs = [_chunk(doc) for doc in DOCUMENTS]
        self.vectors = [self.embedder.embed(doc["text"]) for doc in self.docs]
        self.backend = "local-hash"
        self.graph_backend = "local-graph"

    def search(self, query: str, limit: int = 3) -> list[dict[str, Any]]:
        """Hybrid rank: keyword overlap plus the hash embedding score."""
        if not query.strip():
            return []
        qv = self.embedder.embed(query)
        ranked = []
        for doc, vector in zip(self.docs, self.vectors):
            keyword = _keyword_score(query, doc["text"] + " " + doc["title"])
            embedding = _cosine(qv, vector)
            if keyword <= 0:
                continue
            ranked.append(
                {
                    **{k: v for k, v in doc.items() if k != "text"},
                    "excerpt": doc["text"][:240],
                    "keyword_score": round(keyword, 3),
                    "embedding_score": round(embedding, 3),
                    "score": round(keyword * 0.6 + embedding * 0.4, 3),
                    "signals": _signals(keyword, embedding),
                }
            )
        ranked.sort(key=lambda row: row["score"], reverse=True)
        return ranked[:limit]

    def expand_entity(self, entity: str) -> dict[str, Any]:
        """One graph hop. The caller names an entity and does not send a graph query."""
        name = entity.strip()
        if not name or len(name) > 200:
            return {
                "entity": entity,
                "neighbors": [],
                "passages": [],
                "error": "entity is required",
            }
        rows = GRAPH.get(name, [])[:MAX_NEIGHBORS]
        neighbors = [{"relation": row["relation"], "target": row["target"]} for row in rows]
        passages = []
        for row in rows:
            if row["passage"] not in passages and len(passages) < 4:
                passages.append(strip_untrusted(row["passage"]))
        return {
            "entity": name,
            "neighbors": neighbors,
            "passages": passages,
            "simulated": True,
            "backend": self.graph_backend,
        }

    def run_pattern(self, pattern: str, query: str) -> dict[str, Any]:
        """Execute one named RAG pattern and return citations plus a grounded answer."""
        pattern = pattern or "classic"
        if pattern == "graph":
            return self._graph(query)
        if pattern == "corrective":
            return self._corrective(query)
        if pattern == "multi_hop":
            return self._multi_hop(query)
        if pattern == "hybrid":
            return self._pack("hybrid", query, self.search(query))
        if pattern == "agentic":
            return self._agentic(query)
        return self._pack("classic", query, self.search(query))

    def _pack(self, pattern: str, query: str, hits: list[dict[str, Any]]) -> dict[str, Any]:
        citations = [_cite(hit) for hit in hits]
        if not hits:
            answer = "The source material does not establish an answer."
        else:
            answer = " ".join(hit["excerpt"] for hit in hits)
        return {
            "pattern": pattern,
            "query": query,
            "answer": answer,
            "citations": citations,
            "hits": hits,
            "established": bool(hits),
            "backend": self.backend,
        }

    def _graph(self, query: str) -> dict[str, Any]:
        entity = _entity_from_query(query)
        expanded = self.expand_entity(entity)
        citations = [
            {
                "source_id": f"graph:{expanded['entity']}:{row['target']}",
                "location": row["relation"],
                "title": row["target"],
            }
            for row in expanded["neighbors"]
        ]
        if not expanded["passages"]:
            answer = "The source material does not establish an answer."
        else:
            answer = " ".join(expanded["passages"])
        return {
            "pattern": "graph",
            "query": query,
            "entity": entity,
            "answer": answer,
            "citations": citations,
            "graph": expanded,
            "established": bool(expanded["passages"]),
            "backend": self.graph_backend,
        }

    def _corrective(self, query: str) -> dict[str, Any]:
        first = self.search(query)
        searches = [{"query": query, "hits": len(first)}]
        if first:
            packed = self._pack("corrective", query, first)
            packed["searches"] = searches
            return packed
        refined = _refine(query)
        second = self.search(refined)
        searches.append({"query": refined, "hits": len(second)})
        packed = self._pack("corrective", refined, second)
        packed["searches"] = searches
        if not second:
            packed["answer"] = "The source material does not establish an answer."
            packed["established"] = False
        return packed

    def _agentic(self, query: str) -> dict[str, Any]:
        """First search, then one refined search when the first pass is weak."""
        first = self.search(query)
        searches = [{"query": query, "hits": len(first)}]
        hits = first
        if not first or max(hit["score"] for hit in first) < 0.45:
            refined = _refine(query)
            second = self.search(refined)
            searches.append({"query": refined, "hits": len(second)})
            hits = second or first
        packed = self._pack("agentic", query, hits)
        packed["searches"] = searches
        return packed

    def _multi_hop(self, query: str) -> dict[str, Any]:
        first = self.search(query)
        entity = first[0]["entity"] if first else _entity_from_query(query)
        expanded = self.expand_entity(entity)
        extra = []
        for passage in expanded["passages"]:
            extra.extend(self.search(passage, limit=1))
        seen = set()
        hits = []
        for hit in first + extra:
            if hit["source_id"] in seen:
                continue
            seen.add(hit["source_id"])
            hits.append(hit)
        packed = self._pack("multi_hop", query, hits)
        packed["entity"] = entity
        packed["graph"] = expanded
        packed["hops"] = ["search", "expand_entity", "search"]
        graph_cites = [
            {
                "source_id": f"graph:{entity}:{row['target']}",
                "location": row["relation"],
                "title": row["target"],
            }
            for row in expanded["neighbors"]
        ]
        packed["citations"] = packed["citations"] + graph_cites
        return packed


def known_source_ids() -> set[str]:
    """Document ids and graph neighbor ids this process can cite."""
    ids = {doc["id"] for doc in DOCUMENTS}
    for entity, rows in GRAPH.items():
        for row in rows:
            ids.add(f"graph:{entity}:{row['target']}")
    return ids


def accept_citations(citations: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Drop a citation whose source id was not retrieved from the local corpus or graph."""
    known = known_source_ids()
    return [row for row in citations if isinstance(row, dict) and row.get("source_id") in known]


def _cite(hit: dict[str, Any]) -> dict[str, str]:
    return {
        "source_id": hit["source_id"],
        "location": hit.get("location", "chunk:0"),
        "title": hit.get("title", hit["source_id"]),
    }


def _entity_from_query(query: str) -> str:
    lowered = query.lower()
    if "earthquake" in lowered or "aftershock" in lowered:
        return "Earthquake"
    if "refund" in lowered or "return" in lowered:
        return "Returns"
    if "jacket" in lowered or "nylon" in lowered or "blue" in lowered:
        return "Jacket"
    return "Jacket"


def _refine(query: str) -> str:
    lowered = query.lower()
    if "jacket" in lowered or "apparel" in lowered or "trail" in lowered:
        return "blue trail jacket weight"
    if "refund" in lowered or "order" in lowered:
        return "refund open orders"
    return query


def _signals(keyword: float, embedding: float) -> list[str]:
    found = []
    if keyword > 0:
        found.append("keyword")
    if embedding >= 0.2:
        found.append("embedding")
    return found

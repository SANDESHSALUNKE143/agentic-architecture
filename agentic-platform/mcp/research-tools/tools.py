"""Document and literature search. The retrieval service does the ranking."""

from __future__ import annotations

from shared.memory.rag import Retrieval

_RETRIEVAL = Retrieval()


async def search_documents(ctx, arguments):
    pattern = arguments.get("pattern", "classic")
    packed = _RETRIEVAL.run_pattern(pattern, arguments.get("query", ""))
    return {"result": packed, "simulated": True}


async def expand_entity(ctx, arguments):
    return _RETRIEVAL.expand_entity(arguments.get("entity", ""))


async def search_literature(ctx, arguments):
    query = arguments.get("query", "")
    return {
        "papers": [
            {
                "id": "paper-1",
                "title": f"Simulated note on {query or 'the topic'}",
                "source_id": "lit-local-1",
                "location": "abstract",
            }
        ],
        "simulated": True,
        "label": "simulated literature",
    }

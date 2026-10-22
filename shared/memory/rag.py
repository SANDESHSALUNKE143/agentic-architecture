"""RAG choices on an agent contract. Backends stay local until the environment names them."""

from __future__ import annotations

import os

VECTORS = ("local", "qdrant", "aws")
EMBEDDINGS = ("local", "openai", "aws")
MODELS = ("platform", "openai", "aws")
CADENCE = ("off", "each_run", "hourly", "daily")

_ROWS = {
    "vector": [
        ("local", "Local index", "The documents in this process.", "", "Reading the local document index.", "Reading the local document index."),
        ("qdrant", "Qdrant", "A Qdrant collection. This build still answers from the local index when the URL is empty.", "QDRANT_URL", "Using the local index until QDRANT_URL is set.", "Qdrant is configured. The URL is not shown, and this build still answers from the local index."),
        ("aws", "AWS vector", "An AWS vector index, such as Amazon OpenSearch or S3 Vectors.", "AWS_VECTOR_INDEX", "Using the local index until AWS_VECTOR_INDEX is set.", "An AWS vector index is configured. The value is not shown, and this build still answers from the local index."),
    ],
    "embedding": [
        ("local", "Local embeddings", "A hash of the text, kept in this process.", "", "Embedding in this process.", "Embedding in this process."),
        ("openai", "OpenAI-compatible embeddings", "An embedding model on the same host as the chat model.", "EMBEDDING_MODEL", "Using local embeddings until EMBEDDING_MODEL is set.", "An embedding model name is set. This build still embeds locally."),
        ("aws", "AWS embeddings", "An Amazon Bedrock embedding model.", "AWS_EMBEDDING_MODEL", "Using local embeddings until AWS_EMBEDDING_MODEL is set.", "An AWS embedding model is set. The value is not shown. This build still embeds locally."),
    ],
    "model": [
        ("platform", "Platform model", "The process default: mock, or live when the platform is in live mode.", "", "Using the platform model.", "Using the platform model."),
        ("openai", "OpenAI-compatible model", "Chat on the configured model host. The key stays in the API environment.", "Model key", "Using the platform model until a model key is set.", "A model key is set. The value is not shown."),
        ("aws", "AWS Bedrock", "A Bedrock chat model. This build does not call AWS.", "AWS_BEDROCK_MODEL", "Using the platform model until AWS_BEDROCK_MODEL is set.", "A Bedrock model id is set. The value is not shown. This build still uses the platform model."),
    ],
}

_SECRET = {
    ("model", "openai"): "MODEL_API_KEY",
}


def default_rag() -> dict:
    return {"retrieve": False, "capture": False, "vector": "local", "embedding": "local", "cadence": "off"}


def default_model() -> dict:
    return {"provider": "platform"}


def normalize_rag(raw, path) -> dict:
    incoming = dict(default_rag() if raw is None else raw)
    retrieve = bool(incoming.get("retrieve"))
    capture = bool(incoming.get("capture"))
    vector = str(incoming.get("vector") or "local")
    embedding = str(incoming.get("embedding") or "local")
    if vector not in VECTORS or embedding not in EMBEDDINGS:
        raise ValueError(f"{path} names an unknown RAG vector or embedding.")
    cadence = str(incoming.get("cadence") or ("each_run" if capture else "off"))
    if cadence not in CADENCE:
        raise ValueError(f"{path} names an unknown ingestion cadence.")
    if not capture:
        cadence = "off"
    return {"retrieve": retrieve, "capture": capture, "vector": vector, "embedding": embedding, "cadence": cadence}


def normalize_model(raw, path) -> dict:
    incoming = dict(default_model() if raw is None else raw)
    provider = str(incoming.get("provider") or "platform")
    if provider not in MODELS:
        raise ValueError(f"{path} names an unknown model provider.")
    return {"provider": provider}


def describe(env: dict[str, str] | None = None) -> dict[str, list[dict]]:
    source = os.environ if env is None else env
    catalog: dict[str, list[dict]] = {}
    for kind, rows in _ROWS.items():
        catalog[kind] = []
        for item_id, title, summary, variable, local_detail, live_detail in rows:
            secret = _SECRET.get((kind, item_id), variable)
            mapped = {
                ("vector", "qdrant"): ("qdrant", "QDRANT_URL"),
                ("vector", "aws"): ("aws_vector", "AWS_VECTOR_INDEX"),
                ("embedding", "openai"): ("embedding", "EMBEDDING_BASE_URL"),
                ("model", "openai"): ("model", "MODEL_BASE_URL"),
            }
            if (kind, item_id) in mapped:
                from shared.security.endpoints import is_configured

                configured = is_configured(mapped[(kind, item_id)][0], mapped[(kind, item_id)][1], source)
            else:
                configured = True if not secret else bool(source.get(secret))
            catalog[kind].append({
                "id": item_id,
                "kind": kind,
                "title": title,
                "summary": summary,
                "variable": variable or "In this process",
                "configured": configured,
                "detail": live_detail if configured and secret else local_detail,
            })
    return catalog


def retrieve(kind_vector: str, query: str) -> list[dict]:
    """Read the index for one agent. A configured backend does not reveal its address."""

    from shared.memory.corpus import search

    if kind_vector == "qdrant" and _backend_ready("qdrant", "QDRANT_URL"):
        return [{"source_id": "dataset:qdrant", "location": "qdrant", "snippet": "Qdrant is configured."}]
    if kind_vector == "aws" and _backend_ready("aws_vector", "AWS_VECTOR_INDEX"):
        return [{"source_id": "dataset:aws", "location": "aws", "snippet": "The AWS vector index is configured."}]
    return search(query)


def _backend_ready(endpoint_id: str, env_name: str) -> bool:
    from shared.security.endpoints import is_configured

    return is_configured(endpoint_id, env_name)

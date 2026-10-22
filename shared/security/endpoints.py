"""Host configuration for every external system this platform names.

This repository does not host n8n, Grafana, Qdrant, or AWS. The operator sets the
URL, connection string, username, and password. The password is stored in the
data directory and is never returned by the API.
"""

from __future__ import annotations

import json
import os

from shared.config import data_dir

ENDPOINTS: list[dict[str, str]] = [
    {
        "id": "n8n",
        "title": "n8n",
        "group": "Automation",
        "summary": "This repository does not host n8n. Enter the URL of the n8n you run.",
        "env_url": "N8N_BASE_URL",
        "env_secret": "N8N_TOKEN",
    },
    {
        "id": "grafana",
        "title": "Grafana",
        "group": "Observability",
        "summary": "The Grafana address where dashboards and traces are opened.",
        "env_url": "GRAFANA_URL",
        "env_secret": "GRAFANA_PASSWORD",
    },
    {
        "id": "otlp",
        "title": "OpenTelemetry",
        "group": "Observability",
        "summary": "The collector that receives traces.",
        "env_url": "OTEL_EXPORTER_OTLP_ENDPOINT",
        "env_secret": "",
    },
    {
        "id": "log_store",
        "title": "Log store",
        "group": "Observability",
        "summary": "The store that will read the trace export.",
        "env_url": "OBSERVABILITY_LOG_URL",
        "env_secret": "",
    },
    {
        "id": "qdrant",
        "title": "Qdrant",
        "group": "RAG",
        "summary": "The vector database URL used when an agent selects Qdrant.",
        "env_url": "QDRANT_URL",
        "env_secret": "QDRANT_API_KEY",
    },
    {
        "id": "aws_vector",
        "title": "AWS vector",
        "group": "RAG",
        "summary": "The AWS vector endpoint. Use the access key as the username and the secret key as the password.",
        "env_url": "AWS_VECTOR_ENDPOINT",
        "env_secret": "AWS_SECRET_ACCESS_KEY",
    },
    {
        "id": "embedding",
        "title": "Embedding model",
        "group": "RAG",
        "summary": "The direct URL of the embedding model host.",
        "env_url": "EMBEDDING_BASE_URL",
        "env_secret": "EMBEDDING_API_KEY",
    },
    {
        "id": "model",
        "title": "Model host",
        "group": "RAG",
        "summary": "The direct URL of the chat model host.",
        "env_url": "MODEL_BASE_URL",
        "env_secret": "MODEL_API_KEY",
    },
    {
        "id": "sql",
        "title": "SQL",
        "group": "Data",
        "summary": "The database connection string. A string saved here is shown again. A string set only in the environment is not shown.",
        "env_url": "",
        "env_secret": "",
    },
    {
        "id": "neo4j",
        "title": "Neo4j",
        "group": "Data",
        "summary": "The graph database URL, username, and password.",
        "env_url": "NEO4J_URL",
        "env_secret": "NEO4J_PASSWORD",
    },
]


def _path():
    return data_dir() / "connections.json"


def _read() -> dict:
    path = _path()
    if not path.exists():
        return {}
    try:
        loaded = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}
    return loaded if isinstance(loaded, dict) else {}


def _write(payload: dict) -> None:
    path = _path()
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def saved(endpoint_id: str) -> dict:
    item = _read().get(endpoint_id) or {}
    return item if isinstance(item, dict) else {}


def is_configured(endpoint_id: str, env_name: str = "", env: dict | None = None) -> bool:
    source = os.environ if env is None else env
    if env_name and source.get(env_name):
        return True
    item = saved(endpoint_id)
    return bool(str(item.get("url") or "").strip() or str(item.get("connection_string") or "").strip())


def target(endpoint_id: str, env_name: str = "") -> str:
    item = saved(endpoint_id)
    typed = str(item.get("url") or "").strip()
    if typed:
        return typed
    if env_name:
        return os.environ.get(env_name, "").strip()
    return ""


def public() -> list[dict]:
    rows = []
    for spec in ENDPOINTS:
        item = saved(spec["id"])
        env_url = os.environ.get(spec["env_url"], "").strip() if spec["env_url"] else ""
        url = str(item.get("url") or "").strip() or env_url
        secret_env = os.environ.get(spec["env_secret"], "").strip() if spec["env_secret"] else ""
        rows.append({
            "id": spec["id"],
            "title": spec["title"],
            "group": spec["group"],
            "summary": spec["summary"],
            "url": url,
            "connection_string": str(item.get("connection_string") or ""),
            "username": str(item.get("username") or ""),
            "password_set": bool(str(item.get("password") or "").strip() or secret_env),
            "configured": is_configured(spec["id"], spec["env_url"] or spec["env_secret"]),
        })
    return rows


def update(endpoint_id: str, url: str, connection_string: str, username: str, password: str) -> dict:
    known = {spec["id"] for spec in ENDPOINTS}
    if endpoint_id not in known:
        raise ValueError("Unknown connection.")
    current = _read()
    previous = current.get(endpoint_id) if isinstance(current.get(endpoint_id), dict) else {}
    kept_password = str(previous.get("password") or "")
    incoming_password = password.strip()
    current[endpoint_id] = {
        "url": url.strip()[:500],
        "connection_string": connection_string.strip()[:1000],
        "username": username.strip()[:200],
        "password": incoming_password[:200] if incoming_password else kept_password,
    }
    _write(current)
    return next(row for row in public() if row["id"] == endpoint_id)

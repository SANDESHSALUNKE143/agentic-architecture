"""Saved addresses for systems this repository does not host.

Purpose: store a URL, connection string, username, and password for n8n, Grafana, Qdrant, AWS, SQL, and Neo4j. The password is not returned.
Used by: the settings connection routes and the port checks in the gateway.
"""

from __future__ import annotations

import json
import os

from guardrails.connections.endpoint_specs import ENDPOINTS

from agentic.platform.config import data_dir


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


def ready(endpoint_id: str) -> bool:
    spec = next((item for item in ENDPOINTS if item["id"] == endpoint_id), None)
    if spec is None:
        return False
    probe = spec.get("env_name") or spec["env_url"] or spec["env_secret"]
    return is_configured(spec["id"], probe)


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
            "configured": ready(spec["id"]),
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

"""
Admin connection profile for the insight agent.

Bindings holds the allowlisted names the running process may use. public()
returns server URLs with the password removed. apply() checks the names,
points the live tools at them, and store_revision() appends one immutable
configuration row. The operator console reads that row. It does not write it.

Usage:
    bindings = Bindings()
    apply(bindings, sql, models, web, tools, allowlists, incoming)
    stored = store_revision(bindings)
"""

import os
import re
from dataclasses import replace
from urllib.parse import urlsplit

# ── Name rules ────────────────────────────────────────────────────────

_NAME = re.compile(r"^[A-Za-z_][A-Za-z0-9_]{0,62}$")
_HOST = re.compile(r"^[A-Za-z0-9][A-Za-z0-9.-]{0,251}[A-Za-z0-9]$")
_LABEL = re.compile(r"^[A-Za-z][A-Za-z0-9 ._-]{0,39}$")


# ── Live profile ──────────────────────────────────────────────────────


class Bindings:
    """
    Connection names the running agent is allowed to use.

    Usage:
        bindings = Bindings()
        view = bindings.public()
    """

    def __init__(self):
        self.sql_table = "city_metrics"
        self.retrieval = "qdrant"
        self.graph = "Neo4j"
        self.model_id = "city_trend"
        self.web_host = "stats.example"

    def public(self) -> dict:
        """Return endpoints an admin can read. Passwords are never included."""
        database = _endpoint(os.environ["DATABASE_URL"])
        vectors = _endpoint(os.environ["QDRANT_URL"])
        graph = _endpoint(os.environ["NEO4J_URL"])
        site = _endpoint(os.environ["SITE_ORIGIN"])
        return {
            "sql": {
                "system": "Postgres",
                "table": self.sql_table,
                "url": database["url"],
                "host": database["host"],
                "port": database["port"],
                "database": database["database"],
                "user": database["user"],
                "secret": "Held in the environment",
            },
            "retrieval": {
                "system": "Qdrant",
                "name": self.retrieval,
                "url": vectors["url"],
                "host": vectors["host"],
                "port": vectors["port"],
                "collection": _collection(),
                "secret": "Held in the environment",
            },
            "graph": {
                "system": "Neo4j",
                "name": self.graph,
                "url": graph["url"],
                "host": graph["host"],
                "port": graph["port"],
                "user": os.environ.get("NEO4J_USER", ""),
                "secret": "Held in the environment",
            },
            "model": {
                "system": "Model registry",
                "model_id": self.model_id,
                "url": "in-process",
                "host": "insight-agent",
                "port": None,
                "runtime": "Registered in this process. No remote inference server.",
            },
            "web": {
                "system": "Allowlisted site",
                "host": self.web_host,
                "url": site["url"],
                "server": site["host"],
                "port": site["port"],
            },
        }


# ── Apply a saved profile ─────────────────────────────────────────────


def apply(bindings, sql, models, web, tools, allowlists, incoming: dict) -> None:
    """
    Replace the live allowlist with one validated admin profile.

    Steps:
        1. Reject names that are not simple identifiers or a bare host.
        2. Point the SQL adapter, model registry, and web allowlist at them.
        3. Update the tool argument enums so the model can only ask for those names.
    """
    table = incoming["sql_table"]
    retrieval = incoming["retrieval"]
    graph = incoming["graph"]
    model_id = incoming["model_id"]
    host = incoming["web_host"]
    if not _NAME.fullmatch(table) or not _NAME.fullmatch(model_id):
        raise ValueError("table and model must be simple names")
    if not _HOST.fullmatch(host) or "://" in host:
        raise ValueError("web host must be a bare name")
    if not _LABEL.fullmatch(retrieval) or not _LABEL.fullmatch(graph):
        raise ValueError("retrieval and graph labels must be short names")
    previous_model = bindings.model_id
    previous_host = bindings.web_host
    bindings.sql_table = table
    bindings.retrieval = retrieval
    bindings.graph = graph
    bindings.model_id = model_id
    bindings.web_host = host
    sql.tables = frozenset({table})
    _enum(tools, "query_metrics", "table", table)
    _enum(tools, "predict_trend", "model_id", model_id)
    _enum(tools, "fetch_site", "host", host)
    if model_id != previous_model:
        models.models[model_id] = models.models.pop(previous_model)
    if host != previous_host:
        web.bases[host] = web.bases.pop(previous_host)
    allowlists["sql_tables"] = [table]
    allowlists["models"] = [model_id]
    allowlists["web_hosts"] = [host]
    allowlists["retrieval"] = retrieval
    allowlists["graph"] = graph


def _enum(tools, tool_name: str, field: str, value: str) -> None:
    """Point one tool argument at the newly saved allowlist value."""
    spec = tools._tools[tool_name]
    schema = {
        "type": spec.input_schema["type"],
        "properties": {key: dict(item) for key, item in spec.input_schema["properties"].items()},
        "required": list(spec.input_schema["required"]),
    }
    schema["properties"][field]["enum"] = [value]
    tools._tools[tool_name] = replace(spec, input_schema=schema)


# ── Immutable revisions ───────────────────────────────────────────────


def store_revision(bindings) -> dict:
    """Append one immutable configuration revision for this agent."""
    from agentic_sdk.adapters.persistence.postgres import Database
    from psycopg.types.json import Jsonb

    database = Database(os.environ["DATABASE_URL"])
    database.initialize()
    config = {
        "agent_id": "insight-agent",
        "tenant_id": "example-tenant",
        "connections": bindings.public(),
        "framework": "sdk",
    }
    with database.connect() as connection:
        connection.execute(
            "SELECT pg_advisory_xact_lock(hashtextextended(%s,0))",
            ("example-tenant:insight-agent",),
        )
        latest = connection.execute(
            """SELECT COALESCE(MAX(revision),0) AS revision
            FROM configurations WHERE tenant=%s AND agent=%s""",
            ("example-tenant", "insight-agent"),
        ).fetchone()["revision"]
        connection.execute(
            "INSERT INTO configurations VALUES(%s,%s,%s,%s)",
            ("example-tenant", "insight-agent", latest + 1, Jsonb(config)),
        )
    return {"revision": latest + 1, "connections": config["connections"]}


def _endpoint(raw: str) -> dict:
    """Split a URL and drop any user password before it can reach the admin page."""
    parts = urlsplit(raw)
    host = parts.hostname or ""
    port = parts.port
    user = parts.username or ""
    netloc = host if port is None else f"{host}:{port}"
    if user:
        url = f"{parts.scheme}://{user}@{netloc}{parts.path}"
    else:
        url = f"{parts.scheme}://{netloc}{parts.path}"
    return {
        "url": url,
        "host": host,
        "port": port,
        "user": user or None,
        "database": parts.path.lstrip("/") or None,
    }


def _collection() -> str:
    """Match the Qdrant collection name the retrieval adapter derives for this agent."""
    import hashlib

    from agentic_sdk.adapters.local import HashEmbedder

    scope = hashlib.sha256(b"example-tenant\0insight-agent").hexdigest()
    return "a_" + scope + "_" + HashEmbedder().profile.fingerprint


def current_revision() -> int:
    """Return the latest stored revision, or 0 when nothing has been published."""
    from agentic_sdk.adapters.persistence.postgres import Database

    database = Database(os.environ["DATABASE_URL"])
    database.initialize()
    with database.connect() as connection:
        row = connection.execute(
            """SELECT COALESCE(MAX(revision),0) AS revision
            FROM configurations WHERE tenant=%s AND agent=%s""",
            ("example-tenant", "insight-agent"),
        ).fetchone()
    return int(row["revision"])

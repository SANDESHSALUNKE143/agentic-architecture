"""
Environment for the insight agent.

Opens Postgres, Qdrant, Neo4j, the model registry, and the allowlisted site.
Seeds the sample analyses and the city graph. The agent chooses these
servers. The SDK checks the permission, the allowlist, and the cap.

Usage:
    ports = open_environment()
"""

import os
import threading
import time
from collections.abc import Callable
from dataclasses import dataclass

import psycopg
from agentic_sdk.adapters.graph.neo4j import Neo4jGraphRag
from agentic_sdk.adapters.inference.registry import ModelRegistry
from agentic_sdk.adapters.local import HashEmbedder
from agentic_sdk.adapters.retrieval.qdrant import QdrantStore
from agentic_sdk.adapters.sql.read import ReadOnlySql
from agentic_sdk.adapters.tools.web import AllowlistedWeb
from agentic_sdk.contracts import Context, Document
from neo4j import GraphDatabase
from psycopg.rows import dict_row
from qdrant_client import QdrantClient

# ── Open ports ────────────────────────────────────────────────────────


@dataclass
class Ports:
    """The stores this agent opened and the SQL reconnect function."""

    sql: ReadOnlySql
    store: QdrantStore
    embedder: HashEmbedder
    graph: Neo4jGraphRag
    models: ModelRegistry
    web: AllowlistedWeb
    connect_sql: Callable


# ── Fixtures ──────────────────────────────────────────────────────────

ANALYSES = (
    {
        "id": "analysis-2025q4-pune",
        "text": (
            "Last quarter the Pune review concluded demand was rising "
            "after the infrastructure survey."
        ),
    },
    {
        "id": "analysis-2025q4-mumbai",
        "text": "The Mumbai review concluded the index was flat and recommended no expansion.",
    },
)


def _wait(label, action, attempts=60):
    """Retry a dependency until it accepts a connection or the attempts run out."""
    last = None
    for _ in range(attempts):
        try:
            return action()
        except Exception as exc:
            last = exc
            time.sleep(2)
    raise RuntimeError(f"{label} did not become ready") from last


class _SessionPool:
    """Open a short Neo4j session per call so concurrent requests do not share one."""

    def __init__(self, driver):
        self.driver = driver
        self.lock = threading.Lock()

    def run(self, cypher, **kwargs):
        """Execute one Cypher statement and return materialized records."""
        with self.lock:
            with self.driver.session() as session:
                return [record for record in session.run(cypher, **kwargs)]


def _trend(features: dict) -> dict:
    """Label one city from its index. This is a registered callable, not a trainer."""
    if set(features) != {"city", "index_value"}:
        from agentic_sdk.contracts.orchestration.types import ExecutionError

        raise ExecutionError("city_trend features must be city and index_value")
    value = float(features["index_value"])
    if value >= 1.2:
        label = "rising"
    elif value >= 0.9:
        label = "flat"
    else:
        label = "soft"
    return {
        "model_id": "city_trend",
        "city": features["city"],
        "label": label,
        "score": round(value, 3),
    }


def _seed_graph(driver):
    """Insert the sample city graph if this process is starting against an empty database."""
    statements = [
        (
            "Pune",
            "rising_demand",
            "has_signal",
            "Graph note: rising_demand is linked to cities whose latest index increased.",
        ),
        (
            "Pune",
            "West",
            "in_region",
            "Graph note: West groups Pune and Mumbai for regional comparison.",
        ),
        (
            "Mumbai",
            "flat",
            "has_signal",
            "Graph note: flat means the latest index did not clear the expansion line.",
        ),
    ]
    with driver.session() as session:
        for source, target, relation, passage in statements:
            session.run(
                f"""
                MERGE (source:Entity {{name: $source}})
                MERGE (target:Entity {{name: $target}})
                SET target.passage = $passage
                MERGE (source)-[:{relation}]->(target)
                """,
                source=source,
                target=target,
                passage=passage,
            )


def _connect_sql():
    """Open one Postgres connection. Keepalives let an idle prototype survive a quiet hour."""
    return psycopg.connect(
        os.environ["DATABASE_URL"],
        row_factory=dict_row,
        connect_timeout=5,
        keepalives=1,
        keepalives_idle=30,
        keepalives_interval=10,
        keepalives_count=3,
    )


# ── Open ──────────────────────────────────────────────────────────────


def open_environment():
    """
    Connect the stores this agent calls and seed the fixtures.

    Steps:
        1. Wait until Postgres, Qdrant, and Neo4j accept a connection.
        2. Seed the sample analyses and the city graph.
        3. Return the live adapters the tools will call.
    """
    connection = _wait("postgres", _connect_sql)
    sql = ReadOnlySql(
        connection,
        tables=frozenset({"city_metrics"}),
        row_cap=20,
        timeout_ms=5000,
        paramstyle="pyformat",
    )
    embedder = HashEmbedder()
    qdrant = _wait(
        "qdrant",
        lambda: QdrantClient(
            url=os.environ["QDRANT_URL"],
            api_key=os.environ["QDRANT_API_KEY"],
            timeout=10,
        ),
    )
    store = QdrantStore(qdrant, embedder.profile)
    admin = Context(
        "example-tenant",
        "insight-agent",
        frozenset({"index:admin", "knowledge:write", "knowledge:read"}),
    )
    store.provision(admin)
    for item in ANALYSES:
        store.upsert(admin, Document(item["id"], item["text"]), embedder.embed(item["text"]))
    driver = _wait(
        "neo4j",
        lambda: GraphDatabase.driver(
            os.environ["NEO4J_URL"],
            auth=(os.environ["NEO4J_USER"], os.environ["NEO4J_PASSWORD"]),
        ),
    )
    _wait("neo4j-query", lambda: driver.verify_connectivity())
    _seed_graph(driver)
    graph = Neo4jGraphRag(_SessionPool(driver), max_neighbors=8)
    models = ModelRegistry({"city_trend": _trend})
    web = AllowlistedWeb({"stats.example": os.environ["SITE_ORIGIN"]})
    return Ports(sql, store, embedder, graph, models, web, _connect_sql)

"""Guardrails for SQL, Graph RAG, inference and allowlisted web connectors."""

import sqlite3
import unittest

from agentic_sdk.adapters.graph.neo4j import Neo4jGraphRag
from agentic_sdk.adapters.inference.registry import ModelRegistry
from agentic_sdk.adapters.sql.read import ReadOnlySql
from agentic_sdk.adapters.tools.web import AllowlistedWeb
from agentic_sdk.contracts import Context
from agentic_sdk.contracts.orchestration.types import ExecutionError


def _ctx(*permissions: str) -> Context:
    return Context("tenant", "agent", frozenset(permissions))


class SqlConnectorTests(unittest.TestCase):
    def setUp(self):
        self.db = sqlite3.connect(":memory:")
        self.db.row_factory = sqlite3.Row
        self.db.execute("CREATE TABLE city_metrics (city TEXT, index_value REAL)")
        self.db.execute("INSERT INTO city_metrics VALUES ('Pune', 1.4)")
        self.db.execute("INSERT INTO city_metrics VALUES ('Mumbai', 1.0)")
        self.sql = ReadOnlySql(self.db, tables=frozenset({"city_metrics"}), row_cap=1)

    def test_unknown_table_is_rejected(self):
        with self.assertRaises(ExecutionError):
            self.sql.query(_ctx("sql:read"), "configurations", 1)

    def test_row_cap_is_enforced(self):
        with self.assertRaises(ExecutionError):
            self.sql.query(_ctx("sql:read"), "city_metrics", 2)
        rows = self.sql.query(_ctx("sql:read"), "city_metrics", 1)["rows"]
        self.assertEqual(len(rows), 1)

    def test_missing_permission_does_no_work(self):
        with self.assertRaises(PermissionError):
            self.sql.query(_ctx(), "city_metrics", 1)


class GraphConnectorTests(unittest.TestCase):
    def test_one_hop_is_bounded(self):
        class Session:
            def __init__(self):
                self.kwargs = None

            def run(self, cypher, **kwargs):
                self.kwargs = kwargs
                self.cypher = cypher
                return [
                    {"relation": "has_signal", "target": f"n{i}", "passage": f"p{i}"}
                    for i in range(6)
                ]

        session = Session()
        graph = Neo4jGraphRag(session, max_neighbors=2)
        result = graph.expand(_ctx("graph:read"), "Pune")
        self.assertEqual(len(result["neighbors"]), 2)
        self.assertLessEqual(len(result["passages"]), 4)
        self.assertIn("LIMIT $limit", session.cypher)
        self.assertEqual(session.kwargs["limit"], 2)
        self.assertEqual(session.kwargs["entity"], "Pune")

    def test_missing_permission(self):
        with self.assertRaises(PermissionError):
            Neo4jGraphRag(object()).expand(_ctx(), "Pune")


class InferenceConnectorTests(unittest.TestCase):
    def test_unknown_model_is_rejected(self):
        registry = ModelRegistry({"city_trend": lambda features: {"label": "rising"}})
        with self.assertRaises(ExecutionError):
            registry.predict(_ctx("model:invoke"), "other", {"city": "Pune"})

    def test_missing_permission(self):
        registry = ModelRegistry({"city_trend": lambda features: {"label": "rising"}})
        with self.assertRaises(PermissionError):
            registry.predict(_ctx(), "city_trend", {"city": "Pune"})


class WebConnectorTests(unittest.TestCase):
    def test_unknown_host_is_rejected_without_a_fetch(self):
        calls = []
        web = AllowlistedWeb(
            {"stats.example": "http://site:8080"},
            opener=lambda url: calls.append(url) or {"ok": True},
        )
        with self.assertRaises(ExecutionError):
            web.fetch(_ctx("web:read"), "evil.example", "/cities/pune")
        self.assertEqual(calls, [])

    def test_missing_permission(self):
        web = AllowlistedWeb({"stats.example": "http://site:8080"}, opener=lambda url: {})
        with self.assertRaises(PermissionError):
            web.fetch(_ctx(), "stats.example", "/cities/pune")


if __name__ == "__main__":
    unittest.main()

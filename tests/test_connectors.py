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
        self.db.execute("CREATE TABLE sample_rows (name TEXT, value REAL)")
        self.db.execute("INSERT INTO sample_rows VALUES ('north', 1.4)")
        self.db.execute("INSERT INTO sample_rows VALUES ('south', 1.0)")
        self.sql = ReadOnlySql(self.db, tables=frozenset({"sample_rows"}), row_cap=1)

    def test_unknown_table_is_rejected(self):
        with self.assertRaises(ExecutionError):
            self.sql.query(_ctx("sql:read"), "configurations", 1)

    def test_row_cap_is_enforced(self):
        with self.assertRaises(ExecutionError):
            self.sql.query(_ctx("sql:read"), "sample_rows", 2)
        rows = self.sql.query(_ctx("sql:read"), "sample_rows", 1)["rows"]
        self.assertEqual(len(rows), 1)

    def test_missing_permission_does_no_work(self):
        with self.assertRaises(PermissionError):
            self.sql.query(_ctx(), "sample_rows", 1)


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
        result = graph.expand(_ctx("graph:read"), "sample-entity")
        self.assertEqual(len(result["neighbors"]), 2)
        self.assertLessEqual(len(result["passages"]), 4)
        self.assertIn("LIMIT $limit", session.cypher)
        self.assertEqual(session.kwargs["limit"], 2)
        self.assertEqual(session.kwargs["entity"], "sample-entity")

    def test_missing_permission(self):
        with self.assertRaises(PermissionError):
            Neo4jGraphRag(object()).expand(_ctx(), "sample-entity")


class InferenceConnectorTests(unittest.TestCase):
    def test_unknown_model_is_rejected(self):
        registry = ModelRegistry({"score_model": lambda features: {"label": "rising"}})
        with self.assertRaises(ExecutionError):
            registry.predict(_ctx("model:invoke"), "other", {"name": "north"})

    def test_missing_permission(self):
        registry = ModelRegistry({"score_model": lambda features: {"label": "rising"}})
        with self.assertRaises(PermissionError):
            registry.predict(_ctx(), "score_model", {"name": "north"})


class WebConnectorTests(unittest.TestCase):
    def test_unknown_host_is_rejected_without_a_fetch(self):
        calls = []
        web = AllowlistedWeb(
            {"notes.example": "http://site:8080"},
            opener=lambda url: calls.append(url) or {"ok": True},
        )
        with self.assertRaises(ExecutionError):
            web.fetch(_ctx("web:read"), "evil.example", "/items/1")
        self.assertEqual(calls, [])

    def test_missing_permission(self):
        web = AllowlistedWeb({"notes.example": "http://site:8080"}, opener=lambda url: {})
        with self.assertRaises(PermissionError):
            web.fetch(_ctx(), "notes.example", "/items/1")


if __name__ == "__main__":
    unittest.main()

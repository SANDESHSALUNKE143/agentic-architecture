"""Runtime checks.

Purpose: route, tools, schema, workflow files, and the order approval amount.
Used by: CI and the local test command. It builds a Platform directly.
"""

from __future__ import annotations

import os
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from agentic.platform.composition import Platform  # noqa: E402
from guardrails.connections.credentials import CredentialStore  # noqa: E402
from jobs.queue.checks import JobRunner  # noqa: E402
from loops.llm import usage_from_payload  # noqa: E402
from loops.memory import GraphPort, VectorPort  # noqa: E402
from response.contracts import AgentRequest, validate_output  # noqa: E402
from workflows.router.router import WORKFLOWS  # noqa: E402


def setUpModule():
    from agentic.platform.loader import load_module

    load_module(ROOT / "tests" / "merchant_server.py", "merchant_test_server").ensure_merchant_server()


class RuntimeTests(unittest.TestCase):
    def setUp(self):
        self.platform = Platform()

    def test_workflow_files_are_the_route(self):
        from agentic.platform.loader import load_module

        for name, agents in WORKFLOWS.items():
            module = load_module(
                ROOT / "agentic" / "03-workflows" / "sequences" / name / "workflow.py",
                f"check_{name.replace('-', '_')}",
            )
            self.assertEqual(list(module.AGENTS), agents)

    def test_jacket_uses_catalog_tools(self):
        run = self.platform.start(AgentRequest(task="Find a blue trail jacket under $150"))
        self.assertEqual(run["workflow"], "product-discovery")
        catalog = next(item for item in run["agents"] if item["agent_id"] == "catalog-agent")
        names = [call["name"] for call in catalog["tool_calls"]]
        self.assertIn("search_products", names)
        self.assertTrue(catalog["result"]["products"])
        self.assertIsNone(validate_output(self.platform.contracts["catalog-agent"].output_schema, catalog["result"]))

    def test_schema_rejects_a_missing_explanation(self):
        schema = self.platform.contracts["catalog-agent"].output_schema
        self.assertIsNotNone(validate_output(schema, {"products": [], "sources": []}))

    def test_denied_tool_and_repeated_call(self):
        contract = self.platform.contracts["catalog-agent"]
        denied = self.platform.gateway.call(
            "run-1",
            contract.permissions,
            contract.tools,
            "prepare_order",
            {"product_id": "p-jacket-blue", "user_id": "local-development-user", "amount": 10},
            contract.approval,
            scope="catalog-agent",
        )
        self.assertEqual(denied["error_code"], "tool_denied")
        args = {"query": "jacket"}
        first = self.platform.gateway.call("run-1", contract.permissions, contract.tools, "search_products", args, {}, scope="catalog-agent")
        second = self.platform.gateway.call("run-1", contract.permissions, contract.tools, "search_products", args, {}, scope="catalog-agent")
        self.assertEqual(first["status"], "completed")
        self.assertEqual(second["error_code"], "loop_detected")

    def test_order_amount_is_read_from_the_contract(self):
        self.assertEqual(self.platform.contracts["order-agent"].approval["amount_gte"], 100)
        small = self.platform.start(AgentRequest(task="Place an order for the jacket at $40"))
        self.assertEqual(small["status"], "completed")
        self.assertFalse(small["agents"][0]["requires_approval"])
        large = self.platform.start(AgentRequest(task="Place an order for the jacket at $129"))
        self.assertEqual(large["status"], "needs_approval")
        self.assertEqual(large["agents"][0]["result"]["amount"], 129.0)
        resumed, error = self.platform.resume(large["approval_id"], "approve", "local-operator")
        self.assertEqual(error, "")
        self.assertEqual(resumed["status"], "completed")
        blocked, error = self.platform.resume(large["approval_id"], "approve", "order-agent")
        self.assertEqual(error, "not_pending")

    def test_settings_reject_a_write_tool_on_a_read_agent(self):
        with self.assertRaises(ValueError):
            self.platform.update_contract(
                "catalog-agent",
                {"tools": ["prepare_order"], "approval": {"required_for": ["prepare_order"]}},
            )
        with self.assertRaises(ValueError):
            self.platform.update_contract("order-agent", {"approval": {"required_for": [], "amount_gte": 100}})

    def test_plugin_connection_stays_inside_permissions(self):
        with self.assertRaises(ValueError):
            self.platform.connect_plugin("prepare_order", ["catalog-agent"])
        catalog = self.platform.plugins()
        search = next(item for item in catalog["plugins"] if item["name"] == "search_products")
        self.assertIn("catalog-agent", search["connected_agents"])
        self.assertTrue(any(item["id"] == "model" and item["configured"] is False for item in catalog["connections"]))
        events = []
        run = self.platform.start(AgentRequest(task="Find a blue trail jacket under $150", agents=["catalog-agent"]), on_event=events.append)
        self.assertEqual(run["workflow"], "agent-chain")
        self.assertTrue(any(event.get("type") == "tool" and event.get("tool") == "search_products" for event in events))
        blocked = self.platform.gateway.call(
            "run-sql",
            {"sql_read": True},
            ["query_sql"],
            "query_sql",
            {"query": "delete from orders"},
            {},
            scope="analysis",
        )
        self.assertEqual(blocked["error_code"], "connection_required")
        from tempfile import TemporaryDirectory

        previous_data = os.environ.get("PLATFORM_DATA_DIR")
        with TemporaryDirectory() as folder:
            os.environ["PLATFORM_DATA_DIR"] = folder
            described = {item["name"]: item for item in self.platform.gateway.describe()}
        if previous_data is None:
            os.environ.pop("PLATFORM_DATA_DIR", None)
        else:
            os.environ["PLATFORM_DATA_DIR"] = previous_data
        self.assertTrue(described["search_products"]["connection_ready"])
        self.assertFalse(described["query_sql"]["connection_ready"])
        self.assertFalse(described["use_mcp_server"]["connection_ready"])
        details = described["get_product_details"]
        self.assertIn("mcp/catalog-tools/tools.py", details["source"])
        self.assertNotIn("http", details["source"])
        self.assertIn("examples/merchant-mcp", details["source"])
        catalog_contract = self.platform.contracts["catalog-agent"]
        fetched = self.platform.gateway.call(
            "run-merchant",
            catalog_contract.permissions,
            catalog_contract.tools,
            "get_product_details",
            {"product_id": "p-jacket-blue"},
            {},
            scope="catalog-agent",
        )
        self.assertEqual(fetched["status"], "completed")
        self.assertEqual(fetched["result"]["products"][0]["price"], 129)
        self.assertNotIn("129", (ROOT / "agentic" / "05-tools" / "mcp" / "catalog-tools" / "tools.py").read_text(encoding="utf-8"))
        previous_url = os.environ.get("MERCHANT_MCP_URL")
        previous_data = os.environ.get("PLATFORM_DATA_DIR")
        os.environ["MERCHANT_MCP_URL"] = "http://127.0.0.1:9/mcp"
        os.environ["MCP_HTTP_TIMEOUT"] = "1"
        isolated = TemporaryDirectory()
        os.environ["PLATFORM_DATA_DIR"] = isolated.name
        try:
            down = self.platform.gateway.call(
                "run-down",
                catalog_contract.permissions,
                catalog_contract.tools,
                "get_product_details",
                {"product_id": "p-jacket-blue"},
                {},
                scope="down",
            )
            self.assertEqual(down["status"], "failed")
            self.assertEqual(down["error_code"], "upstream_unavailable")
            self.assertNotIn("Bearer", str(down))
        finally:
            isolated.cleanup()
            if previous_url is None:
                os.environ.pop("MERCHANT_MCP_URL", None)
            else:
                os.environ["MERCHANT_MCP_URL"] = previous_url
            if previous_data is None:
                os.environ.pop("PLATFORM_DATA_DIR", None)
            else:
                os.environ["PLATFORM_DATA_DIR"] = previous_data
            os.environ.pop("MCP_HTTP_TIMEOUT", None)
        with self.assertRaises(ValueError):
            self.platform.update_contract("catalog-agent", {"tools": ["search_products", "query_sql"]})
        os.environ["SQL_CONNECTION"] = "configured-for-test"
        os.environ["WEB_ALLOWLIST"] = "example.test"
        try:
            sql = self.platform.gateway.call(
                "run-sql",
                {"sql_read": True},
                ["query_sql"],
                "query_sql",
                {"query": "delete from orders"},
                {},
                scope="analysis",
            )
            self.assertEqual(sql["status"], "failed")
            self.assertEqual(sql["result"]["error"], "rejected")
            web = self.platform.gateway.call(
                "run-web",
                {"web_read": True},
                ["fetch_url"],
                "fetch_url",
                {"url": "https://evil.example/secret"},
                {},
                scope="research",
            )
            self.assertEqual(web["result"]["error"], "denied")
        finally:
            os.environ.pop("SQL_CONNECTION", None)
            os.environ.pop("WEB_ALLOWLIST", None)
        self.assertTrue(VectorPort().query("jacket"))
        self.assertEqual(GraphPort().query("jacket"), [])
        self.assertEqual(JobRunner().run_due("workflow-check")["status"], "completed")
        store = CredentialStore()
        store.put("tenant", "catalog-agent", "catalog_read", "scoped")
        self.assertEqual(store.get("tenant", "catalog-agent", "catalog_read"), "scoped")
        copied = usage_from_payload({"model": "mock", "usage": {"total_tokens": 12}, "cost": 0.01})
        self.assertEqual(copied["total_tokens"], 12)
        self.assertEqual(copied["cost"], 0.01)

    def test_observability_is_part_of_the_agent_contract(self):
        catalog = self.platform.contracts["catalog-agent"]
        self.assertEqual(catalog.observability, ["platform_trace", "evaluation"])
        with self.assertRaises(ValueError):
            self.platform.update_contract("catalog-agent", {"observability": ["vendor"]})
        original = Path(catalog.path).read_text(encoding="utf-8")
        try:
            self.platform.connect_observability("otlp", ["catalog-agent"])
            updated = self.platform.contracts["catalog-agent"]
            self.assertEqual(updated.observability, ["platform_trace", "evaluation", "otlp"])
            sinks = {item["id"]: item for item in self.platform.plugins()["observability"]}
            self.assertFalse(sinks["otlp"]["configured"])
            self.assertIn("catalog-agent", sinks["otlp"]["connected_agents"])
            self.assertNotIn("http", sinks["otlp"]["detail"])
        finally:
            Path(catalog.path).write_text(original, encoding="utf-8")
            self.platform.reload()
            self.assertEqual(self.platform.contracts["catalog-agent"].observability, ["platform_trace", "evaluation"])

    def test_rag_is_chosen_on_the_agent(self):
        research = self.platform.contracts["research-agent"]
        catalog = self.platform.contracts["catalog-agent"]
        self.assertTrue(research.rag["retrieve"])
        self.assertFalse(research.rag["capture"])
        self.assertFalse(catalog.rag["retrieve"])
        self.assertEqual(catalog.rag["vector"], "local")
        self.assertEqual(catalog.model["provider"], "platform")
        with self.assertRaises(ValueError):
            self.platform.update_contract("catalog-agent", {"rag": {**catalog.rag, "vector": "pinecone"}})
        original = Path(research.path).read_text(encoding="utf-8")
        try:
            self.platform.connect_rag("vector", "aws", ["research-agent"])
            updated = self.platform.contracts["research-agent"]
            self.assertEqual(updated.rag["vector"], "aws")
            self.assertEqual(self.platform.contracts["catalog-agent"].rag["vector"], "local")
            run = self.platform.start(AgentRequest(task="What does the indexed document say about the jacket?", agents=["research-agent"]))
            self.assertEqual(run["status"], "completed")
            blob = str(run)
            self.assertNotIn("AWS_VECTOR_INDEX", blob)
            self.assertNotIn("http", blob)
        finally:
            Path(research.path).write_text(original, encoding="utf-8")
            self.platform.reload()

    def test_notes_and_ingestion_cadence_round_trip_into_the_agent_file(self):
        research = self.platform.contracts["research-agent"]
        original = Path(research.path).read_text(encoding="utf-8")
        try:
            updated = self.platform.update_contract(
                "research-agent",
                {
                    "memory": {**research.memory, "notes": ["Jacket sizes live in the index.", "  "]},
                    "rag": {**research.rag, "capture": True, "cadence": "daily"},
                },
            )
            self.assertEqual(updated.memory["notes"], ["Jacket sizes live in the index."])
            self.assertEqual(updated.rag["cadence"], "daily")
            text = Path(research.path).read_text(encoding="utf-8")
            self.assertIn("Jacket sizes live in the index.", text)
            self.assertIn("daily", text)
            cleared = self.platform.update_contract("research-agent", {"rag": {**updated.rag, "capture": False, "cadence": "hourly"}})
            self.assertEqual(cleared.rag["cadence"], "off")
        finally:
            Path(research.path).write_text(original, encoding="utf-8")
            self.platform.reload()

    def test_connection_url_is_saved_and_password_stays_hidden(self):
        import os
        from tempfile import TemporaryDirectory

        previous = os.environ.get("PLATFORM_DATA_DIR")
        with TemporaryDirectory() as folder:
            os.environ["PLATFORM_DATA_DIR"] = folder
            try:
                saved = self.platform.save_endpoint(
                    "n8n",
                    "https://n8n.example.test",
                    "n8n://board",
                    "operator",
                    "local-secret",
                )
                self.assertEqual(saved["url"], "https://n8n.example.test")
                self.assertEqual(saved["username"], "operator")
                self.assertTrue(saved["password_set"])
                self.assertNotIn("password", saved)
                self.assertNotIn("local-secret", str(saved))
                listed = {item["id"]: item for item in self.platform.endpoints()}
                self.assertEqual(listed["n8n"]["url"], "https://n8n.example.test")
                self.assertIn("does not host n8n", listed["n8n"]["summary"])
                self.assertEqual(listed["grafana"]["title"], "Grafana")
                kept = self.platform.save_endpoint("n8n", "https://n8n.example.test", "n8n://board", "operator", "")
                self.assertTrue(kept["password_set"])
                self.assertNotIn("local-secret", str(kept))
                from guardrails.connections.mcp_servers import add, public, remove

                onboarded = add("Product server", "product", "https://catalog.example.test/mcp", "client", "mcp-token")
                self.assertEqual(onboarded["purpose"], "product")
                from guardrails.connections.mcp_servers import address

                self.assertEqual(address("product"), "https://catalog.example.test/mcp")
                self.assertTrue(onboarded["password_set"])
                self.assertNotIn("mcp-token", str(onboarded))
                self.assertEqual(len(public()), 1)
                with self.assertRaises(ValueError):
                    add("Broken", "product", "ftp://catalog.example.test", "", "")
                remove(onboarded["id"])
                self.assertEqual(public(), [])
            finally:
                if previous is None:
                    os.environ.pop("PLATFORM_DATA_DIR", None)
                else:
                    os.environ["PLATFORM_DATA_DIR"] = previous


if __name__ == "__main__":
    unittest.main()

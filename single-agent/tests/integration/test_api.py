"""Desk-agent over HTTP.

Purpose: the jacket task returns products and a stock count through the offline harness.
Used by: the single-agent test job.
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from agentic.platform.config import DEV_TOKEN  # noqa: E402
from agentic.platform.loader import load_module  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

app = load_module(ROOT / "agentic" / "01-entry" / "app.py", "single_agent_api").app
HEADERS = {"Authorization": f"Bearer {DEV_TOKEN}"}


def setUpModule():
    load_module(ROOT / "tests" / "merchant_server.py", "single_merchant_api").ensure_merchant_server()


class ApiTests(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    def test_health_requires_the_token(self):
        self.assertEqual(self.client.get("/health").status_code, 401)
        health = self.client.get("/health", headers=HEADERS)
        self.assertEqual(health.status_code, 200)
        self.assertEqual(health.json()["agents"], 1)
        self.assertEqual(health.json()["harness"], "langchain")

    def test_jacket_task(self):
        started = self.client.post(
            "/agent-runs",
            headers=HEADERS,
            json={"task": "Find a blue trail jacket under $150", "session_id": "ses-jacket"},
        )
        self.assertEqual(started.status_code, 200, started.text)
        body = started.json()
        self.assertEqual(body["status"], "completed")
        self.assertEqual(body["harness"], "langchain")
        self.assertTrue(body["result"]["products"])
        self.assertIsInstance(body["result"]["available"], (int, float))
        names = [call["name"] for call in body["tool_calls"]]
        self.assertIn("search_products", names)
        self.assertIn("check_stock", names)
        self.assertTrue(any(event.get("harness") == "langchain" for event in body["trace"]))

    def test_settings_switch_the_harness(self):
        try:
            switched = self.client.put("/settings/harness", headers=HEADERS, json={"harness": "claude"})
            self.assertEqual(switched.status_code, 200, switched.text)
            self.assertEqual(switched.json()["harness"], "claude")
            health = self.client.get("/health", headers=HEADERS)
            self.assertEqual(health.json()["harness"], "claude")
            rejected = self.client.put("/settings/harness", headers=HEADERS, json={"harness": "nope"})
            self.assertEqual(rejected.status_code, 422)
        finally:
            restored = self.client.put("/settings/harness", headers=HEADERS, json={"harness": "langchain"})
            self.assertEqual(restored.status_code, 200)
            self.assertEqual(restored.json()["harness"], "langchain")

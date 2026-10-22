"""HTTP API, including settings and approvals."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from fastapi.testclient import TestClient  # noqa: E402
from shared.config import DEV_TOKEN  # noqa: E402
from shared.loader import load_module  # noqa: E402

app = load_module(ROOT / "apps" / "agent-api" / "app.py", "agent_api_app").app
HEADERS = {"Authorization": f"Bearer {DEV_TOKEN}"}


class ApiTests(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)
        self.headers = HEADERS

    def test_health_agents_and_auth(self):
        self.assertEqual(self.client.get("/health").status_code, 401)
        health = self.client.get("/health", headers=self.headers)
        self.assertEqual(health.status_code, 200)
        self.assertEqual(health.json()["agents"], 8)
        settings = self.client.get("/settings/platform", headers=self.headers).json()
        self.assertIn("mode", settings)
        self.assertFalse(settings["model_api_key_set"])
        self.assertNotIn("MODEL_API_KEY", str(settings))

    def test_run_and_approval(self):
        started = self.client.post(
            "/agent-runs",
            headers=self.headers,
            json={"task": "Place an order for the jacket at $129"},
        ).json()
        self.assertEqual(started["status"], "needs_approval")
        decision = self.client.post(
            f"/approvals/{started['approval_id']}/decision",
            headers=self.headers,
            json={"decision": "approve", "actor": "local-operator"},
        )
        self.assertEqual(decision.status_code, 200)
        self.assertEqual(decision.json()["status"], "completed")

    def test_settings_cannot_grant_a_write(self):
        response = self.client.put(
            "/settings/agents/catalog-agent",
            headers=self.headers,
            json={"tools": ["prepare_order"], "approval": {"required_for": ["prepare_order"]}},
        )
        self.assertEqual(response.status_code, 422)
        current = self.client.get("/settings/agents/catalog-agent", headers=self.headers).json()
        self.assertIn("search_products", current["tools"])

    def test_stream_and_plugins(self):
        with self.client.stream(
            "POST",
            "/agent-runs/stream",
            headers=self.headers,
            json={"task": "Find a blue trail jacket under $150", "agents": ["catalog-agent"]},
        ) as response:
            self.assertEqual(response.status_code, 200)
            body = "".join(response.iter_text())
        self.assertIn("search_products", body)
        self.assertIn('"type": "done"', body)
        plugins = self.client.get("/plugins", headers=self.headers)
        self.assertEqual(plugins.status_code, 200)
        names = [item["name"] for item in plugins.json()["plugins"]]
        self.assertIn("compare_products", names)
        denied = self.client.put("/plugins/prepare_order", headers=self.headers, json={"agents": ["catalog-agent"]})
        self.assertEqual(denied.status_code, 422)
        guide = self.client.get("/guide", headers=self.headers)
        self.assertEqual(guide.status_code, 200)
        self.assertIn("repository", [page["id"] for page in guide.json()])


if __name__ == "__main__":
    unittest.main()

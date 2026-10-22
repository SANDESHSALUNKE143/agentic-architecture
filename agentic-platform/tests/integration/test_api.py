"""API mock startup, health, and a run."""

from __future__ import annotations

import os
import unittest

from shared.config import ROOT
from shared.loader import load_module

from tests.support import make_platform


class ApiTests(unittest.TestCase):
    def setUp(self):
        os.environ["PLATFORM_ENV"] = "development"
        module = load_module(ROOT / "apps" / "agent-api" / "app.py", "platform_agent_api_test")
        from fastapi.testclient import TestClient

        self.platform = make_platform()
        self.client = TestClient(module.create_app(self.platform))
        self.headers = {"Authorization": "Bearer local-dev-token-not-for-production"}

    def test_health_and_mock_run(self):
        health = self.client.get("/health")
        self.assertEqual(health.status_code, 200)
        self.assertEqual(health.json()["status"], "ok")
        denied = self.client.get("/agents")
        self.assertEqual(denied.status_code, 401)
        agents = self.client.get("/agents", headers=self.headers)
        self.assertEqual(agents.status_code, 200)
        self.assertEqual(len(agents.json()["agents"]), 22)
        run = self.client.post(
            "/agent-runs",
            headers=self.headers,
            json={"task": "Find a jacket and check whether it is available"},
        )
        self.assertEqual(run.status_code, 200)
        body = run.json()
        fetched = self.client.get(f"/agent-runs/{body['request_id']}", headers=self.headers)
        self.assertEqual(fetched.json()["status"], "completed")

    def test_cancel_an_in_flight_run(self):
        import asyncio

        import httpx
        from agents.base import finish

        async def slow(step, _observations):
            await asyncio.sleep(2)
            return finish("late")

        self.platform.agents["catalog-agent"].handler = slow

        async def scenario():
            transport = httpx.ASGITransport(app=self.client.app)
            async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
                posted = asyncio.create_task(
                    client.post(
                        "/agent-runs",
                        headers=self.headers,
                        json={"task": "Find a jacket", "agents": ["catalog-agent"]},
                    )
                )
                request_id = ""
                for _ in range(50):
                    if self.platform.store.runs:
                        request_id = next(iter(self.platform.store.runs))
                        break
                    await asyncio.sleep(0.02)
                cancelled = await client.post(
                    f"/agent-runs/{request_id}/cancel", headers=self.headers
                )
                body = await posted
                return cancelled.status_code, body.json()

        code, body = asyncio.run(scenario())
        self.assertEqual(code, 200)
        self.assertEqual(body["errors"][-1]["error_code"], "cancelled")

    def test_production_rejects_the_default_token(self):
        os.environ["PLATFORM_ENV"] = "production"
        try:
            module = load_module(ROOT / "apps" / "agent-api" / "app.py", "platform_agent_api_prod")
            with self.assertRaises(RuntimeError):
                module.create_app(self.platform)
        finally:
            os.environ["PLATFORM_ENV"] = "development"


if __name__ == "__main__":
    unittest.main()

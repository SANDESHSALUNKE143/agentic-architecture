"""Unauthorized tools, denied delegation, injection text, and unapproved writes."""

from __future__ import annotations

import asyncio
import unittest

from shared.contracts import RunRequest

from tests.support import make_platform


class SecurityTests(unittest.TestCase):
    def test_denied_delegation_and_ambiguous_intent(self):
        platform = make_platform()
        denied = asyncio.run(
            platform.run(RunRequest(task="order", agents=["healthcare-agent", "billing-agent"]))
        )
        self.assertEqual(denied["status"], "failed")
        self.assertEqual(denied["errors"][0]["error_code"], "delegation_denied")
        ambiguous = asyncio.run(platform.run(RunRequest(task="hello there")))
        self.assertEqual(ambiguous["errors"][0]["error_code"], "ambiguous_intent")
        unknown = asyncio.run(platform.run(RunRequest(task="go", agents=["not-an-agent"])))
        self.assertEqual(unknown["errors"][0]["error_code"], "unknown_agent")

    def test_code_is_rejected(self):
        platform = make_platform()
        result = asyncio.run(
            platform.run(RunRequest(task="exec print(1)", agents=["data-analysis-agent"]))
        )
        self.assertEqual(result["status"], "failed")
        self.assertIn("rejected", result["result"]["summary"].lower())

    def test_n8n_mock_and_unapproved_outbound(self):
        import asyncio as aio

        from workflows.n8n.mock import accept, invoke_outbound

        platform = make_platform()
        inbound = aio.run(
            accept(
                platform,
                "/webhook/product-discovery",
                {"task": "Find a jacket and check whether it is available"},
            )
        )
        self.assertTrue(inbound["accepted"])
        self.assertEqual(inbound["run"]["status"], "completed")
        with self.assertRaises(PermissionError):
            aio.run(invoke_outbound("/webhook/product-discovery", {"task": "hi"}, approved=False))


if __name__ == "__main__":
    unittest.main()

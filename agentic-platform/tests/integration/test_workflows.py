"""End-to-end runs: two specialists, approval, learning, and RAG examples."""

from __future__ import annotations

import asyncio
import unittest

from examples.scenarios.run_scenario import run_example
from shared.contracts import RunRequest

from tests.support import make_platform


class WorkflowTests(unittest.TestCase):
    def test_product_discovery_uses_two_specialists(self):
        platform = make_platform()
        result = asyncio.run(
            platform.run(RunRequest(task="Find a jacket and check whether it is available"))
        )
        self.assertEqual(result["status"], "completed")
        self.assertEqual(result["agents"], ["shopping-agent", "catalog-agent", "inventory-agent"])
        names = [call["name"] for call in result["tool_calls"]]
        self.assertIn("search_products", names)
        self.assertIn("check_stock", names)
        self.assertIn("memory: short_term", [event["message"] for event in result["trace"]])

    def test_order_is_blocked_until_approval(self):
        platform = make_platform()
        paused = asyncio.run(platform.run(RunRequest(task="Prepare an order for p-jacket-blue")))
        self.assertEqual(paused["status"], "needs_approval")
        self.assertTrue(
            all(call["name"] != "prepare_order" or not call["ok"] for call in paused["tool_calls"])
        )
        resumed = asyncio.run(platform.resume(paused["approval_id"], "approved", "operator"))
        self.assertEqual(resumed["status"], "completed")
        self.assertIn("billing-agent", resumed["agents"])
        self.assertTrue(
            any(call["name"] == "prepare_order" and call["ok"] for call in resumed["tool_calls"])
        )

    def test_rejected_order_is_not_submitted(self):
        platform = make_platform()
        paused = asyncio.run(platform.run(RunRequest(task="Prepare an order for p-jacket-blue")))
        rejected = asyncio.run(platform.resume(paused["approval_id"], "rejected", "operator"))
        self.assertEqual(rejected["status"], "failed")
        self.assertTrue(
            any(event["error_code"] == "approval_rejected" for event in rejected["errors"])
        )

    def test_failed_handoff_keeps_the_error(self):
        result = asyncio.run(run_example(make_platform(), "failed-run"))
        self.assertEqual(result["status"], "failed")
        self.assertTrue(
            any(event["error_code"] == "delegation_denied" for event in result["errors"])
        )
        self.assertTrue(result["trace"])

    def test_learning_examples(self):
        platform = make_platform()
        short = asyncio.run(run_example(platform, "short-term-memory"))
        self.assertTrue(any(event["message"] == "memory: short_term" for event in short["trace"]))
        long = asyncio.run(run_example(platform, "long-term-memory"))
        self.assertTrue(any(event["message"] == "memory: long_term" for event in long["trace"]))
        loop = asyncio.run(run_example(platform, "agent-loop"))
        self.assertGreaterEqual(
            sum(1 for call in loop["tool_calls"] if call["name"] == "search_documents"), 2
        )
        human = asyncio.run(run_example(platform, "human-review"))
        self.assertEqual(human["status"], "completed")
        feedback = asyncio.run(run_example(platform, "feedback"))
        self.assertTrue(feedback["feedback"])
        learned = asyncio.run(run_example(platform, "self-learning"))
        self.assertTrue(learned["learned_from"])
        self.assertEqual(learned["agents"], ["catalog-agent"])
        self.assertNotIn("prepare_order", [call["name"] for call in learned["tool_calls"]])

    def test_rag_examples_cite_real_sources(self):
        platform = make_platform()
        classic = asyncio.run(run_example(platform, "rag-classic"))
        self.assertTrue(any(row["source_id"] == "doc-jackets" for row in classic["citations"]))
        empty = asyncio.run(run_example(platform, "rag-corrective"))
        self.assertIn("does not establish", empty["result"]["summary"])
        graph = asyncio.run(run_example(platform, "rag-graph"))
        self.assertTrue(
            any(row["source_id"].startswith("graph:Jacket:") for row in graph["citations"])
        )
        hybrid = asyncio.run(run_example(platform, "rag-hybrid"))
        self.assertTrue(hybrid["result"]["data"]["hits"])
        multi = asyncio.run(run_example(platform, "rag-multi-hop"))
        self.assertIn("expand_entity", [call["name"] for call in multi["tool_calls"]])


class CombinationTests(unittest.TestCase):
    def test_every_allowlisted_pair(self):
        from shared.config import ROOT
        from shared.loader import load_module

        platform = make_platform()
        pairs = load_module(
            ROOT / "workflows" / "agent-chain" / "combinations.py",
            "platform_combinations_test",
        ).allowlisted_pairs(sorted(platform.agents))
        self.assertGreater(len(pairs), 20)
        for source, target in pairs:
            result = asyncio.run(
                platform.run(RunRequest(task=f"{source} then {target}", agents=[source, target]))
            )
            self.assertIn(result["status"], {"completed", "needs_approval", "failed"})
            self.assertNotEqual(
                result["status"], "failed", msg=f"{source}->{target} {result['result']}"
            )
            self.assertTrue(result["trace"])


if __name__ == "__main__":
    unittest.main()

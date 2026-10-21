"""The sells agent answers an order question from its two tools."""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "examples"))


class SellsAgentTests(unittest.TestCase):
    def test_order_answer_names_status_and_offer(self):
        from sells_agent.action import execute
        from sells_agent.runtime import build

        runner, context, observer = build()
        status, payload = execute(
            runner,
            context,
            observer,
            "What is the status of order 1001, and can I add express shipping?",
        )
        self.assertEqual(status, 200)
        self.assertEqual(payload["tools_used"], ["get_order", "get_offer"])
        self.assertIn("open", payload["answer"])
        self.assertIn("Express shipping is available.", payload["answer"])


if __name__ == "__main__":
    unittest.main()

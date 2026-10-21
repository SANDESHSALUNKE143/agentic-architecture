"""LangChain, LangGraph, and the n8n webhook call the same harness."""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "examples"))


class FrameworkCallerTests(unittest.TestCase):
    def test_three_callers_reach_the_harness(self):
        import asyncio

        import frameworks

        report = asyncio.run(frameworks.demo())
        self.assertEqual(report["langchain"], "governed: Which city is rising?")
        self.assertEqual(report["langgraph"], "governed: Which city is rising?")
        self.assertEqual(report["webhook"], "/webhook/city-brief")
        self.assertTrue(report["n8n"]["accepted"])


if __name__ == "__main__":
    unittest.main()

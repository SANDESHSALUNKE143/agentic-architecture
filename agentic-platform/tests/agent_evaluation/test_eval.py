"""unittest wrapper so discover runs the evaluation cases."""

from __future__ import annotations

import asyncio
import json
import unittest
from pathlib import Path

from shared.contracts import RunRequest

from tests.support import make_platform

CASES = Path(__file__).resolve().parents[1] / "agent-evaluation" / "cases.json"


class EvaluationTests(unittest.TestCase):
    def test_cases(self):
        platform = make_platform()
        for case in json.loads(CASES.read_text(encoding="utf-8")):
            result = asyncio.run(
                platform.run(
                    RunRequest(
                        task=case["task"],
                        workflow=case.get("workflow"),
                        agents=case.get("agents"),
                        context=case.get("context") or {},
                    )
                )
            )
            names = [call["name"] for call in result["tool_calls"]]
            for agent in case.get("expect_agents", []):
                self.assertIn(agent, result["agents"], case["id"])
            for tool in case.get("expect_tools", []):
                self.assertIn(tool, names, case["id"])


if __name__ == "__main__":
    unittest.main()

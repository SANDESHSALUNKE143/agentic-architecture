"""Evaluation runner.

Purpose: start each case in tests/agent-evaluation/cases.json and fail when the expected tool is missing.
Used by: the test command in the README and by CI.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from orchestrator.platform import Platform  # noqa: E402
from shared.contracts import AgentRequest  # noqa: E402


def main() -> int:
    from shared.loader import load_module

    load_module(ROOT / "tests" / "merchant_server.py", "merchant_test_server").ensure_merchant_server()
    platform = Platform()
    cases = json.loads((Path(__file__).parent / "cases.json").read_text(encoding="utf-8"))
    failures = []
    for case in cases:
        run = platform.start(AgentRequest(task=case["task"], workflow=case["workflow"]))
        agent = next(item for item in run["agents"] if item["agent_id"] == case["agent_id"])
        names = [call["name"] for call in agent["tool_calls"]]
        missing = [tool for tool in case["expect_tools"] if tool not in names]
        expected = case.get("expect_status", "completed")
        if run["workflow"] != case["workflow"] or agent["status"] != expected or missing:
            failures.append(f"{case['name']}: status={agent['status']} tools={names} missing={missing}")
    if failures:
        print("\n".join(failures))
        return 1
    print(f"{len(cases)} evaluation cases passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

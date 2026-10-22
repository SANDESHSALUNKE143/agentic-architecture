"""Repeatable evaluation. Exit 1 when a case misses its expected agents or tools.

python agentic-platform/tests/agent-evaluation/run.py
"""

from __future__ import annotations

import asyncio
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT.parent / "src"))

from orchestrator.platform import Platform  # noqa: E402
from shared.contracts import RunRequest  # noqa: E402


def main() -> None:
    cases = json.loads((Path(__file__).parent / "cases.json").read_text(encoding="utf-8"))
    platform = Platform(ROOT / "data" / "evaluation")
    failed = 0
    for case in cases:
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
        ok = all(agent in result["agents"] for agent in case.get("expect_agents", []))
        ok = ok and all(tool in names for tool in case.get("expect_tools", []))
        print(f"{case['id']}: {'pass' if ok else 'fail'} status={result['status']}")
        failed += not ok
    if failed:
        raise SystemExit(f"{failed} evaluation case(s) failed")


if __name__ == "__main__":
    main()

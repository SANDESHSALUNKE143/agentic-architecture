"""LangChain runner. Each agent is a tool. The platform still enforces allowlists.

python -m pip install -e '.[frameworks]'
python agentic-platform/examples/langchain/run.py product-discovery
"""

from __future__ import annotations

import asyncio
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT.parent / "src"))

INSTALL = "python -m pip install -e '.[frameworks]'"


def _require():
    try:
        from langchain_core.tools import tool
    except ImportError as exc:
        raise SystemExit(f"LangChain is not installed. {INSTALL}") from exc
    return tool


async def _run(example_id: str) -> dict:
    tool = _require()
    from examples.scenarios.catalog import EXAMPLES
    from examples.scenarios.run_scenario import run_example
    from orchestrator.platform import Platform

    platform = Platform()

    @tool
    async def governed_agent(task: str) -> str:
        """Run one platform example. Permissions stay in the platform."""
        result = await run_example(platform, example_id if task == example_id else example_id)
        summary = (result.get("result") or result.get("run", {}).get("result") or {}).get(
            "summary", ""
        )
        return summary or result.get("status", "")

    if example_id not in EXAMPLES:
        raise SystemExit(f"Unknown example {example_id}.")
    answer = await governed_agent.ainvoke({"task": example_id})
    ran = await run_example(platform, example_id)
    return {"langchain": answer, "status": ran.get("status") or ran.get("run", {}).get("status")}


def main() -> None:
    example_id = sys.argv[1] if len(sys.argv) > 1 else "product-discovery"
    print(json.dumps(asyncio.run(_run(example_id)), indent=2))


if __name__ == "__main__":
    main()

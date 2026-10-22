"""LangGraph runner. One node calls the platform. A write pauses on needs_approval.

python -m pip install -e '.[frameworks]'
python agentic-platform/examples/langgraph/run.py product-discovery
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
        from langgraph.graph import END, START, StateGraph
    except ImportError as exc:
        raise SystemExit(f"LangGraph is not installed. {INSTALL}") from exc
    return END, START, StateGraph


async def _run(example_id: str) -> dict:
    end, start, graph_cls = _require()
    from typing import TypedDict

    from examples.scenarios.catalog import EXAMPLES
    from examples.scenarios.run_scenario import run_example
    from orchestrator.platform import Platform

    if example_id not in EXAMPLES:
        raise SystemExit(f"Unknown example {example_id}.")
    platform = Platform()

    class State(TypedDict):
        example_id: str
        status: str
        summary: str

    async def agent(state: State) -> dict:
        result = await run_example(platform, state["example_id"])
        payload = result.get("run", result)
        summary = (payload.get("result") or {}).get("summary", "")
        return {"status": payload.get("status", ""), "summary": summary}

    graph = graph_cls(State)
    graph.add_node("agent", agent)
    graph.add_edge(start, "agent")
    graph.add_edge("agent", end)
    app = graph.compile()
    state = await app.ainvoke({"example_id": example_id, "status": "", "summary": ""})
    return {"langgraph": state}


def main() -> None:
    example_id = sys.argv[1] if len(sys.argv) > 1 else "product-discovery"
    print(json.dumps(asyncio.run(_run(example_id)), indent=2))


if __name__ == "__main__":
    main()

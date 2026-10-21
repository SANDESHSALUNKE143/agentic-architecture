"""The reference agent answers from evidence and rejects a skipped sequence."""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "examples"))


def _runner(question_tools):
    from agentic_sdk.contracts import Context
    from agentic_sdk.core.execution.tools import ToolRegistry, ToolSpec
    from agentic_sdk.core.harness.runner import AgentRunner
    from insight_agent.cognition.brain import ScriptedModel
    from insight_agent.cognition.memory import INSTRUCTION, REQUIRED_BEFORE_FINAL
    from insight_agent.communication.observe import TraceObserver
    from insight_agent.host.settings import Bindings

    tools = ToolRegistry()
    schema = {"type": "object"}
    permissions = {
        "query_metrics": "sql:read",
        "search_analyses": "knowledge:read",
        "expand_graph": "graph:read",
        "predict_trend": "model:invoke",
        "fetch_site": "web:read",
    }
    for name, handler in question_tools.items():
        tools.add(ToolSpec(name, name, permissions[name], schema, handler))
    bindings = Bindings()
    observer = TraceObserver()
    runner = AgentRunner(
        ScriptedModel(bindings),
        tools,
        INSTRUCTION,
        observer=observer,
        required_before_final=REQUIRED_BEFORE_FINAL,
    )
    context = Context(
        "example-tenant",
        "insight-agent",
        frozenset({"agent:invoke", *permissions.values()}),
    )
    return runner, context, observer


async def _metrics(ctx, arguments):
    del ctx, arguments
    return {
        "rows": [
            {"city": "Pune", "index_value": 1.4},
            {"city": "Mumbai", "index_value": 1.0},
        ]
    }


async def _analyses(ctx, arguments):
    del ctx, arguments
    return {"hits": [{"id": "analysis-2025q4-pune", "text": "Pune demand was rising.", "score": 1}]}


async def _graph(ctx, arguments):
    del ctx, arguments
    return {"passages": ["Graph note: rising_demand is linked to Pune."]}


async def _trend(ctx, arguments):
    del ctx, arguments
    return {"city": "Pune", "label": "rising", "score": 1.4}


async def _site(ctx, arguments):
    del ctx, arguments
    return {"body": {"summary": "Public note for Pune."}}


class InsightExampleTests(unittest.TestCase):
    def test_perceive_rejects_a_blank_question(self):
        from insight_agent.perception import perceive

        with self.assertRaises(ValueError):
            perceive(b'{"question": "  "}')

    def test_rising_city_returns_the_tools_and_an_answer(self):
        from insight_agent.action import execute

        runner, context, observer = _runner(
            {
                "query_metrics": _metrics,
                "search_analyses": _analyses,
                "expand_graph": _graph,
                "predict_trend": _trend,
                "fetch_site": _site,
            }
        )
        status, payload = execute(
            runner,
            context,
            observer,
            "Which city is rising, and what did the last analysis conclude?",
        )
        self.assertEqual(status, 200)
        self.assertIn("query_metrics", payload["tools_used"])
        self.assertIn("search_analyses", payload["tools_used"])
        self.assertIn("Pune", payload["answer"])
        self.assertIn("rising", payload["answer"])

    def test_skip_evidence_is_rejected(self):
        from insight_agent.action import execute

        runner, context, observer = _runner({})
        status, payload = execute(runner, context, observer, "skip evidence")
        self.assertEqual(status, 422)
        self.assertEqual(payload["detail"], "required evidence tools were not called")


if __name__ == "__main__":
    unittest.main()

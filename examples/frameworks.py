"""
Call the SDK harness from LangChain, LangGraph, and an n8n webhook.

The three callers stay outside the business agents. Insight and sells keep
their own tools. This script shows the shared adapters.

Install the extra, then run from the repository root:

    python -m pip install -e '.[frameworks]'
    python examples/frameworks.py
"""

import asyncio

from agentic_sdk.adapters.orchestration.langchain import as_langchain_tool
from agentic_sdk.adapters.orchestration.langgraph import compile_langgraph
from agentic_sdk.adapters.tools.integrations import n8n_tool
from agentic_sdk.contracts import Context
from agentic_sdk.contracts.orchestration.types import ModelReply
from agentic_sdk.core.execution.tools import ToolRegistry
from agentic_sdk.core.harness.runner import AgentRunner

# ── Callers ───────────────────────────────────────────────────────────


class _Answer:
    """Return the question with a fixed prefix. No external model is called."""

    async def decide(self, instruction, question, observations, tools, max_output_tokens):
        """Speak one final answer so the framework call can finish."""
        return ModelReply({"type": "final", "answer": f"governed: {question}"}, 1, 1)


class _Webhook:
    """Stand in for the n8n production webhook. Records the fixed path."""

    def __init__(self):
        self.calls = []

    async def request(self, method, path, body=None, params=None):
        """Accept one POST to the allowlisted webhook path."""
        self.calls.append({"method": method, "path": path, "body": body})
        return {"accepted": True, "path": path}


def _runner():
    """Build a runner whose only permission is to be invoked."""
    context = Context("example-tenant", "framework-demo", frozenset({"agent:invoke"}))
    runner = AgentRunner(_Answer(), ToolRegistry(), "Answer from the question.")
    return runner, context


async def demo():
    """Run one LangChain call, one LangGraph call, and one approved n8n webhook."""
    runner, context = _runner()
    langchain_tool = as_langchain_tool(runner, context)
    langchain_answer = await langchain_tool.ainvoke({"question": "Which city is rising?"})

    graph = compile_langgraph(runner, context)
    graph_state = await graph.ainvoke({"question": "Which city is rising?"})

    webhook = _Webhook()
    tools = ToolRegistry()
    tools.add(
        n8n_tool(
            "notify_city",
            "Start the city brief workflow.",
            "workflow:invoke",
            {"type": "object", "properties": {"city": {"type": "string"}}},
            webhook,
            "/webhook/city-brief",
        )
    )
    workflow_context = Context(
        "example-tenant",
        "framework-demo",
        frozenset({"workflow:invoke"}),
    )
    workflow = await tools.invoke(
        workflow_context,
        "notify_city",
        {"city": "Pune"},
        frozenset({"notify_city"}),
    )
    return {
        "langchain": langchain_answer,
        "langgraph": graph_state["answer"],
        "n8n": workflow,
        "webhook": webhook.calls[0]["path"],
    }


def main() -> None:
    """Print the three caller results."""
    report = asyncio.run(demo())
    print("langchain:", report["langchain"])
    print("langgraph:", report["langgraph"])
    print("n8n:", report["webhook"], report["n8n"]["accepted"])


if __name__ == "__main__":
    main()

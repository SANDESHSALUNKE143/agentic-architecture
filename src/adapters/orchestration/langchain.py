"""
LangChain tool that calls the SDK harness.

LangChain asks the question. AgentRunner still checks identity, permissions,
quotas, and the tool allowlist. Install the frameworks extra before importing
the LangChain types this module loads on first use.

Usage:
    tool = as_langchain_tool(runner, context)
    answer = await tool.ainvoke({"question": "Which city is rising?"})
"""

# ── Tool ──────────────────────────────────────────────────────────────


def as_langchain_tool(runner, context):
    """Return a LangChain tool whose only action is one governed agent run."""
    from langchain_core.tools import tool

    @tool
    async def governed_agent(question: str) -> str:
        """Ask the governed agent. The SDK harness enforces permissions and quotas."""
        result = await runner.run(context, question)
        return result.answer

    return governed_agent

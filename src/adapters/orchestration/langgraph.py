"""
LangGraph node that calls the SDK harness.

The graph holds the question and the answer. The node does not choose tools
or grant permissions. AgentRunner does. Install the frameworks extra before
importing the graph types this module loads on first use.

Usage:
    app = compile_langgraph(runner, context)
    state = await app.ainvoke({"question": "Which city is rising?"})
"""

# ── Graph ─────────────────────────────────────────────────────────────


def compile_langgraph(runner, context):
    """Compile a one-node graph. The node runs AgentRunner and returns the answer."""
    from typing import TypedDict

    from langgraph.graph import END, START, StateGraph

    class State(TypedDict):
        """Question in, governed answer out."""

        question: str
        answer: str

    async def agent(state: State) -> dict:
        """Run one question through the SDK harness."""
        result = await runner.run(context, state["question"])
        return {"answer": result.answer}

    graph = StateGraph(State)
    graph.add_node("agent", agent)
    graph.add_edge(START, "agent")
    graph.add_edge("agent", END)
    return graph.compile()

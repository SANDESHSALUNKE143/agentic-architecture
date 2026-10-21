"""
Foundation model for the insight agent.

The brain. No external LLM is called. decide() asks the planner for the
next evidence step, then speaks an answer only from those results. The
phrase "skip evidence" returns an answer immediately so the harness can
prove it rejects that path.

A later agent replaces this class with a provider model. The reason loop
stays in the library.

Usage:
    model = ScriptedModel(bindings)
    reply = await model.decide(instruction, question, observations, tools, 1024)
"""

from agentic_sdk.contracts.orchestration.types import ModelReply

from insight_agent.cognition.planning import next_step, skipped

# ── Decision model ────────────────────────────────────────────────────


class ScriptedModel:
    """Follow the evidence plan, then answer from the tool results."""

    def __init__(self, bindings):
        """Read the table, model, and site host from the admin connection settings."""
        self.bindings = bindings

    async def decide(self, instruction, question, observations, tools, max_output_tokens):
        """
        Return the next tool action, or a final answer after the plan.

        Steps:
            1. A skipped question returns a final answer with no tools.
            2. Otherwise return the planner's next tool.
            3. When the plan is complete, join the results into one answer.
        """
        del instruction, tools, max_output_tokens
        if skipped(question):
            return ModelReply({"type": "final", "answer": "too early"}, 1, 1)
        step = next_step(self.bindings, question, observations)
        if step is not None:
            tool, arguments = step
            return ModelReply({"type": "tool", "tool": tool, "arguments": arguments}, 1, 1)
        return ModelReply({"type": "final", "answer": _answer(observations)}, 1, 8)


def _answer(observations) -> str:
    """Join connector results into one answer. The harness already required evidence."""
    by_tool = {item["tool"]: item["result"] for item in observations}
    trend = by_tool["predict_trend"]
    analysis = by_tool["search_analyses"]["hits"][0]["text"]
    graph = by_tool["expand_graph"]["passages"][0]
    site = by_tool["fetch_site"]["body"]["summary"]
    return (
        f"{trend['city']} is {trend['label']} with index {trend['score']}. "
        f"{analysis} {graph} {site}"
    )

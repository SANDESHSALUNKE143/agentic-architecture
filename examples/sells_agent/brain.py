"""
Foundation model for the sells agent.

The brain. Follows the order plan and answers only from those two results.

Usage:
    model = ScriptedModel()
    reply = await model.decide(instruction, question, observations, tools, 1024)
"""

from agentic_sdk.contracts.orchestration.types import ModelReply

from sells_agent.planning import next_step

# ── Decision model ────────────────────────────────────────────────────


class ScriptedModel:
    """Follow the order plan, then answer from the tool results."""

    async def decide(self, instruction, question, observations, tools, max_output_tokens):
        """Return the next tool action, or a final answer after both steps."""
        del instruction, tools, max_output_tokens
        step = next_step(question, observations)
        if step is not None:
            tool, arguments = step
            return ModelReply({"type": "tool", "tool": tool, "arguments": arguments}, 1, 1)
        by_tool = {item["tool"]: item["result"] for item in observations}
        order = by_tool["get_order"]
        offer = by_tool["get_offer"]
        answer = f"Order {order['order_id']} is {order['status']}. {offer['offer']}"
        return ModelReply({"type": "final", "answer": answer}, 1, 8)

"""Order status. A refund pauses for approval and is not executed here."""

from agents.base import Agent, finish

AGENT = Agent(
    id="support-agent",
    display_name="Support",
    description="Look up an order. Refunds wait for a human.",
    instructions="Call get_order_status. For a refund, call request_approval and stop.",
    allowed_tools=("get_order_status", "request_approval"),
    permissions=("order:read", "support:write"),
    approval_policy="refund requires approval",
    sample_task="What is the status of order 1001?",
    read_only=False,
)


async def handle(step, observations):
    order_id = step.previous("order_id") or step.recall("order_id") or "1001"
    status = await step.call_tool("get_order_status", {"order_id": order_id})
    order = status["result"].get("order")
    if "refund" not in step.task.lower():
        summary = (
            f"Order {order_id} is {order['status']}."
            if order
            else f"Order {order_id} was not found."
        )
        return finish(summary, {"order": order, "order_id": order_id})
    pending = {
        "name": "request_approval",
        "arguments": {"action": "refund", "summary": f"Refund order {order_id}"},
    }
    await step.call_tool(pending["name"], pending["arguments"])
    return finish(
        f"Refund for order {order_id} is waiting for approval.",
        {"order": order, "order_id": order_id},
        status="needs_approval",
        pending_tool=pending,
    )


AGENT.handler = handle

"""Draft an order. Submission waits for approval and never leaves this process."""

from agents.base import Agent, finish

AGENT = Agent(
    id="order-agent",
    display_name="Order",
    description="Prepare an order draft. Submit waits for approval.",
    instructions="Call prepare_order. Do not mark the draft submitted.",
    allowed_tools=("prepare_order",),
    permissions=("order:write",),
    approval_policy="submit requires approval",
    sample_task="Prepare an order for p-jacket-blue",
    read_only=False,
)


async def handle(step, observations):
    product_id = step.recall("product_id") or step.previous("product_id") or "p-jacket-blue"
    if "p-" in step.task:
        for token in step.task.split():
            if token.startswith("p-"):
                product_id = token.strip(".,")
    pending = {
        "name": "prepare_order",
        "arguments": {"product_id": product_id, "user_id": step.user_id},
    }
    await step.call_tool(pending["name"], pending["arguments"])
    return finish(
        f"Draft for {product_id} is waiting for approval. Nothing was submitted.",
        {"product_id": product_id},
        status="needs_approval",
        pending_tool=pending,
    )


AGENT.handler = handle

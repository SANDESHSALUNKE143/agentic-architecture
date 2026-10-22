"""Draft a purchase order. Sending it waits for approval."""

from agents.base import Agent, finish

AGENT = Agent(
    id="supplier-agent",
    display_name="Supplier",
    description="Draft a purchase-order response.",
    instructions="Call prepare_purchase_order and stop.",
    allowed_tools=("prepare_purchase_order",),
    permissions=("field:write",),
    approval_policy="sending the purchase order requires approval",
    sample_task="Prepare a purchase order for p-jacket-blue",
    read_only=False,
)


async def handle(step, observations):
    pending = {"name": "prepare_purchase_order", "arguments": {"sku": "p-jacket-blue"}}
    await step.call_tool(pending["name"], pending["arguments"])
    return finish(
        "Purchase order po-1 is waiting for approval. Nothing was sent.",
        {"sku": "p-jacket-blue", "sent": False},
        status="needs_approval",
        pending_tool=pending,
    )


AGENT.handler = handle

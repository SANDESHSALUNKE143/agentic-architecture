"""Compare prices. A purchase pauses for approval."""

from agents.base import Agent, finish

AGENT = Agent(
    id="personal-shopping-agent",
    display_name="Personal shopping",
    description="Compare mock prices. Purchasing waits for approval.",
    instructions="Call compare_prices. A purchase calls prepare_order and stops for approval.",
    allowed_tools=("compare_prices", "prepare_order"),
    permissions=("catalog:read", "order:write"),
    approval_policy="purchase requires approval",
    sample_task="Compare prices for p-jacket-blue",
    read_only=False,
)


async def handle(step, observations):
    product_id = "p-jacket-blue"
    for token in step.task.split():
        if token.startswith("p-"):
            product_id = token.strip(".,")
    compared = await step.call_tool("compare_prices", {"product_id": product_id})
    if "buy" not in step.task.lower() and "purchase" not in step.task.lower():
        return finish(
            f"Compared prices for {product_id}.", {"offers": compared["result"].get("offers", [])}
        )
    pending = {
        "name": "prepare_order",
        "arguments": {"product_id": product_id, "user_id": step.user_id},
    }
    await step.call_tool(pending["name"], pending["arguments"])
    return finish(
        f"Purchase of {product_id} is waiting for approval.",
        {"offers": compared["result"].get("offers", [])},
        status="needs_approval",
        pending_tool=pending,
    )


AGENT.handler = handle

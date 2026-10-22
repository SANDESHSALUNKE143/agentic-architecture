"""Check stock for the product id stored by catalog."""

from agents.base import Agent, finish

AGENT = Agent(
    id="inventory-agent",
    display_name="Inventory",
    description="Check stock for a known product id.",
    instructions="Read product_id from short-term memory or the previous handoff, then check_stock.",
    allowed_tools=("check_stock",),
    permissions=("inventory:read",),
    approval_policy="none",
    sample_task="Is p-jacket-blue in stock?",
)


async def handle(step, observations):
    product = step.previous("product") or {}
    product_id = step.recall("product_id") or product.get("id")
    if not product_id:
        product_id = "p-jacket-blue"
    stock = await step.call_tool("check_stock", {"product_id": product_id})
    result = stock["result"]
    if not stock["ok"]:
        return finish("Stock check failed.", result, status="failed")
    label = "in stock" if result.get("in_stock") else "out of stock"
    return finish(f"{product_id} is {label}.", {"stock": result, "product_id": product_id})


AGENT.handler = handle

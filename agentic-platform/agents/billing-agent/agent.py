"""Discount eligibility from mock rules only."""

from agents.base import Agent, finish

AGENT = Agent(
    id="billing-agent",
    display_name="Billing",
    description="Return eligible discounts from the rule table.",
    instructions="Call get_eligible_discounts. Do not invent an offer.",
    allowed_tools=("get_eligible_discounts",),
    permissions=("billing:read",),
    approval_policy="none",
    sample_task="What discount applies to p-jacket-blue?",
)


async def handle(step, observations):
    product_id = step.recall("product_id") or step.previous("product_id") or "p-jacket-blue"
    product = step.previous("product") or {}
    if product.get("id"):
        product_id = product["id"]
    outcome = await step.call_tool(
        "get_eligible_discounts",
        {"user_id": step.user_id, "product_id": product_id},
    )
    offers = outcome["result"].get("offers", [])
    if offers:
        summary = f"{offers[0]['percent']}% off {product_id} ({offers[0]['reason']})."
    else:
        summary = f"No discount rule matches {product_id}."
    return finish(summary, {"product_id": product_id, "discounts": outcome["result"]})


AGENT.handler = handle

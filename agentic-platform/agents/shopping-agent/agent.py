"""Prepare a product query. The workflow engine calls catalog and inventory next."""

from agents.base import Agent, finish

AGENT = Agent(
    id="shopping-agent",
    display_name="Shopping",
    description="Coordinate product discovery. Does not place an order.",
    instructions="Turn the task into a catalog query. Do not call order tools.",
    allowed_tools=(),
    permissions=(),
    approval_policy="none",
    sample_task="Find a jacket and check whether it is available",
)


async def handle(step, observations):
    query = step.task
    step.remember("query", query)
    return finish(
        "Prepared a catalog query. Inventory runs after catalog.",
        {"query": query, "places_order": False},
    )


AGENT.handler = handle

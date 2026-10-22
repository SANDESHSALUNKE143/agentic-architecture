"""Pick the order id for support and billing."""

from agents.base import Agent, finish

AGENT = Agent(
    id="customer-service-agent",
    display_name="Customer service",
    description="Coordinate support, then billing.",
    instructions="Extract an order id and pass it on. Do not refund.",
    allowed_tools=(),
    permissions=(),
    approval_policy="none",
    sample_task="What is the status of order 1001?",
)


def _order_id(task: str) -> str:
    for token in task.replace("#", " ").split():
        if token.isdigit():
            return token
    return "1001"


async def handle(step, observations):
    order_id = _order_id(step.task)
    step.remember("order_id", order_id)
    return finish(f"Support will look up order {order_id}.", {"order_id": order_id})


AGENT.handler = handle

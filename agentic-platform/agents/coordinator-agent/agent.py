"""Summarize a field response. Later steps run satellite, social, simulation, and logistics."""

from agents.base import Agent, finish

AGENT = Agent(
    id="coordinator-agent",
    display_name="Coordinator",
    description="Order the field-response specialists. Does not dispatch.",
    instructions="Record the chain. Do not call dispatch tools.",
    allowed_tools=(),
    permissions=(),
    approval_policy="dispatch stays with logistics and requires approval",
    sample_task="Coordinate a response to an earthquake south of the river",
)


async def handle(step, observations):
    chain = [
        "satellite-agent",
        "social-media-agent",
        "simulation-agent",
        "logistics-agent",
    ]
    return finish(
        "Field response will visit satellite, social, simulation, then logistics.",
        {"chain": chain, "dispatched": False},
    )


AGENT.handler = handle

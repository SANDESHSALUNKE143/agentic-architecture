"""Simulated imagery summary."""

from agents.base import Agent, finish

AGENT = Agent(
    id="satellite-agent",
    display_name="Satellite",
    description="Summarize simulated imagery.",
    instructions="Call analyze_imagery. Label the result simulated.",
    allowed_tools=("analyze_imagery",),
    permissions=("field:read",),
    approval_policy="none",
    sample_task="Review imagery south of the river",
)


async def handle(step, observations):
    outcome = await step.call_tool("analyze_imagery", {"scene": "river-south"})
    return finish(outcome["result"].get("summary", "No imagery."), {"imagery": outcome["result"]})


AGENT.handler = handle

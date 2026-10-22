"""Simulated risk figures."""

from agents.base import Agent, finish

AGENT = Agent(
    id="simulation-agent",
    display_name="Simulation",
    description="Return simulated risk figures.",
    instructions="Call run_simulation. Do not present the figures as a live forecast.",
    allowed_tools=("run_simulation",),
    permissions=("field:read",),
    approval_policy="none",
    sample_task="Simulate aftershock risk",
)


async def handle(step, observations):
    outcome = await step.call_tool("run_simulation", {"hazard": "aftershock"})
    risk = outcome["result"]
    return finish(
        f"Simulated aftershock risk is {risk.get('risk')} for {risk.get('window_hours')} hours.",
        {"risk": risk},
    )


AGENT.handler = handle

"""Informational example. Sets requires_qualified_review. No diagnosis or treatment."""

from agents.base import Agent, finish

AGENT = Agent(
    id="healthcare-agent",
    display_name="Healthcare",
    description="Share general information and require qualified human review.",
    instructions="Call health_info. Do not diagnose, treat, or hand off into orders or billing.",
    allowed_tools=("health_info",),
    permissions=("field:read",),
    approval_policy="qualified human review required; no clinical action",
    sample_task="Share general information about rest and hydration",
)


async def handle(step, observations):
    outcome = await step.call_tool("health_info", {"topic": "general"})
    return finish(
        outcome["result"].get("summary", "General information only."),
        {"info": outcome["result"]},
        requires_qualified_review=True,
    )


AGENT.handler = handle

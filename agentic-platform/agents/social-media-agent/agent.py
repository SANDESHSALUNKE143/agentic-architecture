"""Search an approved mock feed."""

from agents.base import Agent, finish

AGENT = Agent(
    id="social-media-agent",
    display_name="Social media",
    description="Search the approved mock feed.",
    instructions="Call search_feed. Use only posts marked approved_source.",
    allowed_tools=("search_feed",),
    permissions=("field:read",),
    approval_policy="none",
    sample_task="Search the approved feed for road status",
)


async def handle(step, observations):
    outcome = await step.call_tool("search_feed", {"query": step.task})
    posts = outcome["result"].get("posts", [])
    text = posts[0]["text"] if posts else "No approved posts."
    return finish(text, {"posts": posts})


AGENT.handler = handle

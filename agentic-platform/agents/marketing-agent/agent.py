"""Draft campaign copy. Sending or spend waits for approval."""

from agents.base import Agent, finish

AGENT = Agent(
    id="marketing-agent",
    display_name="Marketing",
    description="Draft campaign copy from a mock segment.",
    instructions="Call draft_campaign. Sending requires request_approval.",
    allowed_tools=("draft_campaign", "request_approval"),
    permissions=("enterprise:read", "support:write"),
    approval_policy="sending or spend requires approval",
    sample_task="Draft a campaign for trail-club",
    read_only=False,
)


async def handle(step, observations):
    draft = await step.call_tool("draft_campaign", {"segment": "trail-club"})
    copy = draft["result"].get("copy", "")
    if "send" not in step.task.lower():
        return finish("Drafted campaign copy. Nothing was sent.", {"copy": copy, "sent": False})
    pending = {
        "name": "request_approval",
        "arguments": {"action": "send_campaign", "summary": "Send trail-club draft"},
    }
    await step.call_tool(pending["name"], pending["arguments"])
    return finish(
        "Sending the campaign is waiting for approval.",
        {"copy": copy, "sent": False},
        status="needs_approval",
        pending_tool=pending,
    )


AGENT.handler = handle

"""Draft a dispatch. Sending it waits for approval."""

from agents.base import Agent, finish

AGENT = Agent(
    id="logistics-agent",
    display_name="Logistics",
    description="Draft a dispatch. Sending waits for approval.",
    instructions="Call prepare_dispatch and stop. Do not send it.",
    allowed_tools=("prepare_dispatch",),
    permissions=("field:write",),
    approval_policy="dispatch requires approval",
    sample_task="Prepare a dispatch to river-south",
    read_only=False,
)


async def handle(step, observations):
    pending = {"name": "prepare_dispatch", "arguments": {"destination": "river-south"}}
    await step.call_tool(pending["name"], pending["arguments"])
    return finish(
        "Dispatch to river-south is waiting for approval. Nothing was sent.",
        {"destination": "river-south", "sent": False},
        status="needs_approval",
        pending_tool=pending,
    )


AGENT.handler = handle

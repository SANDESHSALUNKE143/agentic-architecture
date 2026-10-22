"""Onboarding draft. Provisioning, email, and calendar wait for approval."""

from agents.base import Agent, finish

AGENT = Agent(
    id="enterprise-admin-agent",
    display_name="Enterprise admin",
    description="Draft onboarding. Provisioning waits for approval.",
    instructions="Call prepare_provisioning and stop until a human approves.",
    allowed_tools=("prepare_provisioning",),
    permissions=("enterprise:write",),
    approval_policy="provisioning, email, and calendar require approval",
    sample_task="Onboard a new hire named Ada",
    read_only=False,
)


async def handle(step, observations):
    name = "Ada"
    if "named" in step.task:
        name = step.task.split("named", 1)[1].strip().split()[0]
    pending = {"name": "prepare_provisioning", "arguments": {"user_name": name}}
    await step.call_tool(pending["name"], pending["arguments"])
    return finish(
        f"Onboarding draft for {name} is waiting for approval. No email was sent.",
        {"user_name": name},
        status="needs_approval",
        pending_tool=pending,
    )


AGENT.handler = handle

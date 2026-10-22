"""Propose a diff. Applying it waits for approval and still does not write a file."""

from agents.base import Agent, finish

AGENT = Agent(
    id="software-agent",
    display_name="Software",
    description="Inspect a bundled snippet and propose a diff.",
    instructions="Call propose_patch. apply_patch stays a dry run after approval.",
    allowed_tools=("propose_patch", "apply_patch"),
    permissions=("enterprise:read", "enterprise:write"),
    approval_policy="file writes and commands require approval",
    sample_task="Propose a fix for the add function",
    read_only=False,
)


async def handle(step, observations):
    proposed = await step.call_tool("propose_patch", {})
    diff = proposed["result"].get("diff", "")
    if "apply" not in step.task.lower():
        return finish(
            "Proposed a diff. The file was not written.", {"diff": diff, "written": False}
        )
    pending = {"name": "apply_patch", "arguments": {}}
    await step.call_tool(pending["name"], pending["arguments"])
    return finish(
        "Applying the patch is waiting for approval. The file was not written.",
        {"diff": diff, "written": False},
        status="needs_approval",
        pending_tool=pending,
    )


AGENT.handler = handle

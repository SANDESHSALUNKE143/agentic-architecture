"""Run one catalog example. Framework runners call this and do not reimplement the flow."""

from __future__ import annotations

from examples.scenarios.catalog import EXAMPLES
from shared.contracts import RunRequest
from workflows.n8n.mock import accept as accept_webhook


async def run_example(platform, example_id: str) -> dict:
    spec = EXAMPLES[example_id]
    if spec.get("setup") == "note":
        await _save_note(platform, "I prefer blue jackets")
    if spec.get("setup") == "learn":
        first = await platform.run(
            RunRequest(
                task="Find a jacket and check whether it is available", workflow="product-discovery"
            )
        )
        platform.feedback(
            first["request_id"], "not_helpful", "jacket questions should start at catalog"
        )
    request = RunRequest(
        task=spec["task"],
        workflow=spec.get("workflow"),
        agents=spec.get("agents"),
        context=spec.get("context") or {},
    )
    if spec.get("setup") == "n8n":
        return await accept_webhook(platform, "/webhook/product-discovery", {"task": spec["task"]})
    result = await platform.run(request)
    if spec.get("setup") == "approve" and result.get("approval_id"):
        result = await platform.resume(result["approval_id"], "approved", "operator")
    if spec.get("setup") == "feedback":
        platform.feedback(
            result["request_id"], "not_helpful", "jacket questions should start at catalog"
        )
        result = platform.engine.public_run(platform.store.get(result["request_id"]))
        result["feedback"] = platform.learning.feedback_for_run(result["request_id"])
    return result


async def _save_note(platform, text: str) -> None:
    staged = platform.memory.stage_note(text, "local-development-user")
    approval = platform.store.open_approval(
        run_id="",
        agent_id="memory",
        action="save_note",
        summary=staged["summary"],
        params=staged["params"],
        impact="The note is stored locally after approval.",
    )
    await platform.resume(approval["id"], "approved", "operator")

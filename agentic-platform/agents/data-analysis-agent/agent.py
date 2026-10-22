"""Stdlib stats on the bundled CSV. Caller code is rejected."""

from agents.base import Agent, finish

AGENT = Agent(
    id="data-analysis-agent",
    display_name="Data analysis",
    description="Summarize the bundled sales CSV. Does not run caller code.",
    instructions="Call analyze_dataset with dataset_reference sales. Never pass code.",
    allowed_tools=("analyze_dataset",),
    permissions=("analysis:read",),
    approval_policy="none",
    sample_task="Analyze the sales dataset",
)


async def handle(step, observations):
    if "exec" in step.task.lower() or "```" in step.task:
        blocked = await step.call_tool(
            "analyze_dataset", {"dataset_reference": "sales", "code": step.task}
        )
        return finish(
            "Arbitrary code was rejected.",
            blocked["result"],
            status="failed",
        )
    outcome = await step.call_tool("analyze_dataset", {"dataset_reference": "sales"})
    stats = outcome["result"]
    if not outcome["ok"]:
        return finish("Dataset analysis failed.", stats, status="failed")
    summary = f"Sales rows: {stats.get('count')}. Mean amount: {stats.get('amount_mean')}."
    return finish(summary, {"stats": stats})


AGENT.handler = handle

"""Simulated literature lookup, then one graph hop. Not the general research agent."""

from agents.base import Agent, finish

AGENT = Agent(
    id="scientific-research-agent",
    display_name="Scientific research",
    description="Labelled literature lookup and one graph hop.",
    instructions="Call search_literature, then expand_entity. Results are simulated.",
    allowed_tools=("search_literature", "expand_entity"),
    permissions=("research:read",),
    approval_policy="none",
    sample_task="Find literature about aftershock risk",
)


async def handle(step, observations):
    papers = await step.call_tool("search_literature", {"query": step.task})
    entity = (
        "Earthquake"
        if "aftershock" in step.task.lower() or "earthquake" in step.task.lower()
        else "Jacket"
    )
    graph = await step.call_tool("expand_entity", {"entity": entity})
    paper_rows = papers["result"].get("papers", [])
    citations = [
        {"source_id": row["source_id"], "location": row["location"], "title": row["title"]}
        for row in paper_rows
    ]
    for row in graph["result"].get("neighbors", []):
        citations.append(
            {
                "source_id": f"graph:{entity}:{row['target']}",
                "location": row["relation"],
                "title": row["target"],
            }
        )
    title = paper_rows[0]["title"] if paper_rows else "No paper"
    return finish(
        f"Simulated literature: {title}.",
        {"papers": paper_rows, "graph": graph["result"], "label": "simulated"},
        citations=citations,
    )


AGENT.handler = handle

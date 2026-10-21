"""
Planning for the insight agent.

The strategist. It chooses the next evidence step and does not write the
answer. The foundation model turns that step into a reply.

Usage:
    step = next_step(bindings, question, observations)
"""

# ── Evidence plan ─────────────────────────────────────────────────────

SKIP = "skip evidence"


def skipped(question: str) -> bool:
    """Return whether this question is the path that must not gather evidence."""
    return question.strip() == SKIP


def next_step(bindings, question, observations):
    """
    Return the next tool name and arguments, or None when the plan is complete.

    Steps:
        1. Read the metrics table.
        2. Search past analyses with the question text.
        3. Expand the leading city in the graph.
        4. Score that city with the registered model.
        5. Read the allowlisted public page.
    """
    used = [item["tool"] for item in observations]
    if "query_metrics" not in used:
        return "query_metrics", {"table": bindings.sql_table, "limit": 5}
    if "search_analyses" not in used:
        return "search_analyses", {"query": question, "limit": 2}
    if "expand_graph" not in used:
        return "expand_graph", {"entity": _top_city(observations)}
    if "predict_trend" not in used:
        return "predict_trend", {
            "model_id": bindings.model_id,
            "features": _features(observations),
        }
    if "fetch_site" not in used:
        return "fetch_site", {"host": bindings.web_host, "path": "/cities/pune"}
    return None


def _rows(observations):
    """Return SQL rows from the query_metrics observation."""
    for item in observations:
        if item["tool"] == "query_metrics":
            return item["result"]["rows"]
    return []


def _top_city(observations) -> str:
    """Choose the city with the highest index from the SQL rows."""
    best = max(_rows(observations), key=lambda row: row["index_value"])
    return best["city"]


def _features(observations) -> dict:
    """Build the registered model's feature object from the SQL row."""
    best = max(_rows(observations), key=lambda row: row["index_value"])
    return {"city": best["city"], "index_value": best["index_value"]}

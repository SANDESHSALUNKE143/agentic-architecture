"""
Workflow checks — required tools and structured fields.

An evaluation case can prove the agent followed the path: it called the
tools the task requires, and when the answer is JSON it contains the
fields the task named. The check does not decide whether the answer is
true. A later grader, owned by the business, can do that with its own
expected values.

Usage:
    report = check_workflow(result, required_tools={"query_metrics"}, required_fields=("city",))
"""

from __future__ import annotations

import json

# ── Check ─────────────────────────────────────────────────────────────


def check_workflow(
    result,
    *,
    required_tools: frozenset[str] = frozenset(),
    required_fields: tuple[str, ...] = (),
) -> dict:
    """Return ok, or the missing tools and fields. Do not score factual truth.

    1. Compare the tools the run recorded with the required set.
    2. When fields are required, parse the answer as a JSON object.
    3. Report every missing name. A prose answer fails the field check.
    """
    used = set(getattr(result, "tools_used", ()) or ())
    missing_tools = sorted(required_tools - used)
    missing_fields: list[str] = []
    if required_fields:
        answer = getattr(result, "answer", "")
        try:
            body = json.loads(answer)
        except (ValueError, TypeError):
            body = None
        if not isinstance(body, dict):
            missing_fields = list(required_fields)
        else:
            missing_fields = [name for name in required_fields if name not in body]
    return {
        "ok": not missing_tools and not missing_fields,
        "missing_tools": missing_tools,
        "missing_fields": missing_fields,
    }

"""
Learning for the sells agent.

Records the outcome of one run in this process. Weights are not changed.

Usage:
    note(run_id, tools, "ok", duration_ms)
"""

# ── Outcome ───────────────────────────────────────────────────────────

OUTCOMES = []


def note(run_id: str, tools: list[str], status: str, duration_ms: float) -> None:
    """Keep one content-free outcome. The question and the answer stay out."""
    OUTCOMES.append(
        {"run_id": run_id, "tools": list(tools), "status": status, "duration_ms": duration_ms}
    )

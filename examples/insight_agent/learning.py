"""
Learning for the insight agent.

The feedback loop for this reference. A finished or rejected run is recorded
as status, tool names, and duration. The question and the answer are not
stored, and the foundation model weights are not changed.

Usage:
    note(run_id, tools, "ok", duration_ms)
"""

from insight_agent.host.tracking import record

# ── Outcome ───────────────────────────────────────────────────────────


def note(run_id: str, tools: list[str], status: str, duration_ms: float) -> None:
    """Record one content-free outcome of a run."""
    record(run_id, tools, status, duration_ms)

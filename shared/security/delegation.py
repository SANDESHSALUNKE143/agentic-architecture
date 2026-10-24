"""Which agent may hand work to which other agent.

Purpose: allow read-only hops, and allow only the listed hops that include a write agent.
Used by: orchestrator/planner/planner.py before any tool runs. Edit this file when a new handoff is required.
"""

from __future__ import annotations

READ_AGENTS = {
    "catalog-agent",
    "shopping-agent",
    "support-agent",
    "inventory-agent",
    "billing-agent",
    "data-analysis-agent",
    "research-agent",
}
WRITE_EDGES = {("shopping-agent", "order-agent"), ("order-agent", "billing-agent")}


def can_delegate(source: str, target: str) -> tuple[bool, str]:
    if source == target:
        return False, "An agent cannot hand off to itself."
    if source in READ_AGENTS and target in READ_AGENTS:
        return True, "Read-only hop is allowed."
    if (source, target) in WRITE_EDGES:
        return True, "This write hop is allowlisted."
    return False, f"{source} cannot hand off to {target}."

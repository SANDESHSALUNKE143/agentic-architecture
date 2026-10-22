"""Which agent may hand work to which other agent.

Read-only hops are open between specialists. An agent cannot hand off to itself.
A write hop must be listed. Healthcare cannot hand off into order, billing,
logistics, or enterprise-admin work.
"""

from __future__ import annotations

READ_ONLY_AGENTS = frozenset(
    {
        "catalog-agent",
        "shopping-agent",
        "customer-service-agent",
        "inventory-agent",
        "billing-agent",
        "data-analysis-agent",
        "research-agent",
        "scientific-research-agent",
        "satellite-agent",
        "social-media-agent",
        "simulation-agent",
        "coordinator-agent",
        "healthcare-agent",
    }
)

WRITE_AGENTS = frozenset(
    {
        "support-agent",
        "order-agent",
        "personal-shopping-agent",
        "enterprise-admin-agent",
        "software-agent",
        "marketing-agent",
        "logistics-agent",
        "supplier-agent",
        "agriculture-agent",
    }
)

# Immediate hops that may land on a write agent. The run still pauses for approval.
WRITE_EDGES = frozenset(
    {
        ("customer-service-agent", "support-agent"),
        ("personal-shopping-agent", "order-agent"),
        ("coordinator-agent", "logistics-agent"),
        ("simulation-agent", "logistics-agent"),
    }
)

HEALTHCARE_BLOCKS = frozenset(
    {
        "order-agent",
        "billing-agent",
        "logistics-agent",
        "enterprise-admin-agent",
    }
)

HEALTHCARE_REASONS = {
    "order-agent": "Healthcare cannot hand off into order submission.",
    "billing-agent": "Healthcare cannot hand off into billing.",
    "logistics-agent": "Healthcare cannot hand off into logistics dispatch.",
    "enterprise-admin-agent": "Healthcare cannot hand off into account provisioning.",
}


def is_write_agent(agent_id: str) -> bool:
    return agent_id in WRITE_AGENTS


def can_delegate(source: str, target: str) -> tuple[bool, str]:
    """Return whether source may hand off to target, and a person-readable reason."""
    if source == target:
        return False, f"{source} cannot hand off to itself."
    if source == "healthcare-agent" and target in HEALTHCARE_BLOCKS:
        return False, HEALTHCARE_REASONS[target]
    if target in WRITE_AGENTS:
        if (source, target) in WRITE_EDGES:
            return True, "Write hop is listed and will pause for approval."
        return False, f"{source} cannot hand off into {target} write tools."
    if target in READ_ONLY_AGENTS:
        return True, "Read-only hop is allowed."
    return False, f"{target} is not an allowlisted agent."

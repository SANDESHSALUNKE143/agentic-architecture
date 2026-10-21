"""
Planning for the sells agent.

The strategist. Read the order, then the shipping offer.

Usage:
    step = next_step(question, observations)
"""

# ── Evidence plan ─────────────────────────────────────────────────────


def next_step(question, observations):
    """Return the next tool name and arguments, or None when the plan is complete."""
    del question
    used = [item["tool"] for item in observations]
    if "get_order" not in used:
        return "get_order", {"order_id": "1001"}
    if "get_offer" not in used:
        return "get_offer", {"order_id": "1001"}
    return None

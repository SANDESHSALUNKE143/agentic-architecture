"""Discount rules. Eligibility comes only from this table."""

from __future__ import annotations

RULES = {
    ("local-development-user", "p-jacket-blue"): {"percent": 10, "reason": "trail-club"},
}


async def get_eligible_discounts(ctx, arguments):
    rule = RULES.get((arguments["user_id"], arguments["product_id"]))
    if rule is None:
        return {"eligible": False, "offers": [], "simulated": True}
    return {"eligible": True, "offers": [rule], "simulated": True}

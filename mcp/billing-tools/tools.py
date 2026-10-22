"""One local discount rule. The tool does not invent other offers."""

from __future__ import annotations

RULES = {("local-development-user", "p-jacket-blue"): {"label": "trail-club", "percent": 10}}


def get_eligible_discounts(user_id: str, product_id: str) -> dict:
    offer = RULES.get((user_id, product_id))
    offers = [offer] if offer else []
    explanation = "One local rule matched." if offer else "No discount rule matched."
    return {"product_id": product_id, "offers": offers, "explanation": explanation}

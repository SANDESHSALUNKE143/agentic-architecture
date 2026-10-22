"""Order drafts. prepare_order has no external side effect."""

from __future__ import annotations

ORDERS = {
    "1001": {"order_id": "1001", "status": "open", "item": "p-jacket-blue"},
    "1002": {"order_id": "1002", "status": "shipped", "item": "p-lamp"},
}
_DRAFTS: dict[str, dict] = {}


async def get_order_status(ctx, arguments):
    order = ORDERS.get(str(arguments["order_id"]))
    if order is None:
        return {"order": None, "found": False, "simulated": True}
    return {"order": order, "found": True, "simulated": True}


async def prepare_order(ctx, arguments):
    key = f"{arguments['user_id']}:{arguments['product_id']}"
    draft = _DRAFTS.get(key)
    if draft is None:
        draft = {
            "draft_id": f"draft-{len(_DRAFTS) + 1}",
            "product_id": arguments["product_id"],
            "user_id": arguments["user_id"],
            "submitted": False,
            "simulated": True,
        }
        _DRAFTS[key] = draft
    return {"draft": draft, "simulated": True}

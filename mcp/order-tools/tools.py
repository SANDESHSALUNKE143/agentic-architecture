"""Order status is readable. Preparing an order is simulated and may wait for approval."""

from __future__ import annotations

ORDERS = {
    "1001": {"order_id": "1001", "status": "open", "product_id": "p-jacket-blue"},
    "1002": {"order_id": "1002", "status": "shipped", "product_id": "p-boots"},
}


def get_order_status(order_id: str) -> dict:
    order = ORDERS.get(str(order_id), {"order_id": str(order_id), "status": "unknown", "product_id": ""})
    return {"order_id": order["order_id"], "status": order["status"], "explanation": f"Order {order['order_id']} is {order['status']}."}


def prepare_order(product_id: str, user_id: str, amount: float, approved: bool = False) -> dict:
    return {
        "product_id": product_id,
        "user_id": user_id,
        "amount": amount,
        "submitted": False,
        "simulated": True,
        "explanation": "Order draft is simulated and was not submitted to a merchant.",
        "approved": approved,
    }

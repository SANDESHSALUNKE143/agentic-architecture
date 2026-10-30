"""Order client.

Purpose: ask the orders MCP server for status and a draft. This file holds no orders.
Used by: agentic/05-tools/mcp/tool-gateway/registry.py. The order and support contracts name these tools.
"""

from __future__ import annotations

from agentic.platform.config import ROOT
from agentic.platform.loader import load_module

_client = load_module(ROOT / "agentic" / "05-tools" / "mcp" / "tool-gateway" / "client.py", "merchant_mcp_client")


def get_order_status(order_id: str) -> dict:
    return _client.call_tool("orders", "get_order_status", {"order_id": order_id})


def prepare_order(product_id: str, user_id: str, amount: float, approved: bool = False) -> dict:
    return _client.call_tool(
        "orders",
        "prepare_order",
        {"product_id": product_id, "user_id": user_id, "amount": amount, "approved": approved},
    )


_ORDERS = (
    "mcp/order-tools/tools.py calls the MCP server whose purpose is orders. "
    "Order records live on that server."
)

TOOLS = {
    "get_order_status": {
        "group": "Orders",
        "summary": "Reads whether an order is open or shipped.",
        "source": _ORDERS,
        "permission": "order_read",
        "write": False,
        "mcp_purpose": "orders",
        "fn": get_order_status,
        "schema": {"order_id": "string"},
    },
    "prepare_order": {
        "group": "Orders",
        "summary": "Asks the orders MCP server to store a draft. It does not charge a card.",
        "source": _ORDERS,
        "permission": "order_write",
        "write": True,
        "mcp_purpose": "orders",
        "fn": prepare_order,
        "schema": {"product_id": "string", "user_id": "string", "amount": "number"},
    },
}

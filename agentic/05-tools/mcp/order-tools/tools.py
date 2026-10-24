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

"""Billing client.

Purpose: ask the billing MCP server which discount applies. This file holds no discount rules.
Used by: agentic/05-tools/mcp/tool-gateway/registry.py under get_eligible_discounts. The billing agent contract names that tool.
"""

from __future__ import annotations

from agentic.platform.config import ROOT
from agentic.platform.loader import load_module

_client = load_module(ROOT / "agentic" / "05-tools" / "mcp" / "tool-gateway" / "client.py", "merchant_mcp_client")


def get_eligible_discounts(user_id: str, product_id: str) -> dict:
    return _client.call_tool(
        "billing",
        "get_eligible_discounts",
        {"user_id": user_id, "product_id": product_id},
    )


_BILLING = (
    "mcp/billing-tools/tools.py calls the MCP server whose purpose is billing. "
    "Discount rules live on that server."
)

TOOLS = {
    "get_eligible_discounts": {
        "group": "Billing",
        "summary": "Returns a discount only when the billing MCP server matches a rule.",
        "source": _BILLING,
        "permission": "billing_read",
        "write": False,
        "mcp_purpose": "billing",
        "fn": get_eligible_discounts,
        "schema": {"user_id": "string", "product_id": "string"},
    },
}

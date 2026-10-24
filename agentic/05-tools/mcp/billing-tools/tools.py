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

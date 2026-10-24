"""Catalog client.

Purpose: ask the product MCP server to search, read, compare, and check stock. This file holds no prices.
Used by: mcp/tool-gateway/registry.py. Catalog, shopping, and inventory contracts name these tools.
"""

from __future__ import annotations

from shared.config import ROOT
from shared.loader import load_module

_client = load_module(ROOT / "mcp" / "tool-gateway" / "client.py", "merchant_mcp_client")


def search_products(query: str) -> dict:
    return _client.call_tool("product", "search_products", {"query": query})


def get_product_details(product_id: str) -> dict:
    return _client.call_tool("product", "get_product_details", {"product_id": product_id})


def compare_products(product_ids: list[str]) -> dict:
    return _client.call_tool("product", "compare_products", {"product_ids": product_ids})


def check_stock(product_id: str) -> dict:
    return _client.call_tool("product", "check_stock", {"product_id": product_id})

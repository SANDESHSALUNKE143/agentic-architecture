"""Catalog client.

Purpose: ask the product MCP server to search, read, compare, and check stock. This file holds no prices.
Used by: agentic/05-tools/mcp/tool-gateway/registry.py. Catalog, shopping, and inventory contracts name these tools.
"""

from __future__ import annotations

from agentic.platform.config import ROOT
from agentic.platform.loader import load_module

_client = load_module(ROOT / "agentic" / "05-tools" / "mcp" / "tool-gateway" / "client.py", "merchant_mcp_client")


def search_products(query: str) -> dict:
    return _client.call_tool("product", "search_products", {"query": query})


def get_product_details(product_id: str) -> dict:
    return _client.call_tool("product", "get_product_details", {"product_id": product_id})


def compare_products(product_ids: list[str]) -> dict:
    return _client.call_tool("product", "compare_products", {"product_ids": product_ids})


def check_stock(product_id: str) -> dict:
    return _client.call_tool("product", "check_stock", {"product_id": product_id})


_PRODUCT = (
    "mcp/catalog-tools/tools.py calls the MCP server whose purpose is product. "
    "Prices and stock live on that server. The local stand-in is mocks/merchant."
)

TOOLS = {
    "search_products": {
        "group": "Catalog",
        "summary": "Finds products that match the request.",
        "source": _PRODUCT,
        "permission": "catalog_read",
        "write": False,
        "mcp_purpose": "product",
        "fn": search_products,
        "schema": {"query": "string"},
    },
    "get_product_details": {
        "group": "Catalog",
        "summary": "Reads the price and record for one product.",
        "source": _PRODUCT,
        "permission": "catalog_read",
        "write": False,
        "mcp_purpose": "product",
        "fn": get_product_details,
        "schema": {"product_id": "string"},
    },
    "compare_products": {
        "group": "Catalog",
        "summary": "Compares listed products by price.",
        "source": _PRODUCT,
        "permission": "catalog_read",
        "write": False,
        "mcp_purpose": "product",
        "fn": compare_products,
        "schema": {"product_ids": "array"},
    },
    "check_stock": {
        "group": "Inventory",
        "summary": "Reports how many units are in stock.",
        "source": _PRODUCT,
        "permission": "inventory_read",
        "write": False,
        "mcp_purpose": "product",
        "fn": check_stock,
        "schema": {"product_id": "string"},
    },
}

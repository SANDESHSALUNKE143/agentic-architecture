"""Tool registry.

Purpose: name every plugin, its permission, and the function that answers it.
Used by: mcp/tool-gateway/gateway.py. Add a tool here before a contract names it.
"""

from __future__ import annotations

from typing import Any

from shared.config import ROOT
from shared.loader import load_module

_catalog = load_module(ROOT / "mcp" / "catalog-tools" / "tools.py", "catalog_tools")
_orders = load_module(ROOT / "mcp" / "order-tools" / "tools.py", "order_tools")
_billing = load_module(ROOT / "mcp" / "billing-tools" / "tools.py", "billing_tools")
_support = load_module(ROOT / "mcp" / "support-tools" / "tools.py", "support_tools")
shared_ports = load_module(ROOT / "mcp" / "tool-gateway" / "ports.py", "gateway_ports")

Tool = dict[str, Any]

REGISTRY: dict[str, Tool] = {
    "search_products": {"group": "Catalog", "summary": "Finds products that match the request.", "source": "Local file mcp/catalog-tools/tools.py. The PRODUCTS dictionary in that file holds the name and the price. This tool does not call an API and does not read a website.", "permission": "catalog_read", "write": False, "fn": _catalog.search_products, "schema": {"query": "string"}},
    "get_product_details": {"group": "Catalog", "summary": "Reads the price and record for one product.", "source": "Local file mcp/catalog-tools/tools.py. The price is a number in the PRODUCTS dictionary, such as 129 for the blue trail jacket. No API credential is used.", "permission": "catalog_read", "write": False, "fn": _catalog.get_product_details, "schema": {"product_id": "string"}},
    "compare_products": {"group": "Catalog", "summary": "Compares listed products by price.", "source": "Local file mcp/catalog-tools/tools.py. Prices come from the same PRODUCTS dictionary.", "permission": "catalog_read", "write": False, "fn": _catalog.compare_products, "schema": {"product_ids": "array"}},
    "check_stock": {"group": "Inventory", "summary": "Reports how many units are in stock.", "source": "Local file mcp/catalog-tools/tools.py. Stock is the stock field on PRODUCTS.", "permission": "inventory_read", "write": False, "fn": _catalog.check_stock, "schema": {"product_id": "string"}},
    "get_order_status": {"group": "Orders", "summary": "Reads whether an order is open or shipped.", "permission": "order_read", "write": False, "fn": _orders.get_order_status, "schema": {"order_id": "string"}},
    "prepare_order": {"group": "Orders", "summary": "Prepares a simulated order. It does not submit a purchase.", "permission": "order_write", "write": True, "fn": _orders.prepare_order, "schema": {"product_id": "string", "user_id": "string", "amount": "number"}},
    "get_eligible_discounts": {"group": "Billing", "summary": "Returns a discount only when a local rule matches.", "permission": "billing_read", "write": False, "fn": _billing.get_eligible_discounts, "schema": {"user_id": "string", "product_id": "string"}},
    "request_approval": {"group": "Support", "summary": "Records a refund request and waits for an operator.", "permission": "support_write", "write": True, "fn": _support.request_approval, "schema": {"action": "string", "summary": "string"}},
    "search_documents": {"group": "Research", "summary": "Answers from the local document index.", "permission": "research_read", "write": False, "fn": shared_ports.search_documents, "schema": {"query": "string"}},
    "analyze_dataset": {"group": "Analysis", "summary": "Summarizes the local sales fixture.", "permission": "analysis_read", "write": False, "fn": shared_ports.analyze_dataset, "schema": {"dataset_reference": "string"}},
    "query_sql": {"group": "Connections", "summary": "Runs a read-only SELECT. Writes are rejected.", "permission": "sql_read", "write": False, "endpoint": "sql", "fn": shared_ports.query_sql, "schema": {"query": "string"}},
    "fetch_url": {"group": "Connections", "summary": "Reads a page only when the host is allowlisted.", "permission": "web_read", "write": False, "endpoint": "web", "fn": shared_ports.fetch_url, "schema": {"url": "string"}},
    "invoke_n8n": {"group": "Connections", "summary": "Simulates an n8n call and waits for approval.", "permission": "n8n_write", "write": True, "endpoint": "n8n", "fn": shared_ports.invoke_n8n, "schema": {"path": "string"}},
    "use_mcp_server": {"group": "MCP", "summary": "Records an MCP server address. This process does not call that server.", "permission": "mcp_client", "write": False, "endpoint": "mcp", "fn": shared_ports.use_mcp_server, "schema": {"tool_name": "string"}},
}

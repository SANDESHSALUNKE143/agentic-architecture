"""Tool registry.

Purpose: name every plugin, its permission, and the function that answers it.
Used by: agentic/05-tools/mcp/tool-gateway/gateway.py. Add a tool here before a contract names it.
"""

from __future__ import annotations

from typing import Any

from agentic.platform.config import ROOT
from agentic.platform.loader import load_module

_catalog = load_module(ROOT / "agentic" / "05-tools" / "mcp" / "catalog-tools" / "tools.py", "catalog_tools")
_orders = load_module(ROOT / "agentic" / "05-tools" / "mcp" / "order-tools" / "tools.py", "order_tools")
_billing = load_module(ROOT / "agentic" / "05-tools" / "mcp" / "billing-tools" / "tools.py", "billing_tools")
_support = load_module(ROOT / "agentic" / "05-tools" / "mcp" / "support-tools" / "tools.py", "support_tools")
shared_ports = load_module(ROOT / "agentic" / "05-tools" / "mcp" / "tool-gateway" / "ports.py", "gateway_ports")

Tool = dict[str, Any]
_PRODUCT = "mcp/catalog-tools/tools.py calls the MCP server whose purpose is product. Prices and stock live on that server. The local example is examples/merchant-mcp."
_ORDERS = "mcp/order-tools/tools.py calls the MCP server whose purpose is orders. Order records live on that server."
_BILLING = "mcp/billing-tools/tools.py calls the MCP server whose purpose is billing. Discount rules live on that server."
_SUPPORT = "mcp/support-tools/tools.py calls the MCP server whose purpose is support. The refund decision lives on that server."

REGISTRY: dict[str, Tool] = {
    "search_products": {"group": "Catalog", "summary": "Finds products that match the request.", "source": _PRODUCT, "permission": "catalog_read", "write": False, "mcp_purpose": "product", "fn": _catalog.search_products, "schema": {"query": "string"}},
    "get_product_details": {"group": "Catalog", "summary": "Reads the price and record for one product.", "source": _PRODUCT, "permission": "catalog_read", "write": False, "mcp_purpose": "product", "fn": _catalog.get_product_details, "schema": {"product_id": "string"}},
    "compare_products": {"group": "Catalog", "summary": "Compares listed products by price.", "source": _PRODUCT, "permission": "catalog_read", "write": False, "mcp_purpose": "product", "fn": _catalog.compare_products, "schema": {"product_ids": "array"}},
    "check_stock": {"group": "Inventory", "summary": "Reports how many units are in stock.", "source": _PRODUCT, "permission": "inventory_read", "write": False, "mcp_purpose": "product", "fn": _catalog.check_stock, "schema": {"product_id": "string"}},
    "get_order_status": {"group": "Orders", "summary": "Reads whether an order is open or shipped.", "source": _ORDERS, "permission": "order_read", "write": False, "mcp_purpose": "orders", "fn": _orders.get_order_status, "schema": {"order_id": "string"}},
    "prepare_order": {"group": "Orders", "summary": "Asks the orders MCP server to store a draft. It does not charge a card.", "source": _ORDERS, "permission": "order_write", "write": True, "mcp_purpose": "orders", "fn": _orders.prepare_order, "schema": {"product_id": "string", "user_id": "string", "amount": "number"}},
    "get_eligible_discounts": {"group": "Billing", "summary": "Returns a discount only when the billing MCP server matches a rule.", "source": _BILLING, "permission": "billing_read", "write": False, "mcp_purpose": "billing", "fn": _billing.get_eligible_discounts, "schema": {"user_id": "string", "product_id": "string"}},
    "request_approval": {"group": "Support", "summary": "Sends a refund request to the support MCP server and waits for an operator.", "source": _SUPPORT, "permission": "support_write", "write": True, "mcp_purpose": "support", "fn": _support.request_approval, "schema": {"action": "string", "summary": "string"}},
    "search_documents": {"group": "Research", "summary": "Answers from the local document index.", "permission": "research_read", "write": False, "fn": shared_ports.search_documents, "schema": {"query": "string"}},
    "analyze_dataset": {"group": "Analysis", "summary": "Summarizes the local sales fixture.", "permission": "analysis_read", "write": False, "fn": shared_ports.analyze_dataset, "schema": {"dataset_reference": "string"}},
    "query_sql": {"group": "Connections", "summary": "Runs a read-only SELECT. Writes are rejected.", "permission": "sql_read", "write": False, "endpoint": "sql", "fn": shared_ports.query_sql, "schema": {"query": "string"}},
    "fetch_url": {"group": "Connections", "summary": "Reads a page only when the host is allowlisted.", "permission": "web_read", "write": False, "endpoint": "web", "fn": shared_ports.fetch_url, "schema": {"url": "string"}},
    "invoke_n8n": {"group": "Connections", "summary": "Simulates an n8n call and waits for approval.", "permission": "n8n_write", "write": True, "endpoint": "n8n", "fn": shared_ports.invoke_n8n, "schema": {"path": "string"}},
    "use_mcp_server": {"group": "MCP", "summary": "Lists the tools published by a configured MCP server.", "permission": "mcp_client", "write": False, "endpoint": "mcp", "fn": shared_ports.use_mcp_server, "schema": {"tool_name": "string"}},
}

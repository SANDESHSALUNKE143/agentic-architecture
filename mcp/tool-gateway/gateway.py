"""One registry. Tools run only when the agent contract and permission allow them."""

from __future__ import annotations

import hashlib
import json
from typing import Any, Callable

from shared.config import ROOT
from shared.loader import load_module

_catalog = load_module(ROOT / "mcp" / "catalog-tools" / "tools.py", "catalog_tools")
_orders = load_module(ROOT / "mcp" / "order-tools" / "tools.py", "order_tools")
_billing = load_module(ROOT / "mcp" / "billing-tools" / "tools.py", "billing_tools")
_support = load_module(ROOT / "mcp" / "support-tools" / "tools.py", "support_tools")
shared_ports = load_module(ROOT / "mcp" / "tool-gateway" / "ports.py", "gateway_ports")

Tool = dict[str, Any]

REGISTRY: dict[str, Tool] = {
    "search_products": {"group": "Catalog", "summary": "Finds products that match the request.", "permission": "catalog_read", "write": False, "fn": _catalog.search_products, "schema": {"query": "string"}},
    "get_product_details": {"group": "Catalog", "summary": "Reads the price and record for one product.", "permission": "catalog_read", "write": False, "fn": _catalog.get_product_details, "schema": {"product_id": "string"}},
    "compare_products": {"group": "Catalog", "summary": "Compares listed products by price.", "permission": "catalog_read", "write": False, "fn": _catalog.compare_products, "schema": {"product_ids": "array"}},
    "check_stock": {"group": "Inventory", "summary": "Reports how many units are in stock.", "permission": "inventory_read", "write": False, "fn": _catalog.check_stock, "schema": {"product_id": "string"}},
    "get_order_status": {"group": "Orders", "summary": "Reads whether an order is open or shipped.", "permission": "order_read", "write": False, "fn": _orders.get_order_status, "schema": {"order_id": "string"}},
    "prepare_order": {"group": "Orders", "summary": "Prepares a simulated order. It does not submit a purchase.", "permission": "order_write", "write": True, "fn": _orders.prepare_order, "schema": {"product_id": "string", "user_id": "string", "amount": "number"}},
    "get_eligible_discounts": {"group": "Billing", "summary": "Returns a discount only when a local rule matches.", "permission": "billing_read", "write": False, "fn": _billing.get_eligible_discounts, "schema": {"user_id": "string", "product_id": "string"}},
    "request_approval": {"group": "Support", "summary": "Records a refund request and waits for an operator.", "permission": "support_write", "write": True, "fn": _support.request_approval, "schema": {"action": "string", "summary": "string"}},
    "search_documents": {"group": "Research", "summary": "Answers from the local document index.", "permission": "research_read", "write": False, "fn": shared_ports.search_documents, "schema": {"query": "string"}},
    "analyze_dataset": {"group": "Analysis", "summary": "Summarizes the local sales fixture.", "permission": "analysis_read", "write": False, "fn": shared_ports.analyze_dataset, "schema": {"dataset_reference": "string"}},
    "query_sql": {"group": "Connections", "summary": "Runs a read-only SELECT. Writes are rejected.", "permission": "sql_read", "write": False, "fn": shared_ports.query_sql, "schema": {"query": "string"}},
    "fetch_url": {"group": "Connections", "summary": "Reads a page only when the host is allowlisted.", "permission": "web_read", "write": False, "fn": shared_ports.fetch_url, "schema": {"url": "string"}},
    "invoke_n8n": {"group": "Connections", "summary": "Simulates an n8n call and waits for approval.", "permission": "n8n_write", "write": True, "fn": shared_ports.invoke_n8n, "schema": {"path": "string"}},
}


def digest(arguments: dict) -> str:
    raw = json.dumps(arguments, sort_keys=True, default=str)
    return hashlib.sha256(raw.encode()).hexdigest()[:16]


class ToolGateway:
    def __init__(self) -> None:
        self.seen: dict[str, set[tuple[str, str]]] = {}

    def names(self) -> set[str]:
        return set(REGISTRY)

    def schema_for(self, name: str) -> dict:
        return dict(REGISTRY[name]["schema"])

    def describe(self) -> list[dict]:
        return [
            {
                "name": name,
                "group": spec.get("group", "Other"),
                "summary": spec.get("summary", ""),
                "permission": spec["permission"],
                "write": spec["write"],
                "schema": spec["schema"],
            }
            for name, spec in REGISTRY.items()
        ]

    def call(
        self,
        run_id: str,
        agent_permissions: dict[str, bool],
        allowlist: list[str],
        name: str,
        arguments: dict,
        approval: dict,
        approved: bool = False,
        scope: str = "",
    ) -> dict[str, Any]:
        if name not in allowlist or name not in REGISTRY:
            return {"ok": False, "error_code": "tool_denied", "result": {}, "name": name}
        spec = REGISTRY[name]
        if not agent_permissions.get(spec["permission"], False):
            return {"ok": False, "error_code": "tool_denied", "result": {}, "name": name}
        signature = (name, digest(arguments))
        seen = self.seen.setdefault(f"{run_id}:{scope}", set())
        if signature in seen:
            return {"ok": False, "error_code": "loop_detected", "result": {}, "name": name}
        if spec["write"] and not approved and _needs_approval(name, arguments, approval):
            return {
                "ok": True,
                "status": "needs_approval",
                "name": name,
                "arguments": arguments,
                "result": {"explanation": "Waiting for approval.", "submitted": False},
            }
        seen.add(signature)
        result = _invoke(spec["fn"], arguments, approved)
        status = "failed" if result.get("error") else "completed"
        return {"ok": status == "completed", "status": status, "name": name, "arguments": arguments, "result": result}


def _needs_approval(name: str, arguments: dict, approval: dict) -> bool:
    required = set(approval.get("required_for") or [])
    if name not in required:
        return False
    if "amount_gte" in approval and "amount" in arguments:
        return float(arguments["amount"]) >= float(approval["amount_gte"])
    return True


def _invoke(fn: Callable, arguments: dict, approved: bool) -> dict:
    kwargs = dict(arguments)
    if "approved" in fn.__code__.co_varnames:
        kwargs["approved"] = approved
    return fn(**kwargs)

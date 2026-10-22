"""Allowlisted tool calls. Schemas and permissions are checked in the SDK registry.

Write tools are not invoked until a human approval id is supplied. Agents cannot
widen their own allowlist.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from agentic_sdk.contracts import Context
from agentic_sdk.contracts.orchestration.types import ExecutionError
from agentic_sdk.core.execution.tools import ToolRegistry, ToolSpec
from shared.loader import load_module
from shared.observability.trace import Timer
from shared.security.redact import contains_injection, strip_untrusted

_ROOT = Path(__file__).resolve().parents[2]


def _tools(folder: str, module_name: str):
    """Load a tool module by path so the folder name `mcp` does not shadow the MCP SDK."""
    return load_module(_ROOT / "mcp" / folder / "tools.py", module_name)


catalog_tools = _tools("catalog-tools", "platform_catalog_tools")
order_tools = _tools("order-tools", "platform_order_tools")
billing_tools = _tools("billing-tools", "platform_billing_tools")
support_tools = _tools("support-tools", "platform_support_tools")
research_tools = _tools("research-tools", "platform_research_tools")
analysis_tools = _tools("analysis-tools", "platform_analysis_tools")
enterprise_tools = _tools("enterprise-tools", "platform_enterprise_tools")
field_tools = _tools("field-tools", "platform_field_tools")

_OBJECT = {"type": "object", "additionalProperties": False}


def _schema(properties: dict, required: list[str]) -> dict:
    return {**_OBJECT, "properties": properties, "required": required}


def _string(name: str) -> dict:
    return {name: {"type": "string", "minLength": 1, "maxLength": 400}}


def build_registry() -> ToolRegistry:
    """Register every mock tool once."""
    registry = ToolRegistry()
    specs = [
        (
            "search_products",
            "Search the mock catalog.",
            "catalog:read",
            _schema(_string("query"), ["query"]),
            catalog_tools.search_products,
            True,
        ),
        (
            "get_product_details",
            "Details for one product id.",
            "catalog:read",
            _schema(_string("product_id"), ["product_id"]),
            catalog_tools.get_product_details,
            True,
        ),
        (
            "check_stock",
            "Stock for one product id.",
            "inventory:read",
            _schema(_string("product_id"), ["product_id"]),
            catalog_tools.check_stock,
            True,
        ),
        (
            "compare_prices",
            "Compare mock seller prices.",
            "catalog:read",
            _schema(_string("product_id"), ["product_id"]),
            catalog_tools.compare_prices,
            True,
        ),
        (
            "get_order_status",
            "Status for a mock order.",
            "order:read",
            _schema(_string("order_id"), ["order_id"]),
            order_tools.get_order_status,
            True,
        ),
        (
            "prepare_order",
            "Draft an order. Nothing is submitted.",
            "order:write",
            _schema({**_string("product_id"), **_string("user_id")}, ["product_id", "user_id"]),
            order_tools.prepare_order,
            False,
        ),
        (
            "get_eligible_discounts",
            "Discount eligibility from mock rules.",
            "billing:read",
            _schema({**_string("user_id"), **_string("product_id")}, ["user_id", "product_id"]),
            billing_tools.get_eligible_discounts,
            True,
        ),
        (
            "request_approval",
            "Ask a human to approve an action.",
            "support:write",
            _schema({**_string("action"), **_string("summary")}, ["action", "summary"]),
            support_tools.request_approval,
            False,
        ),
        (
            "search_documents",
            "Retrieve local documents.",
            "research:read",
            _schema({"query": {"type": "string"}, "pattern": {"type": "string"}}, ["query"]),
            research_tools.search_documents,
            True,
        ),
        (
            "expand_entity",
            "One graph hop for a named entity.",
            "research:read",
            _schema(_string("entity"), ["entity"]),
            research_tools.expand_entity,
            True,
        ),
        (
            "search_literature",
            "Simulated literature lookup.",
            "research:read",
            _schema({"query": {"type": "string"}}, []),
            research_tools.search_literature,
            True,
        ),
        (
            "analyze_dataset",
            "Stats for the bundled sales CSV.",
            "analysis:read",
            _schema({"dataset_reference": {"type": "string"}, "code": {"type": "string"}}, []),
            analysis_tools.analyze_dataset,
            True,
        ),
        (
            "prepare_provisioning",
            "Draft an account. No email is sent.",
            "enterprise:write",
            _schema(_string("user_name"), ["user_name"]),
            enterprise_tools.prepare_provisioning,
            False,
        ),
        (
            "draft_campaign",
            "Draft campaign copy. Nothing is sent.",
            "enterprise:read",
            _schema({"segment": {"type": "string"}}, []),
            enterprise_tools.draft_campaign,
            True,
        ),
        (
            "propose_patch",
            "Propose a diff. The file is not written.",
            "enterprise:read",
            _schema({}, []),
            enterprise_tools.propose_patch,
            True,
        ),
        (
            "apply_patch",
            "Dry-run a patch. The file is not written.",
            "enterprise:write",
            _schema({}, []),
            enterprise_tools.apply_patch,
            False,
        ),
        (
            "analyze_imagery",
            "Simulated imagery summary.",
            "field:read",
            _schema({"scene": {"type": "string"}}, []),
            field_tools.analyze_imagery,
            True,
        ),
        (
            "search_feed",
            "Approved-feed search.",
            "field:read",
            _schema({"query": {"type": "string"}}, []),
            field_tools.search_feed,
            True,
        ),
        (
            "run_simulation",
            "Simulated risk figures.",
            "field:read",
            _schema({"hazard": {"type": "string"}}, []),
            field_tools.run_simulation,
            True,
        ),
        (
            "prepare_dispatch",
            "Draft a dispatch. Nothing is sent.",
            "field:write",
            _schema({"destination": {"type": "string"}}, []),
            field_tools.prepare_dispatch,
            False,
        ),
        (
            "prepare_purchase_order",
            "Draft a purchase order. Nothing is sent.",
            "field:write",
            _schema({"sku": {"type": "string"}}, []),
            field_tools.prepare_purchase_order,
            False,
        ),
        (
            "read_sensors",
            "Simulated sensor reading.",
            "field:read",
            _schema({"field": {"type": "string"}}, []),
            field_tools.read_sensors,
            True,
        ),
        (
            "irrigate",
            "Irrigation request. The valve stays closed.",
            "field:write",
            _schema({"field": {"type": "string"}}, []),
            field_tools.irrigate,
            False,
        ),
        (
            "health_info",
            "General health information. Not a diagnosis.",
            "field:read",
            _schema({"topic": {"type": "string"}}, []),
            field_tools.health_info,
            True,
        ),
    ]
    for name, description, permission, schema, handler, read_only in specs:
        registry.add(ToolSpec(name, description, permission, schema, handler, read_only))
    return registry


class Gateway:
    """Call a tool for one agent. The agent's allowlist is checked first."""

    def __init__(self, registry: ToolRegistry | None = None) -> None:
        self.registry = registry or build_registry()

    def describe(self) -> list[dict[str, Any]]:
        rows = []
        for spec in self.registry._tools.values():
            rows.append(
                {
                    "name": spec.name,
                    "description": spec.description,
                    "permission": spec.permission,
                    "read_only": spec.read_only,
                    "input_schema": spec.input_schema,
                }
            )
        return rows

    async def call(
        self,
        *,
        agent_id: str,
        permissions: tuple[str, ...],
        allowed_tools: tuple[str, ...],
        name: str,
        arguments: dict[str, Any],
        trace,
        approved: bool,
    ) -> dict[str, Any]:
        timer = Timer()
        trace.add(
            "tool",
            "started",
            f"{agent_id} called {name}.",
            agent_id=agent_id,
            tool_name=name,
            input_summary=arguments,
        )
        if name not in allowed_tools:
            trace.add(
                "tool",
                "blocked",
                f"{name} is not on the {agent_id} allowlist.",
                agent_id=agent_id,
                tool_name=name,
                error_code="tool_denied",
                duration_ms=timer.elapsed_ms(),
            )
            return {"ok": False, "error_code": "tool_denied", "result": {}}
        spec = self.registry._tools.get(name)
        if spec is None:
            trace.add(
                "tool",
                "failed",
                f"{name} is not a registered tool.",
                agent_id=agent_id,
                tool_name=name,
                error_code="tool_error",
                duration_ms=timer.elapsed_ms(),
            )
            return {"ok": False, "error_code": "tool_error", "result": {}}
        if not spec.read_only and not approved:
            trace.add(
                "tool",
                "needs_approval",
                f"{name} is a write and waits for approval.",
                agent_id=agent_id,
                tool_name=name,
                error_code="approval_required",
                input_summary=arguments,
                duration_ms=timer.elapsed_ms(),
            )
            return {
                "ok": False,
                "error_code": "approval_required",
                "needs_approval": True,
                "tool": name,
                "arguments": arguments,
                "result": {"preview": arguments, "executed": False, "simulated": True},
            }
        ctx = Context("local", agent_id, frozenset(permissions))
        approved_names = frozenset({name}) if approved and not spec.read_only else frozenset()
        try:
            result = await self.registry.invoke(ctx, name, arguments, approved_names)
        except PermissionError:
            trace.add(
                "tool",
                "blocked",
                f"{agent_id} lacks permission for {name}.",
                agent_id=agent_id,
                tool_name=name,
                error_code="tool_denied",
                duration_ms=timer.elapsed_ms(),
            )
            return {"ok": False, "error_code": "tool_denied", "result": {}}
        except ExecutionError as exc:
            code = "schema_invalid" if "schema" in str(exc) else "tool_error"
            trace.add(
                "tool",
                "failed",
                str(exc),
                agent_id=agent_id,
                tool_name=name,
                error_code=code,
                duration_ms=timer.elapsed_ms(),
            )
            return {"ok": False, "error_code": code, "result": {}}
        cleaned = _scrub(result)
        trace.add(
            "tool",
            "ok",
            f"{name} finished.",
            agent_id=agent_id,
            tool_name=name,
            output_summary=cleaned,
            duration_ms=timer.elapsed_ms(),
        )
        return {"ok": True, "error_code": "", "result": cleaned}


def _scrub(value: Any) -> Any:
    if isinstance(value, dict):
        return {key: _scrub(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_scrub(item) for item in value]
    if isinstance(value, str) and contains_injection(value):
        return strip_untrusted(value)
    return value

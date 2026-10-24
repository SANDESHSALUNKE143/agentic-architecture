"""The only plugin caller.

Purpose: run a tool only when the agent contract lists it and the permission is true. Writes in approval.required_for wait.
Used by: agentic/04-loops/runtime/runtime.py and agentic/platform/composition.py. The tool list is registry.py.
"""

from __future__ import annotations

import hashlib
import json
import logging
from typing import Any, Callable

from agentic.platform.config import ROOT
from agentic.platform.loader import load_module

logger = logging.getLogger("agentic.gateway")

_registry = load_module(ROOT / "agentic" / "05-tools" / "mcp" / "tool-gateway" / "registry.py", "tool_registry")
REGISTRY = _registry.REGISTRY



def _endpoint_ready(endpoint: str) -> bool:
    from guardrails.connections.endpoints import ready
    from guardrails.connections.mcp_servers import any_configured

    if endpoint == "mcp":
        return ready(endpoint) or any_configured()
    return ready(endpoint)


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
        from guardrails.connections.endpoints import ENDPOINTS, public
        from guardrails.connections.mcp_servers import saved_for

        hosts = {row["id"]: row for row in public()}
        titles = {spec["id"]: spec["title"] for spec in ENDPOINTS}
        rows = []
        for name, spec in REGISTRY.items():
            endpoint = spec.get("endpoint") or ""
            host = hosts.get(endpoint) or {}
            connection_ready, connection_summary, connection_url = _connection(spec, host, titles)
            purpose = spec.get("mcp_purpose") or ""
            saved = saved_for(purpose) if purpose else None
            rows.append({
                "name": name,
                "group": spec.get("group", "Other"),
                "summary": spec.get("summary", ""),
                "permission": spec["permission"],
                "write": spec["write"],
                "schema": spec["schema"],
                "endpoint": endpoint,
                "mcp_purpose": purpose,
                "mcp_server_id": "" if saved is None else saved["id"],
                "mcp_server_title": "" if saved is None else saved["title"],
                "mcp_password_set": bool(saved and saved["password_set"]),
                "connection_ready": connection_ready,
                "connection_summary": connection_summary,
                "connection_url": connection_url,
                "connection_string": host.get("connection_string") or "",
                "source": spec.get("source") or "",
            })
        return rows

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
        from guardrails.connections.endpoints import ENDPOINTS, public

        hosts = {row["id"]: row for row in public()}
        titles = {item["id"]: item["title"] for item in ENDPOINTS}
        endpoint = spec.get("endpoint") or ""
        ready, summary, _url = _connection(spec, hosts.get(endpoint) or {}, titles)
        if not ready:
            return {
                "ok": False,
                "status": "failed",
                "error_code": "connection_required",
                "name": name,
                "result": {"error": "connection_required", "explanation": summary},
            }
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
        try:
            result = _invoke(spec["fn"], arguments, approved)
        except Exception:
            logger.warning("tool %s failed before it returned a result", name)
            result = {"error": "upstream_unavailable", "explanation": "The tool call failed before it returned a result."}
        if not isinstance(result, dict):
            result = {"error": "upstream_rejected", "explanation": "The tool returned an unexpected result."}
        error = result.get("error")
        outcome = {
            "ok": not error,
            "status": "failed" if error else "completed",
            "name": name,
            "arguments": arguments,
            "result": result,
        }
        if error:
            outcome["error_code"] = str(error)[:80]
        return outcome


def _connection(spec: dict, host: dict, titles: dict) -> tuple[bool, str, str]:
    from guardrails.connections.mcp_servers import address, purpose_ready

    endpoint = spec.get("endpoint") or ""
    purpose = spec.get("mcp_purpose") or ""
    if purpose:
        ready = purpose_ready(purpose)
        url = address(purpose)
        if ready:
            return True, f"Calls the {purpose} MCP server.", url
        return False, f"No MCP server is configured for {purpose}.", ""
    if not endpoint:
        return True, "Runs in this process. No connection string.", ""
    ready = _endpoint_ready(endpoint)
    title = titles.get(endpoint, endpoint)
    url = host.get("url") or ""
    if ready:
        return True, f"{title} is configured.", url
    return False, f"Save the {title} connection before an agent can use this tool.", url


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

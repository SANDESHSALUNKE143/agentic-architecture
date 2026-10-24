"""The only plugin caller.

Purpose: run a tool only when the agent contract lists it and the permission is true. Writes in approval.required_for wait.
Used by: agents/runtime.py and orchestrator/platform.py. The tool list is registry.py.
"""

from __future__ import annotations

import hashlib
import json
from typing import Any, Callable

from shared.config import ROOT
from shared.loader import load_module

_registry = load_module(ROOT / "mcp" / "tool-gateway" / "registry.py", "tool_registry")
REGISTRY = _registry.REGISTRY



def _endpoint_ready(endpoint: str) -> bool:
    from shared.security.endpoints import ready
    from shared.security.mcp_servers import any_configured

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
        from shared.security.endpoints import ENDPOINTS, public

        hosts = {row["id"]: row for row in public()}
        titles = {spec["id"]: spec["title"] for spec in ENDPOINTS}
        rows = []
        for name, spec in REGISTRY.items():
            endpoint = spec.get("endpoint") or ""
            host = hosts.get(endpoint) or {}
            connection_ready = _endpoint_ready(endpoint) if endpoint else True
            title = titles.get(endpoint, endpoint)
            if not endpoint:
                connection_summary = "Runs in this process. No connection string."
            elif connection_ready:
                connection_summary = f"{title} is configured."
            else:
                connection_summary = f"Save the {title} connection before an agent can use this tool."
            rows.append({
                "name": name,
                "group": spec.get("group", "Other"),
                "summary": spec.get("summary", ""),
                "permission": spec["permission"],
                "write": spec["write"],
                "schema": spec["schema"],
                "endpoint": endpoint,
                "connection_ready": connection_ready,
                "connection_summary": connection_summary,
                "connection_url": host.get("url") or "",
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
        endpoint = spec.get("endpoint") or ""
        if endpoint and not _endpoint_ready(endpoint):
                return {
                    "ok": False,
                    "status": "failed",
                    "error_code": "connection_required",
                    "name": name,
                    "result": {"error": "connection_required", "explanation": "Save the connection before this tool can be used."},
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

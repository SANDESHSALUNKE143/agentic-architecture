"""Local stand-in for n8n. It runs the orchestrator. No n8n process is required.

A live POST uses the SDK n8n_tool and only after trusted approval.
"""

from __future__ import annotations

import os
from typing import Any

from agentic_sdk.adapters.tools.integrations import n8n_tool
from agentic_sdk.contracts import Context
from agentic_sdk.core.execution.tools import ToolRegistry
from shared.contracts import RunRequest

PATHS = {
    "/webhook/product-discovery": "product-discovery",
    "/webhook/customer-support": "customer-support",
    "/webhook/order-processing": "order-processing",
    "/webhook/agent-chain": "agent-chain",
}


async def accept(platform, path: str, body: dict[str, Any] | None) -> dict[str, Any]:
    """Inbound webhook. The path is fixed. The body cannot choose a URL."""
    if path not in PATHS:
        raise ValueError("use a fixed production webhook path")
    payload = body or {}
    workflow = PATHS[path]
    agents = payload.get("agents")
    task = payload.get("task") or "Find a jacket and check whether it is available"
    if workflow == "agent-chain" and not agents:
        agents = ["catalog-agent", "inventory-agent"]
    request = RunRequest(
        task=task,
        workflow=None if workflow == "agent-chain" else workflow,
        agents=agents if workflow == "agent-chain" else None,
        context=payload.get("context") or {},
        user_id=payload.get("user_id") or "local-development-user",
    )
    result = await platform.run(request)
    return {"accepted": True, "path": path, "run": result}


class _Transport:
    """Records one POST. Used when N8N_BASE_URL is unset."""

    def __init__(self) -> None:
        self.calls: list[dict[str, Any]] = []

    async def request(self, method, path, body=None, params=None):
        self.calls.append({"method": method, "path": path, "body": body})
        return {"accepted": True, "path": path, "simulated": True}


async def invoke_outbound(path: str, body: dict[str, Any], approved: bool) -> dict[str, Any]:
    """Outbound webhook. Live base URL is used only when N8N_BASE_URL is set."""
    if not path.startswith("/webhook/"):
        raise ValueError("use a fixed production webhook path")
    transport = _Transport()
    if os.environ.get("N8N_BASE_URL"):
        from agentic_sdk.adapters.tools.http import JsonTransport

        transport = JsonTransport(
            os.environ["N8N_BASE_URL"],
            lambda: os.environ.get("N8N_TOKEN", ""),
            allow_loopback_http=True,
        )
    registry = ToolRegistry()
    registry.add(
        n8n_tool(
            "start_workflow",
            "Start a fixed n8n webhook.",
            "workflow:invoke",
            {
                "type": "object",
                "properties": {"task": {"type": "string"}},
                "additionalProperties": True,
            },
            transport,
            path,
        )
    )
    ctx = Context("local", "n8n-outbound", frozenset({"workflow:invoke"}))
    approved_names = frozenset({"start_workflow"}) if approved else frozenset()
    result = await registry.invoke(ctx, "start_workflow", body, approved_names)
    return {"result": result, "path": path}

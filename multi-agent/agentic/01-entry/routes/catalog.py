"""Agent, tool, plugin, RAG, and observability routes.

Purpose: list what is loaded and connect a plugin only when the contract already allows it.
Used by: agentic/01-entry/app.py. The plugins screen and the agent tool tab call these routes.
"""

from __future__ import annotations

from pathlib import Path

from fastapi import Header, HTTPException

from agentic.platform.loader import load_module
from agentic.platform.platform_map import describe_platform

_ENTRY = Path(__file__).resolve().parents[1]
_bodies = load_module(_ENTRY / "bodies.py", "agent_api_bodies")
_auth = load_module(_ENTRY.parent / "02-guardrails" / "auth" / "auth.py", "agent_api_auth")


def mount(app, platform) -> None:
    @app.get("/health", tags=["Health"], summary="Process status")
    def health(authorization: str | None = Header(default=None)):
        _auth.authorized(authorization)
        return platform.health()

    @app.get("/platform", tags=["Platform"], summary="Steps, workflows, security, and edit paths")
    def platform_index(authorization: str | None = Header(default=None)):
        _auth.authorized(authorization)
        return describe_platform()

    @app.get("/agents", tags=["Agents"], summary="Loaded agent contracts")
    def agents(authorization: str | None = Header(default=None)):
        _auth.authorized(authorization)
        return [
            {
                "name": contract.name,
                "description": contract.description,
                "tools": contract.tools,
                "examples": contract.examples,
            }
            for contract in platform.contracts.values()
        ]

    @app.get("/tools", tags=["Agents"], summary="Plugins registered in the gateway")
    def tools(authorization: str | None = Header(default=None)):
        _auth.authorized(authorization)
        return platform.gateway.describe()

    @app.get("/plugins", tags=["Plugins"], summary="Plugins and which agents may call them")
    def plugins(authorization: str | None = Header(default=None)):
        _auth.authorized(authorization)
        return platform.plugins()

    @app.put("/plugins/{name}", tags=["Plugins"], summary="Connect a plugin to agents that may call it")
    def connect_plugin(name: str, body: _bodies.PluginBody, authorization: str | None = Header(default=None)):
        _auth.authorized(authorization)
        try:
            return platform.connect_plugin(name, body.agents)
        except ValueError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc

    @app.put("/settings/rag/{kind}/{choice}", tags=["Plugins"], summary="Set a RAG choice on the named agents")
    def connect_rag(kind: str, choice: str, body: _bodies.PluginBody, authorization: str | None = Header(default=None)):
        _auth.authorized(authorization)
        try:
            return platform.connect_rag(kind, choice, body.agents)
        except ValueError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc

    @app.put("/settings/observability/{sink_id}", tags=["Plugins"], summary="Select an observability sink")
    def connect_observability(sink_id: str, body: _bodies.PluginBody, authorization: str | None = Header(default=None)):
        _auth.authorized(authorization)
        try:
            return platform.connect_observability(sink_id, body.agents)
        except ValueError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc

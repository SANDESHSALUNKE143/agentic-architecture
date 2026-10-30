"""MCP server routes.

Purpose: onboard, update, check, and remove an MCP server. The token is not returned.
Used by: agentic/01-entry/app.py. The tool connection on Plugins calls these routes.
"""

from __future__ import annotations

from pathlib import Path

from fastapi import Header, HTTPException
from guardrails.connections import mcp_servers
from guardrails.connections.mcp_probe import probe

from agentic.platform.loader import load_module

_ENTRY = Path(__file__).resolve().parents[1]
_bodies = load_module(_ENTRY / "bodies.py", "agent_api_bodies")
_auth = load_module(_ENTRY.parent / "02-guardrails" / "auth" / "auth.py", "agent_api_auth")


def mount(app, platform) -> None:
    @app.post("/settings/mcp-servers", tags=["Plugins"], summary="Onboard one MCP server")
    def add_mcp_server(body: _bodies.McpServerBody, authorization: str | None = Header(default=None)):
        _auth.authorized(authorization)
        try:
            return mcp_servers.add(body.title, body.purpose, body.url, body.username, body.password)
        except ValueError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc

    @app.put("/settings/mcp-servers/{server_id}", tags=["Plugins"], summary="Update one onboarded MCP server")
    def save_mcp_server(server_id: str, body: _bodies.McpServerBody, authorization: str | None = Header(default=None)):
        _auth.authorized(authorization)
        try:
            return mcp_servers.update(server_id, body.title, body.purpose, body.url, body.username, body.password)
        except ValueError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc

    @app.post("/settings/mcp-servers/{server_id}/check", tags=["Plugins"], summary="Send MCP initialize to one onboarded server")
    def check_mcp_server(server_id: str, authorization: str | None = Header(default=None)):
        _auth.authorized(authorization)
        try:
            return probe(server_id)
        except ValueError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc

    @app.delete("/settings/mcp-servers/{server_id}", tags=["Plugins"], summary="Remove one onboarded MCP server")
    def delete_mcp_server(server_id: str, authorization: str | None = Header(default=None)):
        _auth.authorized(authorization)
        try:
            mcp_servers.remove(server_id)
        except ValueError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        return {"removed": server_id}

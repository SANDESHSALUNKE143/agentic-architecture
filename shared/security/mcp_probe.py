"""Ask one onboarded MCP server if it answers.

Purpose: run the same initialize handshake the tool client uses, then record the result.
Used by: apps/agent-api/routes_mcp.py. The session call is mcp/tool-gateway/client.py.
"""

from __future__ import annotations

from shared.config import ROOT
from shared.loader import load_module
from shared.security.mcp_servers import _read, _url, record_check

_client = load_module(ROOT / "mcp" / "tool-gateway" / "client.py", "merchant_mcp_client")


def probe(server_id: str) -> dict:
    current = _read()
    item = current.get(server_id)
    if not isinstance(item, dict):
        raise ValueError("Unknown MCP server.")
    url = _url(str(item.get("url") or ""))
    token = str(item.get("password") or "").strip()
    status, detail = _client.ping(url, token)
    return record_check(server_id, status, detail)

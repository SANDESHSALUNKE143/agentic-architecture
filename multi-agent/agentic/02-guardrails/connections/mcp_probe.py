"""Ask one onboarded MCP server if it answers.

Purpose: run the same initialize handshake the tool client uses, then record the result.
Used by: agentic/01-entry/routes/mcp.py. The session call is agentic/05-tools/mcp/tool-gateway/client.py.
"""

from __future__ import annotations

from guardrails.connections.mcp_servers import _read, _url, record_check

from agentic.platform.config import ROOT
from agentic.platform.loader import load_module

_client = load_module(ROOT / "agentic" / "05-tools" / "mcp" / "tool-gateway" / "client.py", "merchant_mcp_client")


def probe(server_id: str) -> dict:
    current = _read()
    item = current.get(server_id)
    if not isinstance(item, dict):
        raise ValueError("Unknown MCP server.")
    url = _url(str(item.get("url") or ""))
    token = str(item.get("password") or "").strip()
    status, detail = _client.ping(url, token)
    return record_check(server_id, status, detail)

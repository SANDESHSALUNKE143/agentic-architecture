"""Ask one onboarded MCP server if it answers.

Purpose: send the MCP initialize call. The address store is mcp_servers.py.
Used by: apps/agent-api/routes_mcp.py.
"""

from __future__ import annotations

import json
import urllib.error
import urllib.request

from shared.security.mcp_servers import _read, _url, record_check


def probe(server_id: str) -> dict:
    current = _read()
    item = current.get(server_id)
    if not isinstance(item, dict):
        raise ValueError("Unknown MCP server.")
    url = _url(str(item.get("url") or ""))
    token = str(item.get("password") or "").strip()
    payload = json.dumps({
        "jsonrpc": "2.0",
        "id": 1,
        "method": "initialize",
        "params": {
            "protocolVersion": "2024-11-05",
            "capabilities": {},
            "clientInfo": {"name": "agentic-architecture", "version": "1.0.0"},
        },
    }).encode()
    headers = {"Content-Type": "application/json", "Accept": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    request = urllib.request.Request(url, data=payload, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(request, timeout=3) as response:
            response.read(400)
        status, detail = "ok", "The server answered. Sample product prices still come from the local catalog file."
    except (urllib.error.URLError, TimeoutError, OSError):
        status, detail = "failed", "Address saved. The server did not answer the MCP initialize call."
    return record_check(server_id, status, detail)

"""Support client.

Purpose: send a refund request to the support MCP server. This file does not decide the refund.
Used by: agentic/05-tools/mcp/tool-gateway/registry.py under request_approval. The support contract names that tool.
"""

from __future__ import annotations

from agentic.platform.config import ROOT
from agentic.platform.loader import load_module

_client = load_module(ROOT / "agentic" / "05-tools" / "mcp" / "tool-gateway" / "client.py", "merchant_mcp_client")


def request_approval(action: str, summary: str, approved: bool = False) -> dict:
    return _client.call_tool(
        "support",
        "request_approval",
        {"action": action, "summary": summary, "approved": approved},
    )

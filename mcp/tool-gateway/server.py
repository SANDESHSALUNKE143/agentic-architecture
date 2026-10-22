"""MCP stdio server. Import the installed mcp package before this repo is on the path."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def build_server():
    sys.path[:] = [item for item in sys.path if Path(item).resolve() != ROOT]
    try:
        from mcp.server.fastmcp import FastMCP
    except ModuleNotFoundError:
        from mcp.server.mcpserver import MCPServer as FastMCP
    sys.path.insert(0, str(ROOT))
    from shared.loader import load_module

    gateway = load_module(ROOT / "mcp" / "tool-gateway" / "gateway.py", "tool_gateway_registry")
    server = FastMCP("agentic-tool-gateway")
    for name, spec in gateway.REGISTRY.items():
        server.tool(name=name)(spec["fn"])
    return server


def main() -> None:
    build_server().run("stdio")


if __name__ == "__main__":
    main()

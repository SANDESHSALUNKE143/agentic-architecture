"""stdio MCP server for the read-only demo tools.

The REST API is not this server. If the mcp package is missing, the process
exits with the install command and does not pretend to speak MCP.
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

READ_ONLY = (
    "search_products",
    "get_product_details",
    "check_stock",
    "get_order_status",
    "get_eligible_discounts",
    "search_documents",
    "analyze_dataset",
)

INSTALL = "python -m pip install 'mcp'"


def build_server():
    """Register the read-only tools. main() is what starts stdio."""
    blocked = {ROOT.resolve(), Path.cwd().resolve()}
    sys.path[:] = [entry for entry in sys.path if Path(entry or ".").resolve() not in blocked]
    try:
        from mcp.server.fastmcp import FastMCP as Server
    except ImportError:
        try:
            from mcp.server.mcpserver import MCPServer as Server
        except ImportError:
            raise SystemExit(
                "Native MCP is not installed. "
                f"{INSTALL}. The tool gateway still enforces schemas over the HTTP API."
            )
    sys.path.insert(0, str(ROOT))
    sys.path.insert(0, str(ROOT.parent / "src"))
    from shared.loader import load_module

    gateway_module = load_module(
        ROOT / "mcp" / "tool-gateway" / "gateway.py", "platform_tool_gateway_mcp"
    )
    gateway = gateway_module.Gateway()
    server = Server("agentic-platform")
    specs = {
        row["name"]: row
        for row in gateway.describe()
        if row["name"] in READ_ONLY and row["read_only"]
    }

    @server.tool()
    async def search_products(query: str) -> dict:
        """Search the mock catalog."""
        return await _call(gateway, "search_products", {"query": query}, specs)

    @server.tool()
    async def get_product_details(product_id: str) -> dict:
        """Details for one mock product."""
        return await _call(gateway, "get_product_details", {"product_id": product_id}, specs)

    @server.tool()
    async def check_stock(product_id: str) -> dict:
        """Stock for one mock product."""
        return await _call(gateway, "check_stock", {"product_id": product_id}, specs)

    @server.tool()
    async def get_order_status(order_id: str) -> dict:
        """Status for a mock order."""
        return await _call(gateway, "get_order_status", {"order_id": order_id}, specs)

    @server.tool()
    async def get_eligible_discounts(user_id: str, product_id: str) -> dict:
        """Discount eligibility from mock rules."""
        return await _call(
            gateway,
            "get_eligible_discounts",
            {"user_id": user_id, "product_id": product_id},
            specs,
        )

    @server.tool()
    async def search_documents(query: str) -> dict:
        """Retrieve local documents."""
        return await _call(
            gateway, "search_documents", {"query": query, "pattern": "classic"}, specs
        )

    @server.tool()
    async def analyze_dataset(dataset_reference: str = "sales") -> dict:
        """Stats for the bundled sales CSV."""
        return await _call(
            gateway, "analyze_dataset", {"dataset_reference": dataset_reference}, specs
        )

    return server


def main() -> None:
    # The local mcp/ folder must not shadow the installed MCP SDK.
    build_server().run()


async def _call(gateway, name: str, arguments: dict, specs: dict) -> dict:
    spec = specs[name]
    from shared.observability.trace import TraceLog

    outcome = await gateway.call(
        agent_id="mcp-server",
        permissions=(spec["permission"],),
        allowed_tools=tuple(specs),
        name=name,
        arguments=arguments,
        trace=TraceLog("mcp"),
        approved=False,
    )
    return outcome["result"]


if __name__ == "__main__":
    main()

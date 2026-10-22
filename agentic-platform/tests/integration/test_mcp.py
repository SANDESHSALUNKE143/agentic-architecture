"""In-process MCP client handshake against the read-only stdio server."""

from __future__ import annotations

import asyncio
import importlib.util
import unittest

from tests.support import ROOT


def _server_module():
    path = ROOT / "mcp" / "tool-gateway" / "server.py"
    spec = importlib.util.spec_from_file_location("platform_mcp_stdio_server", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class McpHandshakeTests(unittest.TestCase):
    def test_client_lists_the_read_only_tools(self):
        module = _server_module()
        try:
            server = module.build_server()
        except SystemExit as exc:
            self.skipTest(str(exc))
        from mcp import Client

        async def listed():
            async with Client(server) as client:
                result = await client.list_tools()
                return sorted(tool.name for tool in result.tools)

        names = asyncio.run(listed())
        self.assertIn("search_products", names)
        self.assertIn("analyze_dataset", names)
        self.assertEqual(len(names), 7)

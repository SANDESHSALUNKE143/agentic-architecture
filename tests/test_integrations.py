import asyncio
import unittest
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock

from agentic_sdk.adapters.anthropic import AnthropicLLM
from agentic_sdk.adapters.integrations import mcp_tool, n8n_tool
from agentic_sdk.contracts import Context

from agentic_sdk.execution import ToolRegistry


class IntegrationAdapterTests(unittest.TestCase):
    def test_anthropic_maps_usage_including_cached_input(self):
        client = Mock()
        client.post.return_value.json.return_value = {
            "content": [{"type": "text", "text": "answer"}],
            "usage": {
                "input_tokens": 4,
                "output_tokens": 2,
                "cache_read_input_tokens": 3,
            },
        }
        answer = AnthropicLLM(client, "approved-model").complete("question", 100)
        self.assertEqual(answer.input_tokens, 7)
        self.assertEqual(answer.text, "answer")
        self.assertEqual(client.post.call_args.kwargs["json"]["max_tokens"], 100)

    def test_n8n_requires_trusted_mutation_approval(self):
        transport = SimpleNamespace(request=AsyncMock(return_value={"ok": True}))
        registry = ToolRegistry()
        registry.add(
            n8n_tool(
                "workflow",
                "Workflow",
                "workflow:invoke",
                {"type": "object"},
                transport,
                "/webhook/approved",
            )
        )
        ctx = Context("tenant", "agent", frozenset({"workflow:invoke"}))
        with self.assertRaises(PermissionError):
            asyncio.run(registry.invoke(ctx, "workflow", {}, frozenset()))
        transport.request.assert_not_called()
        self.assertTrue(
            asyncio.run(registry.invoke(ctx, "workflow", {}, frozenset({"workflow"})))["ok"]
        )

    def test_mcp_allowed_tool_and_error_mapping(self):
        session = SimpleNamespace(
            call_tool=AsyncMock(
                return_value=SimpleNamespace(isError=False, structuredContent={"answer": 42})
            )
        )
        tool = mcp_tool("read", "Read", "read", {"type": "object"}, session, read_only=True)
        ctx = Context("t", "a", frozenset({"read"}))
        self.assertEqual(asyncio.run(tool.handler(ctx, {})), {"answer": 42})
        session.call_tool.return_value.isError = True
        with self.assertRaises(RuntimeError):
            asyncio.run(tool.handler(ctx, {}))

"""Claude Agent SDK harness.

Purpose: query() with gateway tools only. Shell and filesystem tools stay off.
Used by: agentic/03-harness/runtime.py when the contract says claude.
"""

from __future__ import annotations

import asyncio
import json
import os
from typing import Any

from harness.base import HarnessResult


def run(instructions: list[str], messages: list[dict], call_tool, specs: list[tuple[str, dict]]) -> HarnessResult:
    if not os.environ.get("ANTHROPIC_API_KEY", "").strip():
        return HarnessResult(error="harness_unavailable")
    try:
        from claude_agent_sdk import ClaudeAgentOptions, create_sdk_mcp_server, query, tool
    except ImportError:
        return HarnessResult(error="harness_unavailable")
    prompt = messages[-1]["content"] if messages else ""
    try:
        server = _server(create_sdk_mcp_server, tool, call_tool, specs)
        options = ClaudeAgentOptions(
            system_prompt="\n".join(instructions),
            mcp_servers={"gateway": server},
            allowed_tools=[f"mcp__gateway__{name}" for name, _schema in specs],
        )
        reply = asyncio.run(_collect(query, prompt, options))
    except Exception:
        return HarnessResult(error="harness_unavailable")
    return HarnessResult(reply=reply)


def _server(create_sdk_mcp_server, tool, call_tool, specs: list[tuple[str, dict]]):
    tools = [_wrap(tool, call_tool, name, schema) for name, schema in specs]
    return create_sdk_mcp_server(name="gateway", tools=tools)


def _wrap(tool, call_tool, name: str, schema: dict):
    shape = {key: str for key in schema}

    @tool(name, name, shape)
    async def invoke(args: dict[str, Any]) -> dict:
        outcome = call_tool(name, args or {})
        return {"content": [{"type": "text", "text": json.dumps(outcome, default=str)}]}

    return invoke


async def _collect(query, prompt: str, options) -> str:
    reply = ""
    async for message in query(prompt=prompt, options=options):
        content = getattr(message, "content", "")
        if isinstance(content, str) and content.strip():
            reply = content.strip()
        result = getattr(message, "result", None)
        if isinstance(result, str) and result.strip():
            reply = result.strip()
    return reply

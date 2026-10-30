"""Offline and live LangChain loop.

Purpose: create_agent with the gateway tools. No key uses the mock model.
Used by: agentic/03-harness/runtime.py when the contract says langchain.
"""

from __future__ import annotations

from typing import Any

from harness.base import HarnessResult
from langchain.agents import create_agent


def run(model, tools, instructions: list[str], messages: list[dict]) -> HarnessResult:
    agent = create_agent(model, tools, system_prompt="\n".join(instructions))
    outcome = agent.invoke({"messages": messages})
    return HarnessResult(reply=_reply(outcome))


def _reply(outcome: Any) -> str:
    messages = outcome.get("messages") if isinstance(outcome, dict) else []
    for message in reversed(list(messages or [])):
        content = getattr(message, "content", "")
        if isinstance(content, str) and content.strip():
            return content.strip()
    return ""

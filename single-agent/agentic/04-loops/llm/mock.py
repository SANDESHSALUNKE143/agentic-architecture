"""Deterministic chat model.

Purpose: call each allowlisted tool once, then build the JSON result. The same loop runs when a live model is configured.
Used by: agentic/04-loops/llm when PLATFORM_LLM_MODE is mock.
"""

from __future__ import annotations

import json
import re
from typing import Any

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import AIMessage, BaseMessage, ToolMessage
from langchain_core.outputs import ChatGeneration, ChatResult
from pydantic import ConfigDict


def _text(messages: list[BaseMessage]) -> str:
    parts = []
    for message in messages:
        content = getattr(message, "content", "")
        if isinstance(content, str):
            parts.append(content)
    return "\n".join(parts)


def _user_text(messages: list[BaseMessage]) -> str:
    for message in reversed(messages):
        if getattr(message, "type", "") == "human":
            content = message.content
            return content if isinstance(content, str) else _text(messages)
    return _text(messages)


def _tool_name(tool: Any) -> str:
    return getattr(tool, "name", None) or tool.get("name") or ""


def _wanted(tools: list[Any], task: str) -> list[str]:
    names = []
    for tool in tools:
        name = _tool_name(tool)
        if name:
            names.append(name)
    writes = {"prepare_order", "request_approval", "invoke_n8n"}
    lowered = task.lower()
    wants_write = any(word in lowered for word in ("refund", "checkout", "place an order", "prepare an order", "buy "))
    chosen = [name for name in names if name not in writes or wants_write]
    return chosen or names


def tool_arguments(name: str, task: str, tool: Any = None) -> dict[str, Any]:
    product = "p-jacket-blue"
    if "boot" in task.lower():
        product = "p-boots"
    elif "lamp" in task.lower():
        product = "p-lamp"
    amount_match = re.search(r"\$(\d+(?:\.\d+)?)", task)
    amount = float(amount_match.group(1)) if amount_match else 129.0
    order_match = re.search(r"\b(1001|1002)\b", task)
    order_id = order_match.group(1) if order_match else "1001"
    user = "local-development-user"
    mapping = {
        "search_products": {"query": task[:180]},
        "get_product_details": {"product_id": product},
        "compare_products": {"product_ids": ["p-jacket-blue", "p-boots"]},
        "check_stock": {"product_id": product},
        "get_order_status": {"order_id": order_id},
        "prepare_order": {"product_id": product, "user_id": user, "amount": amount},
        "get_eligible_discounts": {"user_id": user, "product_id": product},
        "request_approval": {"action": "refund", "summary": task[:180]},
        "search_documents": {"query": task[:180]},
        "analyze_dataset": {"dataset_reference": "sales", "code": task[:180]},
        "query_sql": {"query": task if "select" in task.lower() else "select 1"},
        "fetch_url": {"url": "https://example.test/catalog"},
        "invoke_n8n": {"path": "/webhook/product-discovery"},
    }
    if name in mapping:
        return dict(mapping[name])
    return _from_tool(tool, task)


def _from_tool(tool: Any, task: str) -> dict[str, Any]:
    model = getattr(tool, "args_schema", None)
    fields = getattr(model, "model_fields", None) or {}
    if not fields:
        return {"query": task[:180]}
    return {key: _sample(getattr(field, "annotation", str), task) for key, field in fields.items()}


def _sample(annotation: Any, task: str) -> Any:
    label = str(annotation).lower()
    if "list" in label:
        return []
    if "dict" in label:
        return {}
    if "bool" in label:
        return False
    if "int" in label or "float" in label:
        return 0
    return task[:180]


class MockChatModel(BaseChatModel):
    """Calls each allowlisted tool once, then returns a JSON object built from observations."""

    model_config = ConfigDict(arbitrary_types_allowed=True)
    bound_tools: list[Any] = []

    @property
    def _llm_type(self) -> str:
        return "mock-chat"

    def bind_tools(self, tools, **kwargs):
        clone = self.model_copy()
        clone.bound_tools = list(tools)
        return clone

    def _generate(self, messages: list[BaseMessage], stop=None, run_manager=None, **kwargs) -> ChatResult:
        done = [message for message in messages if isinstance(message, ToolMessage)]
        done_names = {message.name for message in done}
        task = _user_text(messages)
        bound = {_tool_name(item): item for item in self.bound_tools}
        pending = [name for name in _wanted(self.bound_tools, task) if name not in done_names]
        if pending and len(done) < 4:
            name = pending[0]
            message = AIMessage(
                content="",
                tool_calls=[{
                    "name": name,
                    "args": tool_arguments(name, task, bound.get(name)),
                    "id": f"call-{name}",
                }],
            )
            return ChatResult(generations=[ChatGeneration(message=message)])
        payload = {"explanation": "Completed from tool observations.", "answer": "Completed from tool observations."}
        message = AIMessage(content=json.dumps(payload))
        return ChatResult(generations=[ChatGeneration(message=message)])

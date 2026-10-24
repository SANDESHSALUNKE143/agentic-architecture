"""Choose the chat model.

Purpose: mock mode needs no key. Live mode calls an OpenAI-compatible host when MODEL_API_KEY is set.
Used by: agents/runtime.py.
"""

from __future__ import annotations

import json
import os
import urllib.request
from typing import Any

from shared.config import llm_mode


def usage_from_payload(payload: dict[str, Any]) -> dict[str, Any]:
    usage = payload.get("usage") or {}
    copied: dict[str, Any] = {}
    if payload.get("model"):
        copied["model"] = payload["model"]
    if usage.get("total_tokens") is not None:
        copied["total_tokens"] = usage["total_tokens"]
    if payload.get("cost") is not None:
        copied["cost"] = payload["cost"]
    return copied


class LiveChat:
    """OpenAI-compatible chat. Used only when MODEL_API_KEY is set and mode is live."""

    def __init__(self) -> None:
        self.api_key = os.environ.get("MODEL_API_KEY", "")
        self.base_url = os.environ.get("MODEL_BASE_URL", "https://api.openai.com/v1").rstrip("/")
        self.model = os.environ.get("MODEL_NAME", "gpt-4.1-mini")
        self.last_usage: dict[str, Any] = {}

    def complete(self, messages: list[dict[str, str]]) -> str:
        if not self.api_key:
            raise RuntimeError("MODEL_API_KEY is not set.")
        body = json.dumps({"model": self.model, "messages": messages}).encode()
        request = urllib.request.Request(
            f"{self.base_url}/chat/completions",
            data=body,
            headers={"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"},
        )
        with urllib.request.urlopen(request, timeout=30) as response:
            payload = json.loads(response.read().decode())
        self.last_usage = usage_from_payload(payload)
        return payload["choices"][0]["message"]["content"]


def live_enabled() -> bool:
    return llm_mode() == "live" and bool(os.environ.get("MODEL_API_KEY"))

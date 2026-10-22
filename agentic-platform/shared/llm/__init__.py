"""Model access. Agents call complete(); they never import a vendor SDK."""

from __future__ import annotations

import os
from typing import Protocol

from shared.config import llm_mode


class Provider(Protocol):
    """One completion call. Mock mode is deterministic."""

    name: str

    def complete(self, instruction: str, task: str, evidence: str) -> str:
        """Return a short answer grounded in evidence."""


class MockProvider:
    """Repeat the evidence. No network call."""

    name = "mock"

    def complete(self, instruction: str, task: str, evidence: str) -> str:
        if not evidence.strip():
            return "The source material does not establish an answer."
        return evidence.strip()[:1200]


def usage_from_payload(payload: dict) -> dict:
    """Copy model, token count, and cost when the provider included them."""
    usage = payload.get("usage") if isinstance(payload, dict) else None
    usage = usage if isinstance(usage, dict) else {}
    tokens = usage.get("total_tokens")
    cost = payload.get("cost", usage.get("cost"))
    return {
        "model": str(payload.get("model") or ""),
        "tokens": tokens if isinstance(tokens, int) else None,
        "cost": float(cost) if isinstance(cost, (int, float)) else None,
    }


class LiveProvider:
    """OpenAI-compatible chat call. Used only when mode is live and a key is set."""

    name = "openai-compatible"

    def __init__(self) -> None:
        self.model = os.environ.get("PLATFORM_LLM_MODEL", "gpt-4o-mini")
        self.base_url = os.environ.get("PLATFORM_LLM_BASE_URL", "https://api.openai.com/v1")
        self.last_usage = {"model": "", "tokens": None, "cost": None}

    def complete(self, instruction: str, task: str, evidence: str) -> str:
        if not os.environ.get("MODEL_API_KEY"):
            raise RuntimeError("MODEL_API_KEY is required when PLATFORM_LLM_MODE=live")
        import json
        from urllib.request import Request, urlopen

        body = json.dumps(
            {
                "model": self.model,
                "messages": [
                    {"role": "system", "content": instruction},
                    {"role": "user", "content": f"{task}\n\nEvidence:\n{evidence}"},
                ],
                "max_tokens": 400,
            }
        ).encode()
        request = Request(
            f"{self.base_url.rstrip('/')}/chat/completions",
            data=body,
            headers={
                "Authorization": f"Bearer {os.environ['MODEL_API_KEY']}",
                "Content-Type": "application/json",
            },
        )
        with urlopen(request, timeout=20) as response:
            payload = json.loads(response.read().decode())
        self.last_usage = usage_from_payload(payload)
        return payload["choices"][0]["message"]["content"]


def get_provider() -> Provider:
    """Live only when asked and a key exists. Otherwise the mock."""
    if llm_mode() == "live" and os.environ.get("MODEL_API_KEY"):
        return LiveProvider()
    return MockProvider()

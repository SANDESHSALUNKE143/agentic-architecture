"""Illustrative adapter contract; implement and test before registration."""

from agentic_sdk.contracts import Completion


class CustomLLM:
    def __init__(self, approved_client, model: str):
        self.client = approved_client
        self.model = model

    def complete(self, prompt: str, max_tokens: int) -> Completion:
        raise NotImplementedError("Map provider response, usage, deadline and sanitized errors")

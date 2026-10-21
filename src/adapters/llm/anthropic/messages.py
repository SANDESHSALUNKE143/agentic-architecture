"""Native Anthropic Messages API adapter using the provider-neutral Completion port."""

import os

from agentic_sdk.contracts import Completion


class AnthropicLLM:
    """Native Messages API adapter using an injected authenticated HTTP client."""

    def __init__(self, client, model):
        self.client, self.model = client, model

    def complete(self, prompt, max_tokens):
        """Request bounded text and account for normal, cache-created and cached input usage."""
        response = self.client.post(
            "/v1/messages",
            json={
                "model": self.model,
                "max_tokens": max_tokens,
                "messages": [{"role": "user", "content": prompt}],
            },
        )
        response.raise_for_status()
        value = response.json()
        usage = value["usage"]
        text = "".join(item["text"] for item in value["content"] if item["type"] == "text")
        # Include cache usage so the caller does not mistake cached input for free input.
        inputs = (
            usage["input_tokens"]
            + usage.get("cache_creation_input_tokens", 0)
            + usage.get("cache_read_input_tokens", 0)
        )
        return Completion(text, inputs, usage["output_tokens"])


def client(api_key_env):
    """Create an owned HTTPS client with an environment key, fixed API version and no redirects."""
    import httpx

    return httpx.Client(
        base_url="https://api.anthropic.com",
        headers={
            "x-api-key": os.environ[api_key_env],
            "anthropic-version": "2023-06-01",
        },
        timeout=20,
        follow_redirects=False,
        trust_env=False,
    )

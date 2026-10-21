"""Compatibility exports for provider consumers."""

from agentic_sdk.adapters.embeddings.compatible import CompatibleEmbedder
from agentic_sdk.adapters.llm.openai_compatible.client import client
from agentic_sdk.adapters.llm.openai_compatible.completion import CompatibleLLM

__all__ = ["client", "CompatibleLLM", "CompatibleEmbedder"]

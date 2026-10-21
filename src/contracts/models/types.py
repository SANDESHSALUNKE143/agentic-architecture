"""Synchronous language-model port and provider-neutral completion result."""

from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class Completion:
    """Provider-neutral response text and reported input/output token counts."""

    text: str
    input_tokens: int
    output_tokens: int


class LLM(Protocol):
    """Synchronous completion port independent of a provider SDK or agent framework."""

    def complete(self, prompt: str, max_tokens: int) -> Completion:
        """Generate text within the requested output-token allowance and return reported usage."""
        ...

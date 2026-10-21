"""Chat-completion mapping for Azure v1 and other compatible endpoints."""

from agentic_sdk.contracts import Completion


class CompatibleLLM:
    """Azure v1 deployment names or OpenAI-compatible provider model identifiers."""

    def __init__(self, client, model: str):
        self.client, self.model = client, model

    def complete(self, prompt: str, max_tokens: int) -> Completion:
        """Map compatible chat output and usage into Completion; reject responses missing usage."""
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            max_completion_tokens=max_tokens,
        )
        if response.usage is None:
            raise RuntimeError("provider omitted usage")
        return Completion(
            response.choices[0].message.content or "",
            response.usage.prompt_tokens,
            response.usage.completion_tokens,
        )

"""Inference contract for models an operator has already registered."""

from typing import Protocol

from agentic_sdk.core.context.identity import Context


class Predictor(Protocol):
    """Run one registered model on a feature object."""

    def predict(self, ctx: Context, model_id: str, features: dict) -> dict:
        """Return the model result. Unknown model ids fail before any call."""
        ...

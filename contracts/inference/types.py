"""
Inference contract.

Agents register model ids before the run. predict() calls one of those ids
with a feature object. Training and the inference server stay outside this port.

Usage:
    class Predictor implementation: predict(context, model_id, features) -> dict
"""

from typing import Protocol

from agentic_sdk.core.context.identity import Context


# ── Port ──────────────────────────────────────────────────────────────


class Predictor(Protocol):
    """Run one registered model on a feature object."""

    def predict(self, ctx: Context, model_id: str, features: dict) -> dict:
        """Return the model result. Unknown model ids fail before any call."""
        ...

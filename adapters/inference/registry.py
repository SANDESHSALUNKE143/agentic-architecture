"""
Model registry port.

The agent registers callables at startup. predict() requires model:invoke
and calls only a known model id. This adapter does not train models and
does not choose a remote inference server.

Usage:
    models = ModelRegistry({"score_model": score})
    result = models.predict(context, "score_model", {"name": "north"})
"""

from agentic_sdk.contracts.orchestration.types import ExecutionError
from agentic_sdk.core.context.identity import Context


# ── Registered models ─────────────────────────────────────────────────


class ModelRegistry:
    """Map a model id to a trusted callable supplied at composition time."""

    def __init__(self, models: dict):
        """Store the approved callables. Keys are the only ids predict will accept."""
        if not isinstance(models, dict) or any(
            not isinstance(name, str) or not name for name in models
        ):
            raise ValueError("models must be a dict of named callables")
        self.models = dict(models)

    def predict(self, ctx: Context, model_id: str, features: dict) -> dict:
        """Require model:invoke and call the registered function with the feature object."""
        ctx.require("model:invoke")
        model = self.models.get(model_id)
        if model is None:
            raise ExecutionError("model is not registered")
        if not isinstance(features, dict) or len(features) > 32:
            raise ExecutionError("features must be a small object")
        result = model(features)
        if not isinstance(result, dict):
            raise ExecutionError("model result must be an object")
        return result

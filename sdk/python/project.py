"""Validated agent settings and reusable model composition."""

import json
import re
from dataclasses import dataclass, field
from pathlib import Path

from agentic_sdk.execution import RunLimits


@dataclass(frozen=True)
class ProjectConfig:
    """Validated version-two identity, model secret references and run limits."""

    tenant_id: str
    agent_id: str
    model: dict
    limits: RunLimits = field(default_factory=RunLimits)

    @classmethod
    def load(cls, path):
        """Read UTF-8 JSON from a local file and validate its closed configuration contract."""
        return cls.from_dict(json.loads(Path(path).read_text(encoding="utf-8")))

    @classmethod
    def from_dict(cls, value):
        """Reject unknown fields, unsupported providers, unsafe endpoints and invalid limits."""
        if (
            not isinstance(value, dict)
            or set(value) != {"schema_version", "tenant_id", "agent_id", "model", "limits"}
            or value["schema_version"] != 2
        ):
            raise ValueError("invalid project config v2")
        for key in ("tenant_id", "agent_id"):
            if not isinstance(value[key], str) or not re.fullmatch(
                r"[a-zA-Z0-9_-]{1,64}", value[key]
            ):
                raise ValueError("invalid identity")
        model = value["model"]
        if not isinstance(model, dict) or model.get("adapter") not in {
            "demo",
            "compatible",
            "anthropic",
        }:
            raise ValueError("unsupported model adapter")
        if model["adapter"] == "demo" and set(model) != {"adapter"}:
            raise ValueError("unexpected demo model options")
        if model["adapter"] == "anthropic":
            if (
                set(model) != {"adapter", "model", "api_key_env"}
                or not all(isinstance(v, str) and v for v in model.values())
                or not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", model["api_key_env"])
            ):
                raise ValueError("invalid Anthropic configuration")
        if model["adapter"] == "compatible":
            if set(model) != {"adapter", "base_url", "model", "api_key_env"} or not all(
                isinstance(v, str) and v for v in model.values()
            ):
                raise ValueError("invalid compatible model configuration")
            from urllib.parse import urlsplit

            endpoint = urlsplit(model["base_url"])
            if (
                endpoint.scheme != "https"
                or not endpoint.hostname
                or endpoint.username
                or endpoint.password
                or endpoint.query
                or endpoint.fragment
            ):
                raise ValueError("approved HTTPS endpoint without embedded credentials required")
            if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", model["api_key_env"]):
                raise ValueError("api_key_env must be an environment variable name")
        try:
            limits = RunLimits(**value["limits"])
        except TypeError as exc:
            raise ValueError("invalid limits") from exc
        return cls(value["tenant_id"], value["agent_id"], dict(model), limits)


def build_model(config: ProjectConfig, demo_factory):
    """Compose demo, compatible or Anthropic decisions from validated configuration.

    Only trusted demo_factory code is invoked; provider secrets come from the
    configured environment variable. No configuration-driven dynamic import occurs."""
    if config.model["adapter"] == "demo":
        return demo_factory()
    if config.model["adapter"] == "anthropic":
        from agentic_sdk.adapters.anthropic import AnthropicLLM, client

        from agentic_sdk.decision_models import JsonDecisionModel

        return JsonDecisionModel(
            AnthropicLLM(client(config.model["api_key_env"]), config.model["model"])
        )
    from agentic_sdk.adapters.providers import CompatibleLLM, client

    from agentic_sdk.decision_models import JsonDecisionModel

    c = client(config.model["base_url"], config.model["api_key_env"])
    return JsonDecisionModel(CompatibleLLM(c, config.model["model"]))

"""Version-one local RAG configuration; the agent/hosted paths use ProjectConfig v2."""

import json
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Config:
    """Version-one local RAG demonstration configuration; use ProjectConfig for tool agents."""

    schema_version: int
    agent_id: str
    tenant_id: str
    llm_adapter: str
    token_budget: int
    max_output_tokens: int


def load(path: str) -> Config:
    """Load the closed v1 demo JSON schema; reject unsupported identities, limits or providers."""
    raw = json.loads(Path(path).read_text(encoding="utf-8"))
    expected = set(Config.__dataclass_fields__)
    if set(raw) != expected:
        raise ValueError("missing or unknown configuration fields")
    for key in ("schema_version", "token_budget", "max_output_tokens"):
        if type(raw[key]) is not int:
            raise ValueError("integer required: " + key)
    if (
        raw["schema_version"] != 1
        or raw["token_budget"] < 1
        or not 1 <= raw["max_output_tokens"] <= 4096
    ):
        raise ValueError("unsupported version or limits")
    for key in ("agent_id", "tenant_id"):
        if (
            not isinstance(raw[key], str)
            or not raw[key].isascii()
            or not raw[key].replace("-", "").replace("_", "").isalnum()
            or len(raw[key]) > 64
        ):
            raise ValueError("invalid identity")
    if raw["llm_adapter"] != "echo":
        raise ValueError(
            "example configuration supports echo only; wire network adapters explicitly"
        )
    return Config(**raw)

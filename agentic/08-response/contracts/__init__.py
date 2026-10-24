"""AgentRequest, AgentContract, and AgentResponse fields.

Purpose: the execution interface every agent shares. output_schema is checked here.
Used by: agentic/01-entry/app.py, the runtime, and the workflow engine.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from typing import Any

import jsonschema
import yaml
from loops.memory.rag import normalize_model, normalize_rag
from observability.sinks.sinks import DEFAULT, IDS, ordered

STATUSES = ("completed", "needs_approval", "failed", "not_implemented")


def new_id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


@dataclass
class AgentRequest:
    task: str
    user_id: str = "local-development-user"
    request_id: str = ""
    context: dict[str, Any] = field(default_factory=dict)
    permissions: dict[str, bool] = field(default_factory=dict)
    session_id: str = ""
    workflow: str | None = None
    agents: list[str] | None = None

    def __post_init__(self) -> None:
        if not self.request_id:
            self.request_id = new_id("run")
        if not self.session_id:
            self.session_id = new_id("ses")


@dataclass
class AgentContract:
    name: str
    description: str
    instructions: list[str]
    tools: list[str]
    memory: dict[str, Any]
    permissions: dict[str, bool]
    output_schema: dict[str, Any]
    approval: dict[str, Any]
    evaluation: dict[str, Any]
    observability: list[str]
    rag: dict[str, Any]
    model: dict[str, Any]
    path: str


def load_contract(path) -> AgentContract:
    raw = yaml.safe_load(PathText.read(path))
    for key in ("name", "description", "instructions", "tools", "permissions", "output_schema"):
        if key not in raw:
            raise ValueError(f"{path} is missing {key}")
    return AgentContract(
        name=raw["name"],
        description=str(raw["description"]).strip(),
        instructions=list(raw["instructions"]),
        tools=list(raw["tools"]),
        memory=dict(raw.get("memory") or {}),
        permissions={key: bool(value) for key, value in dict(raw["permissions"]).items()},
        output_schema=dict(raw["output_schema"]),
        approval=dict(raw.get("approval") or {}),
        evaluation=dict(raw.get("evaluation") or {}),
        observability=_observability(raw.get("observability"), path),
        rag=normalize_rag(raw.get("rag"), path),
        model=normalize_model(raw.get("model"), path),
        path=str(path),
    )


def _observability(raw, path) -> list[str]:
    selected = list(DEFAULT if raw is None else raw)
    unknown = [item for item in selected if item not in IDS]
    if unknown:
        raise ValueError(f"{path} names unknown observability tools: {', '.join(unknown)}")
    return ordered(selected)


def dump_contract(contract: AgentContract, payload: dict[str, Any]) -> None:
    from pathlib import Path

    Path(contract.path).write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")


def validate_output(schema: dict[str, Any], result: dict[str, Any]) -> str | None:
    try:
        jsonschema.validate(result, schema)
    except jsonschema.ValidationError as exc:
        return exc.message
    return None


class PathText:
    @staticmethod
    def read(path) -> str:
        from pathlib import Path

        return Path(path).read_text(encoding="utf-8")

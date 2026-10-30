"""Shape a tool result into the contract output.

Purpose: project tool observations onto output_schema and build the argument model for one tool.
Used by: agentic/04-loops/runtime/runtime.py.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field, create_model
from response.contracts import AgentContract

_TYPE = {"string": str, "number": float, "array": list, "object": dict, "boolean": bool}


def public_result(contract: AgentContract, result: dict) -> dict:
    return {key: result.get(key) for key in contract.output_schema.get("properties", {})}


def project(schema: dict, calls: list[dict], notes: list[dict]) -> dict:
    bag: dict[str, Any] = {}
    for call in calls:
        payload = call.get("result") or {}
        if not isinstance(payload, dict):
            continue
        for key, value in payload.items():
            if key == "sources" and isinstance(value, list):
                bag.setdefault("sources", []).extend(value)
            elif value not in (None, ""):
                bag[key] = value
        for key, value in (call.get("arguments") or {}).items():
            bag.setdefault(key, value)
    if notes and "explanation" not in bag:
        bag["explanation"] = notes[0]["text"]
    for note in notes:
        if note.get("source_id"):
            bag.setdefault("sources", []).append({"source_id": note["source_id"], "location": note.get("location") or ""})
    projected = {}
    for key, spec in schema.get("properties", {}).items():
        if key in bag:
            projected[key] = bag[key]
        elif spec.get("type") == "array":
            projected[key] = []
        elif spec.get("type") == "string":
            projected[key] = bag.get("explanation") or "Completed from tool observations."
        elif spec.get("type") == "object":
            projected[key] = {}
        elif spec.get("type") == "boolean":
            projected[key] = False
        elif spec.get("type") == "number":
            projected[key] = 0
    if "answer" in schema.get("properties", {}) and not projected.get("answer"):
        projected["answer"] = projected.get("explanation") or "The indexed sources do not establish an answer."
    return projected


def args_model(name: str, gateway) -> type[BaseModel]:
    schema = gateway.schema_for(name)
    fields = {}
    for key, kind in schema.items():
        fields[key] = ( _TYPE.get(kind, str), Field(default=None) )
    return create_model(f"{name}_args", **fields)


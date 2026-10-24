"""Save one agent contract.

Purpose: reject a tool the contract cannot call, then write agent.yaml.
Used by: orchestrator/catalog.py. Plugin, RAG, and observability saves call apply_contract.
"""

from __future__ import annotations

from pathlib import Path

import yaml
from shared.config import ROOT
from shared.contracts import AgentContract
from shared.loader import load_module
from shared.memory.rag import CADENCE, EMBEDDINGS, MODELS, VECTORS
from shared.observability.sinks import IDS, ordered

_gateway_mod = load_module(ROOT / "mcp" / "tool-gateway" / "gateway.py", "tool_gateway")
WRITE_TOOLS = {name for name, spec in _gateway_mod.REGISTRY.items() if spec["write"]}

def _described(platform) -> dict:
    return {item["name"]: item for item in platform.gateway.describe()}


def connection_ready(platform, name: str) -> bool:
    item = _described(platform).get(name)
    return bool(item and item["connection_ready"])


def connection_summary(platform, name: str) -> str:
    item = _described(platform).get(name) or {}
    return item.get("connection_summary") or "Save the connection before this tool can be used."


def _memory(memory: dict) -> dict:
    if "notes" not in memory:
        return memory
    raw = memory.get("notes") or []
    if not isinstance(raw, list):
        raise ValueError("Notes are a list of details.")
    notes = [str(item).strip()[:2000] for item in raw if str(item).strip()]
    memory["notes"] = notes[:40]
    return memory



def apply_contract(platform, agent_id: str, updates: dict) -> AgentContract:
    contract = platform.contracts[agent_id]
    unknown = set(updates) - {"instructions", "tools", "memory", "approval", "observability", "rag", "model"}
    if unknown:
        raise ValueError("Only instructions, tools, memory, approval, observability, RAG, and model can be edited.")
    tools = list(updates.get("tools", contract.tools))
    if any(tool not in platform.gateway.names() for tool in tools):
        raise ValueError("Tools must be chosen from the registry.")
    for tool in tools:
        permission = _gateway_mod.REGISTRY[tool]["permission"]
        if not contract.permissions.get(permission, False):
            raise ValueError("That tool is outside this agent's permissions.")
        if not connection_ready(platform, tool):
            raise ValueError(connection_summary(platform, tool))
    approval = dict(updates.get("approval", contract.approval))
    required = set(approval.get("required_for") or [])
    for tool in tools:
        if tool in WRITE_TOOLS and tool not in required:
            raise ValueError("A write tool must keep its approval requirement.")
    if contract.permissions.get("order_write") is False and updates.get("permissions", {}).get("order_write"):
        raise ValueError("A read-only agent cannot be granted order_write.")
    selected = ordered(list(updates.get("observability", contract.observability)))
    if any(item not in IDS for item in updates.get("observability", contract.observability)):
        raise ValueError("Observability tools must be chosen from the catalog.")
    rag = dict(updates.get("rag", contract.rag))
    model = dict(updates.get("model", contract.model))
    if str(rag.get("vector") or "local") not in VECTORS or str(rag.get("embedding") or "local") not in EMBEDDINGS:
        raise ValueError("RAG vector and embedding must be chosen from the catalog.")
    cadence = "off" if not rag.get("capture") else str(rag.get("cadence") or "each_run")
    if cadence not in CADENCE:
        raise ValueError("Ingestion cadence must be off, each run, hourly, or daily.")
    if str(model.get("provider") or "platform") not in MODELS:
        raise ValueError("The model provider must be chosen from the catalog.")
    payload = yaml.safe_load(Path(contract.path).read_text(encoding="utf-8"))
    payload["instructions"] = list(updates.get("instructions", contract.instructions))
    payload["tools"] = tools
    payload["memory"] = _memory(dict(updates.get("memory", contract.memory)))
    payload["approval"] = approval
    payload["observability"] = selected
    payload["rag"] = {
        "retrieve": bool(rag.get("retrieve")),
        "capture": bool(rag.get("capture")),
        "vector": str(rag.get("vector") or "local"),
        "embedding": str(rag.get("embedding") or "local"),
        "cadence": cadence,
    }
    payload["model"] = {"provider": str(model.get("provider") or "platform")}
    Path(contract.path).write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")
    platform.reload()
    return platform.contracts[agent_id]

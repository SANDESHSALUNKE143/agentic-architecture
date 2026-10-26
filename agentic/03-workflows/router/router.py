"""Pick one specialist or one workflow.

Purpose: an agents list wins, then a workflow name, then phrases loaded from files.
Used by: agentic/03-workflows/runs.py. Add a workflow.yaml or a route block. Do not add a name here.
"""

from __future__ import annotations

from pathlib import Path

import yaml

from agentic.platform.config import ROOT

SEQUENCES = ROOT / "agentic" / "03-workflows" / "sequences"
SPECIALISTS = ROOT / "agentic" / "04-loops" / "specialists"


def load_sequences() -> list[dict]:
    rows = [_sequence(path) for path in sorted(SEQUENCES.glob("*/workflow.yaml"))]
    rows.sort(key=lambda row: (row["order"], row["name"]))
    return rows


def load_specialist_routes() -> list[dict]:
    rows = []
    for path in sorted(SPECIALISTS.glob("*/agent.yaml")):
        route = _specialist_route(path)
        if route is not None:
            rows.append(route)
    return rows


def route(task: str, workflow: str | None, agents: list[str] | None) -> tuple[str, list[str]]:
    if agents:
        return "agent-chain", list(agents)
    sequences = {row["name"]: row for row in load_sequences()}
    specialists = {row["name"]: row for row in load_specialist_routes()}
    if workflow:
        chosen = sequences.get(workflow) or specialists.get(workflow)
        if chosen is None:
            return "unknown", []
        return workflow, list(chosen["agents"])
    lowered = task.lower()
    catalog = sorted([*sequences.values(), *specialists.values()], key=lambda row: (row["priority"], row["name"]))
    for row in catalog:
        if any(phrase in lowered for phrase in row["phrases"]):
            return row["name"], list(row["agents"])
    return "ambiguous", []


def _sequence(path: Path) -> dict:
    raw = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    name = str(raw.get("name") or "").strip()
    agents = [str(item) for item in raw.get("agents") or []]
    if not name or not agents:
        raise ValueError(f"{path} needs a name and an agents list")
    return {
        "name": name,
        "agents": agents,
        "phrases": [str(item) for item in raw.get("phrases") or []],
        "priority": int(raw.get("priority", 100)),
        "order": int(raw.get("order", 100)),
        "path": str(path.relative_to(ROOT)),
    }


def _specialist_route(path: Path) -> dict | None:
    raw = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    route_block = raw.get("route")
    if not route_block:
        return None
    name = str(route_block.get("id") or "").strip()
    phrases = [str(item) for item in route_block.get("phrases") or []]
    agent = str(raw.get("name") or "").strip()
    if not name or not phrases or not agent:
        raise ValueError(f"{path} route needs id, phrases, and an agent name")
    return {
        "name": name,
        "agents": [agent],
        "phrases": phrases,
        "priority": int(route_block.get("priority", 100)),
        "path": str(path.relative_to(ROOT)),
    }

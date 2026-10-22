"""Check the allowlist, hop cap, and delegation before any tool runs."""

from __future__ import annotations

from dataclasses import dataclass

from shared.config import MAX_HOPS
from shared.security.delegation import can_delegate


@dataclass
class Plan:
    agents: list[str]
    error: str = ""
    error_code: str = ""


def build_plan(agent_ids: list[str], known: set[str]) -> Plan:
    if not agent_ids:
        return Plan([], "The request did not match a workflow.", "ambiguous_intent")
    if len(agent_ids) > MAX_HOPS:
        return Plan([], "The plan exceeds the hop limit.", "hop_limit")
    unknown = [agent_id for agent_id in agent_ids if agent_id not in known]
    if unknown:
        return Plan([], f"Unknown agent {unknown[0]}.", "unknown_agent")
    for source, target in zip(agent_ids, agent_ids[1:]):
        allowed, reason = can_delegate(source, target)
        if not allowed:
            return Plan([], reason, "delegation_denied")
    return Plan(agent_ids)

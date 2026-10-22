"""Turn a route into a step list. Delegation and hop limits are checked here."""

from __future__ import annotations

from shared.config import MAX_HOPS
from shared.security.delegation import can_delegate


def plan(agent_ids: list[str], known: set[str]) -> dict:
    """Accept the list or return an error_code and message."""
    if not agent_ids:
        return {
            "ok": False,
            "error_code": "ambiguous_intent",
            "message": "The planner has no steps.",
        }
    if len(agent_ids) > MAX_HOPS:
        return {
            "ok": False,
            "error_code": "step_limit",
            "message": f"The chain has {len(agent_ids)} hops. The limit is {MAX_HOPS}.",
        }
    unknown = [agent_id for agent_id in agent_ids if agent_id not in known]
    if unknown:
        return {
            "ok": False,
            "error_code": "unknown_agent",
            "message": f"Unknown agent {unknown[0]}.",
        }
    seen: set[tuple[str, str]] = set()
    for source, target in zip(agent_ids, agent_ids[1:]):
        pair = (source, target)
        if pair in seen:
            return {
                "ok": False,
                "error_code": "loop_detected",
                "message": f"Repeated handoff {source} -> {target}.",
            }
        seen.add(pair)
        allowed, reason = can_delegate(source, target)
        if not allowed:
            return {
                "ok": False,
                "error_code": "delegation_denied",
                "message": reason,
                "source": source,
                "target": target,
            }
    return {"ok": True, "agents": agent_ids}

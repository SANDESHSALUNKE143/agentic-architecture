"""Every allowlisted ordered pair. This is the working set of combinations."""

from __future__ import annotations

from shared.security.delegation import READ_ONLY_AGENTS, WRITE_EDGES, can_delegate


def allowlisted_pairs(agent_ids: list[str]) -> list[tuple[str, str]]:
    pairs = []
    for source in agent_ids:
        for target in agent_ids:
            if source == target:
                continue
            allowed, _reason = can_delegate(source, target)
            if allowed:
                pairs.append((source, target))
    return pairs


def pair_kind(source: str, target: str) -> str:
    if (source, target) in WRITE_EDGES:
        return "write"
    if target in READ_ONLY_AGENTS:
        return "read"
    return "other"

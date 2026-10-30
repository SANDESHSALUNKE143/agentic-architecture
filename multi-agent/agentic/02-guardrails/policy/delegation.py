"""Which agent may hand work to which other agent.

Purpose: allow a read agent to hand work to another read agent. A write hop runs only when the source contract lists the target.
Used by: agentic/02-guardrails/policy/planner.py before any tool runs. Declare the hop on the source agent.yaml.
"""

from __future__ import annotations


def can_delegate(source: str, target: str, contracts: dict) -> tuple[bool, str]:
    if source == target:
        return False, "An agent cannot hand off to itself."
    src = contracts.get(source)
    tgt = contracts.get(target)
    if src is None or tgt is None:
        return False, f"{source} cannot hand off to {target}."
    if getattr(src, "handoff", "read") == "read" and getattr(tgt, "handoff", "read") == "read":
        return True, "Read-only hop is allowed."
    if target in list(getattr(src, "delegates_to", []) or []):
        return True, "This write hop is allowlisted."
    return False, f"{source} cannot hand off to {target}."

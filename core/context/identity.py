"""
Call identity — tenant, agent, and the permissions for this one request.

Context is built by the agent or the credential binding. The model cannot
add a permission. require() fails closed when the grant is missing.

Usage:
    context = Context("tenant", "my-agent", frozenset({"agent:invoke"}))
    context.require("agent:invoke")
"""

from dataclasses import dataclass


# ── Identity ──────────────────────────────────────────────────────────


@dataclass(frozen=True)
class Context:
    """Trusted, immutable tenant/agent identity and permission grants.

    Construct in application composition or credential binding, never from model output.
    This guard prevents accidental misuse; it does not sandbox malicious Python code."""

    tenant_id: str
    agent_id: str
    permissions: frozenset[str]

    def require(self, permission: str) -> None:
        """Raise PermissionError when identity is empty or the permission is absent."""
        if not self.tenant_id or not self.agent_id or permission not in self.permissions:
            raise PermissionError(permission)

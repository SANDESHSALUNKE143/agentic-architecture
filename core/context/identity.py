"""Trusted identity and permission checks shared by every execution path."""

from dataclasses import dataclass


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

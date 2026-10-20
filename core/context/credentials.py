"""
Scoped credentials — a revocable token beside the static bearer.

The static bearer still unlocks a prototype. A scoped credential is for
one tenant and one agent, carries an explicit set of permissions, and
can be revoked without rotating the process secret. This is not a
sign-in provider. There is no issuer discovery and no refresh dance.

Usage:
    store = CredentialStore()
    token = store.issue(context, frozenset({"agent:invoke"}))
    store.resolve(token)
    store.revoke(token)
"""

from __future__ import annotations

import secrets
import threading
from dataclasses import dataclass

from agentic_sdk.core.context.identity import Context

# ── Store ─────────────────────────────────────────────────────────────


@dataclass(frozen=True)
class Credential:
    """One issued credential. The secret itself is the lookup key, not a field here."""

    tenant_id: str
    agent_id: str
    scopes: frozenset[str]


class CredentialStore:
    """Issue, resolve, and revoke in-process credentials.

    The secret is a random URL-safe string. Resolving an unknown or
    revoked secret returns None. The store does not accept a secret the
    caller invented, so a short or guessable value cannot be inserted.
    """

    def __init__(self) -> None:
        self._rows: dict[str, Credential] = {}
        self._lock = threading.Lock()

    def issue(self, ctx: Context, scopes: frozenset[str]) -> str:
        """Create a credential for this tenant and agent and return its secret once."""
        if not scopes:
            raise ValueError("a credential needs at least one scope")
        secret = secrets.token_urlsafe(32)
        with self._lock:
            self._rows[secret] = Credential(ctx.tenant_id, ctx.agent_id, scopes)
        return secret

    def resolve(self, secret: str) -> Credential | None:
        """Return the credential for a live secret, or None when it is unknown."""
        with self._lock:
            return self._rows.get(secret)

    def revoke(self, secret: str) -> None:
        """Drop a secret. Revoking an unknown secret is a no-op."""
        with self._lock:
            self._rows.pop(secret, None)

    def allows(self, secret: str, scope: str) -> bool:
        """True only when the secret is live and its scopes include the requested one."""
        row = self.resolve(secret)
        return row is not None and scope in row.scopes

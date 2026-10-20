"""
Admin audit — who did a named action to a named target.

An operator save, a credential revoke, or a document delete should leave
an event. The event names the action and the target id. It does not
include the question, the answer, the prompt, or a secret. That keeps the
audit useful after a support review without turning it into a second copy
of the user's data.

Usage:
    audit = AuditLog()
    audit.record(context, "credential.revoke", "cred-1", "ok")
"""

from __future__ import annotations

import threading
import time

from agentic_sdk.core.context.identity import Context

_BLOCKED = ("question", "answer", "prompt", "content", "password", "secret", "token")


# ── Log ───────────────────────────────────────────────────────────────


class AuditLog:
    """Append-only in-process audit events with a content denylist."""

    def __init__(self) -> None:
        self.events: list[dict[str, str | float]] = []
        self._lock = threading.Lock()

    def record(self, ctx: Context, action: str, target: str, status: str) -> dict:
        """Append one event. Action and target are identifiers, not payloads.

        1. Reject a blank action.
        2. Reject text that looks like a question, an answer, or a secret.
        3. Store tenant, agent, action, target, and status.
        """
        fields = " ".join((action, target, status)).lower()
        if not action.strip() or any(word in fields for word in _BLOCKED):
            raise ValueError(
                "audit events must name an action and must not carry content or secrets"
            )
        event = {
            "tenant_id": ctx.tenant_id,
            "agent_id": ctx.agent_id,
            "action": action,
            "target": target,
            "status": status,
            "recorded_at": time.time(),
        }
        with self._lock:
            self.events.append(event)
        return event

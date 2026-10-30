"""In-memory credential slots.

Purpose: hold a scoped value for a run. This is not the connector store, and the process token is not kept here.
Used by: agentic/platform/composition.py. Passwords saved in the console go through agentic/02-guardrails/connections/endpoints.py.
"""

from __future__ import annotations


class CredentialStore:
    def __init__(self) -> None:
        self._items: dict[tuple[str, str, str], str] = {}

    def put(self, tenant: str, agent_id: str, scope: str, value: str) -> None:
        self._items[(tenant, agent_id, scope)] = value

    def get(self, tenant: str, agent_id: str, scope: str) -> str | None:
        return self._items.get((tenant, agent_id, scope))

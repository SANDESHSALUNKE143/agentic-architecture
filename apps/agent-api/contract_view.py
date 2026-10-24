"""Contract fields the console may show.

Purpose: shape one agent.yaml for GET and PUT /settings/agents. output_schema is read-only.
Used by: apps/agent-api/routes_settings.py.
"""

from __future__ import annotations


def contract_view(contract) -> dict:
    return {
        "name": contract.name,
        "description": contract.description,
        "instructions": contract.instructions,
        "tools": contract.tools,
        "memory": contract.memory,
        "permissions": contract.permissions,
        "approval": contract.approval,
        "observability": contract.observability,
        "rag": contract.rag,
        "model": contract.model,
        "output_schema": contract.output_schema,
    }

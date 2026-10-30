"""Contracts, plugins, and connector addresses.

Purpose: list plugins and connect one only when the agent already has the permission.
Used by: agentic/platform/composition.py. Saving the YAML file is agentic/platform/contract_edit.py.
"""

from __future__ import annotations

from guardrails.connections.mcp_servers import public as mcp_server_list
from loops.memory.rag import EMBEDDINGS, MODELS, VECTORS
from loops.memory.rag import describe as describe_rag
from observability.sinks.sinks import IDS, describe
from response.contracts import AgentContract

from agentic.platform.config import ROOT
from agentic.platform.contract_edit import apply_contract, connection_ready, connection_summary
from agentic.platform.loader import load_module

_gateway_mod = load_module(ROOT / "agentic" / "05-tools" / "mcp" / "tool-gateway" / "gateway.py", "tool_gateway")


def _connections(env) -> list[dict]:
    from guardrails.connections.endpoints import is_configured

    rows = [
        ("sql", "SQL", "SQL_CONNECTION", "sql", "Using the local read-only fixture.", "A database connection is configured."),
        ("web", "Web", "WEB_ALLOWLIST", "", "Using the local example.test allowlist.", "A host allowlist is configured."),
        ("n8n", "n8n", "N8N_BASE_URL", "n8n", "This repository does not host n8n. Enter its URL in connection configuration.", "An n8n URL is configured. Writes still wait for approval."),
        ("vector", "Vector search", "QDRANT_URL", "qdrant", "Using the local document index.", "Qdrant is configured."),
        ("graph", "Graph", "NEO4J_URL", "neo4j", "Using the local entity graph.", "Neo4j is configured."),
        ("model", "Model", "MODEL_API_KEY", "", "Mock mode. No key is stored here.", "A model key is set. The value is not shown."),
    ]
    connections = []
    for item_id, title, variable, endpoint_id, local_detail, live_detail in rows:
        configured = is_configured(endpoint_id, variable, env) if endpoint_id else bool(env.get(variable))
        connections.append({
            "id": item_id,
            "title": title,
            "variable": variable,
            "configured": configured,
            "detail": live_detail if configured else local_detail,
        })
    return connections


class Catalog:
    def plugins(self) -> dict:
        import os

        connected: dict[str, list[str]] = {name: [] for name in self.gateway.names()}
        eligible: dict[str, list[str]] = {name: [] for name in self.gateway.names()}
        for contract in self.contracts.values():
            for tool in contract.tools:
                if tool in connected:
                    connected[tool].append(contract.name)
            for name, spec in _gateway_mod.REGISTRY.items():
                if contract.permissions.get(spec["permission"], False):
                    eligible[name].append(contract.name)
        plugins = []
        for item in self.gateway.describe():
            plugins.append({
                **item,
                "connected_agents": connected[item["name"]],
                "eligible_agents": eligible[item["name"]],
            })
        return {"plugins": plugins, "connections": _connections(os.environ), "observability": self.observability(), "rag": self.rag_catalog(), "endpoints": self.endpoints(), "mcp_servers": mcp_server_list()}

    def endpoints(self) -> list[dict]:
        from guardrails.connections.endpoints import public

        return public()

    def save_endpoint(self, endpoint_id: str, url: str, connection_string: str, username: str, password: str) -> dict:
        from guardrails.connections.endpoints import update

        return update(endpoint_id, url, connection_string, username, password)

    def observability(self) -> list[dict]:
        import os

        rows = describe(os.environ)
        names = sorted(self.contracts)
        for row in rows:
            row["connected_agents"] = [
                contract.name for contract in self.contracts.values() if row["id"] in contract.observability
            ]
            row["eligible_agents"] = names
        return rows

    def rag_catalog(self) -> dict:
        import os

        catalog = describe_rag(os.environ)
        field = {"vector": "vector", "embedding": "embedding", "model": "provider"}
        for kind, rows in catalog.items():
            for row in rows:
                row["connected_agents"] = []
                row["eligible_agents"] = sorted(self.contracts)
                for contract in self.contracts.values():
                    current = contract.model.get("provider") if kind == "model" else contract.rag.get(field[kind])
                    if current == row["id"]:
                        row["connected_agents"].append(contract.name)
        return catalog

    def connect_rag(self, kind: str, choice: str, agents: list[str]) -> dict:
        allowed = {"vector": VECTORS, "embedding": EMBEDDINGS, "model": MODELS}
        if kind not in allowed or choice not in allowed[kind]:
            raise ValueError("Unknown RAG setting.")
        wanted = []
        for agent_id in agents:
            if agent_id in wanted:
                continue
            if agent_id not in self.contracts:
                raise ValueError(f"{agent_id} is not an agent.")
            wanted.append(agent_id)
        fallback = "platform" if kind == "model" else "local"
        for contract in list(self.contracts.values()):
            should = contract.name in wanted
            if kind == "model":
                current = contract.model.get("provider")
                if should and current != choice:
                    self.update_contract(contract.name, {"model": {"provider": choice}})
                elif not should and current == choice:
                    self.update_contract(contract.name, {"model": {"provider": fallback}})
                continue
            current = contract.rag.get(kind)
            if should and current != choice:
                updated = dict(contract.rag)
                updated[kind] = choice
                self.update_contract(contract.name, {"rag": updated})
            elif not should and current == choice:
                updated = dict(contract.rag)
                updated[kind] = fallback
                self.update_contract(contract.name, {"rag": updated})
        return self.rag_catalog()

    def connect_observability(self, sink: str, agents: list[str]) -> list[dict]:
        if sink not in IDS:
            raise ValueError("Unknown observability tool.")
        wanted = []
        for agent_id in agents:
            if agent_id in wanted:
                continue
            if agent_id not in self.contracts:
                raise ValueError(f"{agent_id} is not an agent.")
            wanted.append(agent_id)
        for contract in list(self.contracts.values()):
            has = sink in contract.observability
            should = contract.name in wanted
            if has == should:
                continue
            selected = [item for item in contract.observability if item != sink]
            if should:
                selected.append(sink)
            self.update_contract(contract.name, {"observability": selected})
        return self.observability()

    def connect_plugin(self, name: str, agents: list[str]) -> dict:
        if name not in _gateway_mod.REGISTRY:
            raise ValueError("Unknown plugin.")
        spec = _gateway_mod.REGISTRY[name]
        if agents and not connection_ready(self, name):
            raise ValueError(connection_summary(self, name))
        wanted = []
        for agent_id in agents:
            if agent_id in wanted:
                continue
            contract = self.contracts.get(agent_id)
            if contract is None or not contract.permissions.get(spec["permission"], False):
                raise ValueError(f"{agent_id} cannot use this plugin.")
            wanted.append(agent_id)
        snapshot = list(self.contracts.values())
        for contract in snapshot:
            has = name in contract.tools
            should = contract.name in wanted
            if has == should:
                continue
            tools = [tool for tool in contract.tools if tool != name]
            approval = dict(contract.approval)
            required = [tool for tool in approval.get("required_for") or [] if tool != name]
            if should:
                tools.append(name)
                if spec["write"]:
                    required.append(name)
            approval["required_for"] = required
            self.update_contract(contract.name, {"tools": tools, "approval": approval})
        return self.plugins()

    def update_contract(self, agent_id: str, updates: dict) -> AgentContract:
        return apply_contract(self, agent_id, updates)

"""Composition root. Adding an agent does not rewrite authentication, logging, or state."""

from __future__ import annotations

from pathlib import Path

import yaml
from agents.runtime import Runtime
from shared.config import MAX_HOPS, ROOT, TIMEOUT_SECONDS, data_dir, llm_mode
from shared.contracts import AgentContract, AgentRequest, load_contract
from shared.evaluation import EvaluationLog
from shared.jobs import JobRunner
from shared.loader import load_module
from shared.memory.rag import CADENCE, EMBEDDINGS, MODELS, VECTORS
from shared.memory.rag import describe as describe_rag
from shared.memory.service import MemoryService
from shared.observability.sinks import IDS, describe, ordered
from shared.observability.trace import TraceLog
from shared.security.credentials import CredentialStore
from shared.security.limits import check_task_size

from orchestrator.planner.planner import Plan, build_plan
from orchestrator.router.router import route

_gateway_mod = load_module(ROOT / "mcp" / "tool-gateway" / "gateway.py", "tool_gateway")
_engine = load_module(ROOT / "orchestrator" / "workflow-engine" / "engine.py", "workflow_engine")
_store_mod = load_module(ROOT / "orchestrator" / "state-manager" / "store.py", "run_store")

WRITE_TOOLS = {name for name, spec in _gateway_mod.REGISTRY.items() if spec["write"]}
AGENT_DIR = ROOT / "agents"


def _memory(memory: dict) -> dict:
    if "notes" not in memory:
        return memory
    raw = memory.get("notes") or []
    if not isinstance(raw, list):
        raise ValueError("Notes are a list of details.")
    notes = [str(item).strip()[:2000] for item in raw if str(item).strip()]
    memory["notes"] = notes[:40]
    return memory


def _connections(env) -> list[dict]:
    from shared.security.endpoints import is_configured

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


class Platform:
    def __init__(self) -> None:
        self.gateway = _gateway_mod.ToolGateway()
        self.memory = MemoryService()
        self.traces = TraceLog()
        self.evaluation = EvaluationLog()
        self.credentials = CredentialStore()
        self.jobs = JobRunner()
        self.store = _store_mod.RunStore()
        self.runtime = Runtime(self.gateway, self.memory, self.traces, self.evaluation)
        self.reload()

    def reload(self) -> None:
        self.contracts = {
            path.parent.name: load_contract(path)
            for path in sorted(AGENT_DIR.glob("*/agent.yaml"))
        }

    def health(self) -> dict:
        return {"status": "ok", "mode": llm_mode(), "agents": len(self.contracts)}

    def platform_settings(self) -> dict:
        import os

        return {
            "mode": llm_mode(),
            "timeout_seconds": TIMEOUT_SECONDS,
            "max_hops": MAX_HOPS,
            "model_api_key_set": bool(os.environ.get("MODEL_API_KEY")),
            "data_dir": str(data_dir()),
            "observability": describe(os.environ),
            "rag": describe_rag(os.environ),
        }

    def start(self, request: AgentRequest, on_event=None) -> dict:
        def emit(payload: dict) -> None:
            if on_event:
                on_event(payload)

        problem = check_task_size(request.task)
        if problem:
            emit({"type": "error", "message": problem})
            return self._finish(request, [], "failed", problem, "task_rejected")
        emit({"type": "activity", "message": "The agent accepted the brief"})
        name, agents = route(request.task, request.workflow, request.agents)
        plan: Plan = build_plan(agents, set(self.contracts))
        if plan.error:
            emit({"type": "error", "message": plan.error})
            return self._finish(request, [], "failed", plan.error, plan.error_code, workflow=name)
        emit({"type": "plan", "workflow": name, "agents": plan.agents, "request_id": request.request_id})
        run = {
            "request_id": request.request_id,
            "session_id": request.session_id,
            "user_id": request.user_id,
            "workflow": name,
            "agents": plan.agents,
            "index": 0,
            "responses": [],
            "status": "running",
            "running": True,
            "cancelled": False,
            "task_preview": request.task[:80],
            "task": request.task,
        }
        self.store.create(run)
        graph = _engine.compile_flow(self.runtime, self.contracts, self.store, on_event=emit)
        state = graph.invoke(_engine.initial_state(request, plan.agents))
        run["responses"] = state.get("responses") or []
        run["index"] = state.get("index", 0)
        run["running"] = False
        run["status"] = state.get("status") or "completed"
        run["error_code"] = state.get("error_code") or ""
        self._capture_approval(run)
        return self.public_run(run)

    def resume(self, approval_id: str, decision: str, actor: str) -> tuple[dict | None, str]:
        approval, error = self.store.decide(approval_id, decision, actor)
        if error:
            return None, error
        run = self.store.get(approval["run_id"])
        if decision != "approve":
            run["status"] = "failed"
            run["error_code"] = "approval_rejected"
            return self.public_run(run), ""
        if approval["argument_hash"] != _store_mod.digest(approval["arguments"]):
            return None, "stale"
        contract = self.contracts[approval["agent_id"]]
        outcome = self.gateway.call(
            run["request_id"],
            contract.permissions,
            contract.tools,
            approval["tool"],
            approval["arguments"],
            contract.approval,
            approved=True,
        )
        result = outcome.get("result") or {}
        public = {
            key: result.get(key, approval["arguments"].get(key, ""))
            for key in contract.output_schema.get("properties", {})
        }
        for item in reversed(run["responses"]):
            if item.get("requires_approval") and item.get("agent_id") == approval["agent_id"]:
                item["status"] = "completed" if outcome.get("ok") else "failed"
                item["requires_approval"] = False
                item["result"] = public
                item["pending_tool"] = None
                break
        remaining = run["agents"][run["index"] :]
        if remaining:
            request = AgentRequest(
                task=run.get("task") or "",
                user_id=run["user_id"],
                request_id=run["request_id"],
                session_id=run["session_id"],
            )
            graph = _engine.compile_flow(self.runtime, self.contracts, self.store)
            state = graph.invoke(_engine.initial_state(request, remaining))
            run["responses"].extend(state.get("responses") or [])
            run["status"] = state.get("status") or "completed"
            self._capture_approval(run)
        else:
            run["status"] = "completed"
        return self.public_run(run), ""

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
        return {"plugins": plugins, "connections": _connections(os.environ), "observability": self.observability(), "rag": self.rag_catalog(), "endpoints": self.endpoints()}

    def endpoints(self) -> list[dict]:
        from shared.security.endpoints import public

        return public()

    def save_endpoint(self, endpoint_id: str, url: str, connection_string: str, username: str, password: str) -> dict:
        from shared.security.endpoints import update

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
        contract = self.contracts[agent_id]
        unknown = set(updates) - {"instructions", "tools", "memory", "approval", "observability", "rag", "model"}
        if unknown:
            raise ValueError("Only instructions, tools, memory, approval, observability, RAG, and model can be edited.")
        tools = list(updates.get("tools", contract.tools))
        if any(tool not in self.gateway.names() for tool in tools):
            raise ValueError("Tools must be chosen from the registry.")
        for tool in tools:
            permission = _gateway_mod.REGISTRY[tool]["permission"]
            if not contract.permissions.get(permission, False):
                raise ValueError("That tool is outside this agent's permissions.")
        approval = dict(updates.get("approval", contract.approval))
        required = set(approval.get("required_for") or [])
        for tool in tools:
            if tool in WRITE_TOOLS and tool not in required:
                raise ValueError("A write tool must keep its approval requirement.")
        if contract.permissions.get("order_write") is False and updates.get("permissions", {}).get("order_write"):
            raise ValueError("A read-only agent cannot be granted order_write.")
        selected = ordered(list(updates.get("observability", contract.observability)))
        if any(item not in IDS for item in updates.get("observability", contract.observability)):
            raise ValueError("Observability tools must be chosen from the catalog.")
        rag = dict(updates.get("rag", contract.rag))
        model = dict(updates.get("model", contract.model))
        if str(rag.get("vector") or "local") not in VECTORS or str(rag.get("embedding") or "local") not in EMBEDDINGS:
            raise ValueError("RAG vector and embedding must be chosen from the catalog.")
        cadence = "off" if not rag.get("capture") else str(rag.get("cadence") or "each_run")
        if cadence not in CADENCE:
            raise ValueError("Ingestion cadence must be off, each run, hourly, or daily.")
        if str(model.get("provider") or "platform") not in MODELS:
            raise ValueError("The model provider must be chosen from the catalog.")
        payload = yaml.safe_load(Path(contract.path).read_text(encoding="utf-8"))
        payload["instructions"] = list(updates.get("instructions", contract.instructions))
        payload["tools"] = tools
        payload["memory"] = _memory(dict(updates.get("memory", contract.memory)))
        payload["approval"] = approval
        payload["observability"] = selected
        payload["rag"] = {
            "retrieve": bool(rag.get("retrieve")),
            "capture": bool(rag.get("capture")),
            "vector": str(rag.get("vector") or "local"),
            "embedding": str(rag.get("embedding") or "local"),
            "cadence": cadence,
        }
        payload["model"] = {"provider": str(model.get("provider") or "platform")}
        Path(contract.path).write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")
        self.reload()
        return self.contracts[agent_id]

    def _capture_approval(self, run: dict) -> None:
        if run["status"] != "needs_approval":
            return
        pending = next((item for item in reversed(run["responses"]) if item.get("requires_approval")), None)
        if pending and pending.get("pending_tool"):
            approval = self.store.open_approval(run["request_id"], pending["agent_id"], pending["pending_tool"])
            run["approval_id"] = approval["id"]

    def _finish(self, request, responses, status, error, error_code, workflow="") -> dict:
        run = {
            "request_id": request.request_id,
            "session_id": request.session_id,
            "user_id": request.user_id,
            "workflow": workflow,
            "agents": [],
            "responses": responses,
            "status": status,
            "running": False,
            "error": error,
            "error_code": error_code,
            "task_preview": request.task[:80],
        }
        self.store.create(run)
        return self.public_run(run)

    def public_run(self, run: dict) -> dict:
        return {
            "request_id": run["request_id"],
            "session_id": run.get("session_id", ""),
            "workflow": run.get("workflow", ""),
            "status": run.get("status"),
            "error": run.get("error", ""),
            "error_code": run.get("error_code", ""),
            "agents": [
                {
                    "agent_id": item.get("agent_id"),
                    "status": item.get("status"),
                    "result": item.get("result"),
                    "tool_calls": item.get("tool_calls", []),
                    "errors": item.get("errors", []),
                    "requires_approval": item.get("requires_approval", False),
                    "citations": item.get("citations", []),
                }
                for item in run.get("responses") or []
            ],
            "approval_id": run.get("approval_id", ""),
            "trace": self.traces.for_run(run["request_id"]),
        }

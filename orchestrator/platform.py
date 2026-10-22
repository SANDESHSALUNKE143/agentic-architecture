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
from shared.memory.service import MemoryService
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


def _connections(env) -> list[dict]:
    rows = [
        ("sql", "SQL", "SQL_CONNECTION", "Using the local read-only fixture.", "A database connection is configured."),
        ("web", "Web", "WEB_ALLOWLIST", "Using the local example.test allowlist.", "A host allowlist is configured."),
        ("n8n", "n8n", "N8N_BASE_URL", "Calls stay simulated until a base URL is set.", "An n8n base URL is configured. Writes still wait for approval."),
        ("vector", "Vector search", "QDRANT_URL", "Using the local document index.", "Qdrant is configured."),
        ("graph", "Graph", "NEO4J_URL", "Using the local entity graph.", "Neo4j is configured."),
        ("model", "Model", "MODEL_API_KEY", "Mock mode. No key is stored here.", "A model key is set. The value is not shown."),
    ]
    connections = []
    for item_id, title, variable, local_detail, live_detail in rows:
        configured = bool(env.get(variable))
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
        }

    def start(self, request: AgentRequest, on_event=None) -> dict:
        def emit(payload: dict) -> None:
            if on_event:
                on_event(payload)

        problem = check_task_size(request.task)
        if problem:
            emit({"type": "error", "message": problem})
            return self._finish(request, [], "failed", problem, "task_rejected")
        emit({"type": "activity", "message": "Accepted the task"})
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
        return {"plugins": plugins, "connections": _connections(os.environ)}

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
        unknown = set(updates) - {"instructions", "tools", "memory", "approval"}
        if unknown:
            raise ValueError("Only instructions, tools, memory, and approval can be edited.")
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
        payload = yaml.safe_load(Path(contract.path).read_text(encoding="utf-8"))
        payload["instructions"] = list(updates.get("instructions", contract.instructions))
        payload["tools"] = tools
        payload["memory"] = dict(updates.get("memory", contract.memory))
        payload["approval"] = approval
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

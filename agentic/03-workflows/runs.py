"""Run a planned list of agents and resume after approval.

Purpose: start a request, pause on a write, and continue the remaining agents after a different actor decides.
Used by: agentic/platform/composition.py. The run routes call Platform.start and Platform.resume.
"""

from __future__ import annotations

from guardrails.limits.task import check_task_size
from guardrails.policy.planner import Plan, build_plan
from response.contracts import AgentRequest
from workflows.router.router import route

from agentic.platform.config import ROOT
from agentic.platform.loader import load_module

_engine = load_module(ROOT / "agentic" / "03-workflows" / "engine" / "engine.py", "workflow_engine")
_store_mod = load_module(ROOT / "agentic" / "03-workflows" / "state" / "store.py", "run_store")


class RunFlow:
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
        plan: Plan = build_plan(agents, set(self.contracts), self.contracts)
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
        from jobs.workers.writer import flush

        flush()
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

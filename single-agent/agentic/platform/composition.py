"""Composition root.

Purpose: wire the gateway, memory, trace, and the harness. This folder has one agent.
Used by: agentic/01-entry/app.py.
"""

from __future__ import annotations

import re
from dataclasses import replace
from pathlib import Path

from guardrails.limits.task import check_task_size
from harness.runtime import AGENT_ID, Runtime
from jobs.queue.runs import RunQueue
from loops.memory.service import MemoryService
from observability.evaluation.log import EvaluationLog
from observability.trace.trace import TraceLog
from response.contracts import AgentRequest, load_contract

from agentic.platform.config import ROOT, llm_mode
from agentic.platform.loader import load_module
from agentic.platform.store import RunStore

_gateway_mod = load_module(ROOT / "agentic" / "05-tools" / "mcp" / "tool-gateway" / "gateway.py", "tool_gateway")
AGENT_DIR = ROOT / "agentic" / "04-loops" / "specialists"
HARNESSES = ("langchain", "claude", "deepagent")
_HARNESS_LINE = re.compile(r"(?m)^harness:\s*\S+\s*$")


class Platform:
    def __init__(self) -> None:
        self.gateway = _gateway_mod.ToolGateway()
        self.memory = MemoryService()
        self.traces = TraceLog()
        self.evaluation = EvaluationLog()
        self.run_queue = RunQueue()
        self.store = RunStore()
        self.runtime = Runtime(self.gateway, self.memory, self.traces, self.evaluation)
        self.contracts = {
            path.parent.name: load_contract(path)
            for path in sorted(AGENT_DIR.glob("*/agent.yaml"))
        }

    def health(self) -> dict:
        return {"status": "ok", "mode": llm_mode(), "agents": len(self.contracts), "harness": self._harness()}

    def start(self, request: AgentRequest, on_event=None) -> dict:
        problem = check_task_size(request.task)
        if problem:
            if on_event:
                on_event({"type": "error", "message": problem})
            return self._finish(request, "failed", problem, "task_rejected")
        contract = self.contracts.get(AGENT_ID)
        if contract is None:
            return self._finish(request, "failed", "desk-agent is not loaded.", "unknown_agent")
        if on_event:
            on_event({"type": "activity", "message": "The agent accepted the brief"})
        response = self.runtime.run(contract, request, on_event=on_event)
        run = {
            "request_id": request.request_id,
            "session_id": request.session_id,
            "user_id": request.user_id,
            "status": response["status"],
            "result": response.get("result") or {},
            "reply": response.get("reply") or "",
            "tool_calls": response.get("tool_calls") or [],
            "errors": response.get("errors") or [],
            "citations": response.get("citations") or [],
            "harness": response.get("harness") or contract.harness,
            "agent_id": contract.name,
            "error": "",
            "error_code": "",
        }
        self.store.create(run)
        return self.public_run(run)

    def harness_settings(self) -> dict:
        return {
            "harness": self._harness(),
            "options": [
                {"id": "langchain", "label": "LangChain", "detail": "Offline mock, or ChatOpenAI when live."},
                {"id": "claude", "label": "Claude Agent SDK", "detail": "Live harness. Needs ANTHROPIC_API_KEY."},
                {"id": "deepagent", "label": "Deep Agents", "detail": "Shadow run. Needs a live model key."},
            ],
        }

    def set_harness(self, name: str) -> dict:
        if name not in HARNESSES:
            raise ValueError(name)
        contract = self.contracts[AGENT_ID]
        path = Path(contract.path)
        text = path.read_text(encoding="utf-8")
        line = f"harness: {name}"
        text = _HARNESS_LINE.sub(line, text, count=1) if _HARNESS_LINE.search(text) else text.rstrip() + f"\n{line}\n"
        path.write_text(text, encoding="utf-8")
        self.contracts[AGENT_ID] = replace(contract, harness=name)
        return self.harness_settings()

    def _harness(self) -> str:
        contract = self.contracts.get(AGENT_ID)
        return "" if contract is None else contract.harness

    def _finish(self, request: AgentRequest, status: str, error: str, error_code: str) -> dict:
        run = {
            "request_id": request.request_id,
            "session_id": request.session_id,
            "status": status,
            "result": {},
            "reply": "",
            "tool_calls": [],
            "errors": [error_code],
            "citations": [],
            "harness": "",
            "agent_id": AGENT_ID,
            "error": error,
            "error_code": error_code,
        }
        self.store.create(run)
        return self.public_run(run)

    def public_run(self, run: dict) -> dict:
        from jobs.workers.writer import flush

        flush()
        return {
            "request_id": run["request_id"],
            "session_id": run.get("session_id", ""),
            "agent_id": run.get("agent_id", AGENT_ID),
            "status": run.get("status"),
            "result": run.get("result") or {},
            "reply": run.get("reply") or "",
            "tool_calls": run.get("tool_calls") or [],
            "errors": run.get("errors") or [],
            "citations": run.get("citations") or [],
            "harness": run.get("harness") or "",
            "error": run.get("error", ""),
            "error_code": run.get("error_code", ""),
            "trace": self.traces.for_run(run["request_id"]),
        }

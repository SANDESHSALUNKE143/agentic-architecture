"""The single-agent loop.

Purpose: load desk-agent, call the selected harness, and project output_schema.
Used by: agentic/platform/composition.py. One of langchain, claude, or deepagent runs.
"""

from __future__ import annotations

import time
from typing import Any

from guardrails.policy.redact import strip_untrusted
from harness.claude import run as run_claude
from harness.deepagent import run as run_deep
from harness.langchain import run as run_langchain
from langchain_core.tools import StructuredTool
from loops.llm import live_enabled, live_model
from loops.llm.mock import MockChatModel
from loops.memory.corpus import accept_citations
from loops.memory.rag import retrieve as retrieve_rag
from response.contracts import AgentContract, AgentRequest, validate_output
from response.project.output import args_model, project, public_result

AGENT_ID = "desk-agent"


def session_messages(history: list[dict], task: str) -> list[dict]:
    messages = []
    for item in history:
        role = item.get("role") or "user"
        if role not in {"user", "assistant"}:
            role = "user"
        text = str(item.get("text") or "").strip()
        if text:
            messages.append({"role": role, "content": text})
    messages.append({"role": "user", "content": task})
    return messages


class Runtime:
    def __init__(self, gateway, memory, traces, evaluation) -> None:
        self.gateway = gateway
        self.memory = memory
        self.traces = traces
        self.evaluation = evaluation

    def run(self, contract: AgentContract, request: AgentRequest, on_event=None) -> dict[str, Any]:
        started = time.monotonic()
        harness_name = contract.harness
        permissions = dict(contract.permissions)
        permissions.update({key: value for key, value in request.permissions.items() if key in permissions})
        self._trace(contract, request.request_id, "load_instructions", harness=harness_name, tools=list(contract.tools))
        _emit(on_event, {"type": "activity", "agent_id": contract.name, "message": "The agent loaded its instructions"})
        task = strip_untrusted(request.task)
        notes = self._notes(contract, request, task, on_event)
        prior = self.memory.history(request.session_id)
        self.memory.remember(session_id=request.session_id, role="user", text=task[:240])
        calls: list[dict] = []

        def call_tool(name: str, arguments: dict) -> dict:
            outcome = self.gateway.call(
                request.request_id,
                permissions,
                contract.tools,
                name,
                arguments,
                contract.approval,
                approved=False,
                scope=contract.name,
            )
            calls.append(outcome)
            detail = ""
            if isinstance(outcome.get("result"), dict):
                detail = str(outcome["result"].get("explanation") or "")[:180]
            _emit(on_event, {
                "type": "tool",
                "agent_id": contract.name,
                "tool": name,
                "status": outcome.get("status") or outcome.get("error_code") or "completed",
                "detail": detail,
            })
            self._trace(
                contract,
                request.request_id,
                "tool",
                harness=harness_name,
                tool=name,
                status=outcome.get("status") or outcome.get("error_code"),
            )
            return outcome

        def _tool(name: str):
            def invoke(**kwargs):
                return call_tool(name, kwargs)

            schema = args_model(name, self.gateway)
            return StructuredTool.from_function(invoke, name=name, description=name, args_schema=schema)

        names = [name for name in contract.tools if name in self.gateway.names()]
        tools = [_tool(name) for name in names]
        specs = [(name, self.gateway.schema_for(name)) for name in names]
        messages = session_messages(prior, task)
        self._trace(contract, request.request_id, "reason", harness=harness_name)
        _emit(on_event, {"type": "activity", "agent_id": contract.name, "message": "The agent is choosing its next step"})
        if harness_name == "langchain":
            model = live_model() if live_enabled() else MockChatModel()
            result = run_langchain(model, tools, list(contract.instructions), messages)
        elif harness_name == "claude":
            result = run_claude(list(contract.instructions), messages, call_tool, specs)
        elif harness_name == "deepagent":
            result = run_deep(tools, list(contract.instructions), messages)
        else:
            result = None
        if result is None or result.error:
            error = "unknown_harness" if result is None else result.error
            response = self._failed(contract, request, error, harness_name)
        else:
            if result.reply:
                self.memory.remember(session_id=request.session_id, role="assistant", text=result.reply[:240])
            response = self._response(contract, request, calls, notes, result.reply, harness_name)
        if "evaluation" in contract.observability:
            self.evaluation.record(
                request.request_id,
                contract.name,
                response["status"],
                [call.get("name", "") for call in calls],
                int((time.monotonic() - started) * 1000),
            )
        self._trace(contract, request.request_id, "persist", harness=harness_name, status=response["status"])
        return response

    def _notes(self, contract, request, task: str, on_event) -> list:
        notes = []
        if contract.memory.get("long_term_memory") == "optional":
            notes = self.memory.find_notes(request.user_id, task)
        if contract.rag.get("retrieve"):
            _emit(on_event, {"type": "activity", "agent_id": contract.name, "message": "The agent is reading its index"})
            for hit in retrieve_rag(str(contract.rag.get("vector") or "local"), task):
                notes.append({
                    "text": strip_untrusted(str(hit.get("snippet") or ""))[:240],
                    "source_id": hit.get("source_id"),
                    "location": hit.get("location") or "",
                })
        if contract.rag.get("capture"):
            self.memory.add_note(request.user_id, task[:240])
        return notes

    def _trace(self, contract: AgentContract, request_id: str, stage: str, **fields: Any) -> None:
        if "platform_trace" not in contract.observability:
            return
        self.traces.add(request_id, stage, agent_id=contract.name, **fields)

    def _failed(self, contract, request, error: str, harness_name: str) -> dict[str, Any]:
        return {
            "status": "failed",
            "result": {},
            "reply": "",
            "citations": [],
            "tool_calls": [],
            "errors": [error],
            "requires_approval": False,
            "agent_id": contract.name,
            "request_id": request.request_id,
            "harness": harness_name,
        }

    def _response(self, contract, request, calls, notes, reply: str, harness_name: str) -> dict[str, Any]:
        errors = [call["error_code"] for call in calls if call.get("error_code")]
        waiting = next((call for call in calls if call.get("status") == "needs_approval"), None)
        result = project(contract.output_schema, calls, notes)
        if reply and "explanation" in contract.output_schema.get("properties", {}) and not result.get("explanation"):
            result["explanation"] = reply
        citations = accept_citations(result.get("sources") or [])
        if "sources" in contract.output_schema.get("properties", {}):
            result["sources"] = citations
        problem = validate_output(contract.output_schema, public_result(contract, result))
        if waiting:
            status = "needs_approval"
        elif errors or problem:
            status = "failed"
            if problem:
                errors.append("schema_invalid")
        else:
            status = "completed"
        return {
            "status": status,
            "result": public_result(contract, result),
            "reply": reply,
            "citations": citations,
            "tool_calls": [
                {"name": call.get("name"), "status": call.get("status") or call.get("error_code")}
                for call in calls
            ],
            "errors": errors,
            "requires_approval": waiting is not None,
            "agent_id": contract.name,
            "request_id": request.request_id,
            "harness": harness_name,
        }


def _emit(on_event, payload: dict) -> None:
    if on_event:
        on_event(payload)

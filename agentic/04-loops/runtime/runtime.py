"""The only reasoning loop.

Purpose: load one agent.yaml, call only its allowed tools, validate output_schema, and return one response.
Used by: agentic/platform/composition.py. Output projection is agentic/08-response/project/output.py. A new agent does not copy this file.
"""

from __future__ import annotations

import time
from typing import Any

from guardrails.policy.redact import strip_untrusted
from langchain.agents import create_agent
from langchain_core.tools import StructuredTool
from loops.llm import live_enabled, live_model
from loops.llm.mock import MockChatModel
from loops.memory.corpus import accept_citations
from loops.memory.rag import retrieve as retrieve_rag
from observability.sinks.sinks import export_flags
from response.contracts import AgentContract, AgentRequest, validate_output
from response.project.output import args_model, project, public_result


class Runtime:
    def __init__(self, gateway, memory, traces, evaluation) -> None:
        self.gateway = gateway
        self.memory = memory
        self.traces = traces
        self.evaluation = evaluation

    def run(self, contract: AgentContract, request: AgentRequest, approved: bool = False, on_event=None) -> dict[str, Any]:
        started = time.monotonic()
        permissions = dict(contract.permissions)
        permissions.update({key: value for key, value in request.permissions.items() if key in permissions})
        self._trace(contract, request.request_id, "load_instructions", agent_id=contract.name, tools=list(contract.tools))
        _emit(on_event, {"type": "activity", "agent_id": contract.name, "message": "The agent loaded its instructions"})
        notes = []
        if contract.memory.get("long_term_memory") == "optional":
            notes = self.memory.find_notes(request.user_id, request.task)
        if contract.rag.get("retrieve"):
            _emit(on_event, {"type": "activity", "agent_id": contract.name, "message": "The agent is reading its index"})
            for hit in retrieve_rag(str(contract.rag.get("vector") or "local"), strip_untrusted(request.task)):
                notes.append({
                    "text": strip_untrusted(str(hit.get("snippet") or ""))[:240],
                    "source_id": hit.get("source_id"),
                    "location": hit.get("location") or "",
                })
        else:
            _emit(on_event, {"type": "activity", "agent_id": contract.name, "message": "This agent does not read from RAG"})
        if contract.rag.get("capture"):
            self.memory.add_note(request.user_id, strip_untrusted(request.task)[:240])
        self.memory.remember(session_id=request.session_id, role="user", text=strip_untrusted(request.task)[:240])
        calls: list[dict] = []

        def _tool(name: str):
            def invoke(**kwargs):
                outcome = self.gateway.call(
                    request.request_id,
                    permissions,
                    contract.tools,
                    name,
                    kwargs,
                    contract.approval,
                    approved=approved,
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
                    agent_id=contract.name,
                    tool=name,
                    status=outcome.get("status") or outcome.get("error_code"),
                )
                return outcome

            schema = args_model(name, self.gateway)
            return StructuredTool.from_function(invoke, name=name, description=name, args_schema=schema)

        tools = [_tool(name) for name in contract.tools if name in self.gateway.names()]
        model = MockChatModel()
        if live_enabled():
            model = live_model()
        agent = create_agent(model, tools, system_prompt="\n".join(contract.instructions))
        self._trace(contract, request.request_id, "reason", agent_id=contract.name)
        _emit(on_event, {"type": "activity", "agent_id": contract.name, "message": "The agent is choosing its next step"})
        agent.invoke({"messages": [{"role": "user", "content": strip_untrusted(request.task)}]})
        response = self._response(contract, request, calls, notes)
        if "evaluation" in contract.observability:
            self.evaluation.record(
                request.request_id,
                contract.name,
                response["status"],
                [call.get("name", "") for call in calls],
                int((time.monotonic() - started) * 1000),
            )
        self._trace(contract, request.request_id, "persist", agent_id=contract.name, status=response["status"])
        selected = [name for name in ("otlp", "log_store") if name in contract.observability]
        if selected:
            self._trace(
                contract,
                request.request_id,
                "export",
                agent_id=contract.name,
                sinks=selected,
                configured=export_flags(selected),
            )
        return response

    def _trace(self, contract: AgentContract, request_id: str, stage: str, **fields: Any) -> None:
        if stage != "export" and "platform_trace" not in contract.observability:
            return
        self.traces.add(request_id, stage, **fields)

    def _response(self, contract, request, calls, notes) -> dict[str, Any]:
        errors = [call["error_code"] for call in calls if call.get("error_code")]
        waiting = next((call for call in calls if call.get("status") == "needs_approval"), None)
        result = project(contract.output_schema, calls, notes)
        citations = accept_citations(result.get("sources") or [])
        result["sources"] = citations if "sources" in contract.output_schema.get("properties", {}) else result.get("sources", [])
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
            "citations": citations,
            "tool_calls": [{"name": call.get("name"), "status": call.get("status") or call.get("error_code")} for call in calls],
            "errors": errors,
            "requires_approval": waiting is not None,
            "pending_tool": None if waiting is None else {"name": waiting["name"], "arguments": waiting.get("arguments", {})},
            "agent_id": contract.name,
            "request_id": request.request_id,
        }


def _emit(on_event, payload: dict) -> None:
    if on_event:
        on_event(payload)



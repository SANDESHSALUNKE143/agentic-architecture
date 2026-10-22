"""Load instructions, resolve tools, run the LangChain loop, validate, and return one response."""

from __future__ import annotations

import time
from typing import Any

from langchain.agents import create_agent
from langchain_core.tools import StructuredTool
from pydantic import BaseModel, Field, create_model
from shared.contracts import AgentContract, AgentRequest, validate_output
from shared.llm import live_enabled
from shared.llm.mock import MockChatModel
from shared.memory.corpus import accept_citations
from shared.security.redact import strip_untrusted

_TYPE = {"string": str, "number": float, "array": list, "object": dict, "boolean": bool}


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
        self.traces.add(request.request_id, "load_instructions", agent_id=contract.name, tools=list(contract.tools))
        _emit(on_event, {"type": "activity", "agent_id": contract.name, "message": "Loaded the contract"})
        notes = []
        if contract.memory.get("long_term_memory") == "optional":
            notes = self.memory.find_notes(request.user_id, request.task)
        self.memory.remember(request.session_id, "user", strip_untrusted(request.task)[:240])
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
                self.traces.add(
                    request.request_id,
                    "tool",
                    agent_id=contract.name,
                    tool=name,
                    status=outcome.get("status") or outcome.get("error_code"),
                )
                return outcome

            schema = _args_model(name, self.gateway)
            return StructuredTool.from_function(invoke, name=name, description=name, args_schema=schema)

        tools = [_tool(name) for name in contract.tools if name in self.gateway.names()]
        model = MockChatModel()
        if live_enabled():
            model = _live_model()
        agent = create_agent(model, tools, system_prompt="\n".join(contract.instructions))
        self.traces.add(request.request_id, "reason", agent_id=contract.name)
        _emit(on_event, {"type": "activity", "agent_id": contract.name, "message": "Choosing the next step"})
        agent.invoke({"messages": [{"role": "user", "content": strip_untrusted(request.task)}]})
        response = self._response(contract, request, calls, notes)
        self.evaluation.record(
            request.request_id,
            contract.name,
            response["status"],
            [call.get("name", "") for call in calls],
            int((time.monotonic() - started) * 1000),
        )
        self.traces.add(request.request_id, "persist", agent_id=contract.name, status=response["status"])
        return response

    def _response(self, contract, request, calls, notes) -> dict[str, Any]:
        errors = [call["error_code"] for call in calls if call.get("error_code")]
        waiting = next((call for call in calls if call.get("status") == "needs_approval"), None)
        result = _project(contract.output_schema, calls, notes)
        citations = accept_citations(result.get("sources") or [])
        result["sources"] = citations if "sources" in contract.output_schema.get("properties", {}) else result.get("sources", [])
        problem = validate_output(contract.output_schema, _public_result(contract, result))
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
            "result": _public_result(contract, result),
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


def _public_result(contract: AgentContract, result: dict) -> dict:
    return {key: result.get(key) for key in contract.output_schema.get("properties", {})}


def _project(schema: dict, calls: list[dict], notes: list[dict]) -> dict:
    bag: dict[str, Any] = {}
    for call in calls:
        payload = call.get("result") or {}
        if not isinstance(payload, dict):
            continue
        for key, value in payload.items():
            if key == "sources" and isinstance(value, list):
                bag.setdefault("sources", []).extend(value)
            elif value not in (None, ""):
                bag[key] = value
        for key, value in (call.get("arguments") or {}).items():
            bag.setdefault(key, value)
    if notes and "explanation" not in bag:
        bag["explanation"] = notes[0]["text"]
    projected = {}
    for key, spec in schema.get("properties", {}).items():
        if key in bag:
            projected[key] = bag[key]
        elif spec.get("type") == "array":
            projected[key] = []
        elif spec.get("type") == "string":
            projected[key] = bag.get("explanation") or "Completed from tool observations."
        elif spec.get("type") == "object":
            projected[key] = {}
        elif spec.get("type") == "boolean":
            projected[key] = False
        elif spec.get("type") == "number":
            projected[key] = 0
    if "answer" in schema.get("properties", {}) and not projected.get("answer"):
        projected["answer"] = projected.get("explanation") or "The indexed sources do not establish an answer."
    return projected


def _args_model(name: str, gateway) -> type[BaseModel]:
    schema = gateway.schema_for(name)
    fields = {}
    for key, kind in schema.items():
        fields[key] = ( _TYPE.get(kind, str), Field(default=None) )
    return create_model(f"{name}_args", **fields)


def _live_model():
    import os

    from langchain_openai import ChatOpenAI

    return ChatOpenAI(api_key=os.environ["MODEL_API_KEY"], model=os.environ.get("MODEL_NAME", "gpt-4.1-mini"))

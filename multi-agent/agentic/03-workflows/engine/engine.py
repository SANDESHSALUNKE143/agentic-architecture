"""Run the planned agents in order.

Purpose: LangGraph steps through the agent list and pauses when a write needs approval. This is the workflow engine. n8n is not this file.
Used by: agentic/platform/composition.py after the planner accepts the list.
"""

from __future__ import annotations

import concurrent.futures
from typing import Any, TypedDict

from langgraph.graph import END, StateGraph
from response.contracts import AgentRequest

from agentic.platform.config import TIMEOUT_SECONDS


class FlowState(TypedDict, total=False):
    task: str
    user_id: str
    request_id: str
    session_id: str
    context: dict
    agents: list
    index: int
    responses: list
    status: str
    paused: bool
    error_code: str


def compile_flow(runtime, contracts: dict, store, on_event=None):
    def emit(payload: dict) -> None:
        if on_event:
            on_event(payload)

    def step(state: FlowState) -> dict:
        run = store.get(state["request_id"])
        if run and run.get("cancelled"):
            return {"status": "failed", "paused": True, "error_code": "cancelled"}
        index = state["index"]
        agent_id = state["agents"][index]
        emit({"type": "step", "status": "running", "agent_id": agent_id})
        request = AgentRequest(
            task=state["task"],
            user_id=state["user_id"],
            request_id=state["request_id"],
            session_id=state["session_id"],
            context=state.get("context") or {},
        )

        def _invoke():
            return runtime.run(contracts[agent_id], request, approved=False, on_event=on_event)

        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
            future = pool.submit(_invoke)
            try:
                response = future.result(timeout=TIMEOUT_SECONDS)
            except concurrent.futures.TimeoutError:
                response = {
                    "status": "failed",
                    "result": {},
                    "citations": [],
                    "tool_calls": [],
                    "errors": ["timeout"],
                    "requires_approval": False,
                    "agent_id": agent_id,
                }
        responses = list(state.get("responses") or []) + [response]
        emit({
            "type": "step",
            "status": response.get("status"),
            "agent_id": agent_id,
            "result": response.get("result") or {},
            "tool_calls": response.get("tool_calls") or [],
        })
        paused = bool(response.get("requires_approval"))
        failed = response.get("status") == "failed"
        return {
            "responses": responses,
            "index": index + 1,
            "status": "needs_approval" if paused else response["status"],
            "paused": paused or failed,
            "error_code": "timeout" if "timeout" in response.get("errors", []) else "",
        }

    def route(state: FlowState) -> str:
        if state.get("paused") or state.get("status") in {"failed", "needs_approval"}:
            return END
        if state["index"] >= len(state["agents"]):
            return END
        return "step"

    graph = StateGraph(FlowState)
    graph.add_node("step", step)
    graph.set_entry_point("step")
    graph.add_conditional_edges("step", route, {"step": "step", END: END})
    return graph.compile()


def initial_state(request: AgentRequest, agents: list[str]) -> dict[str, Any]:
    return {
        "task": request.task,
        "user_id": request.user_id,
        "request_id": request.request_id,
        "session_id": request.session_id,
        "context": request.context,
        "agents": agents,
        "index": 0,
        "responses": [],
        "status": "running",
        "paused": False,
    }

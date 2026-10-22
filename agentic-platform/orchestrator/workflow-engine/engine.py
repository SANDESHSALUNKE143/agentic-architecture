"""Run agents one after another.

Flow for a reader:
1. Router chooses a workflow or an explicit list.
2. Planner checks the allowlist, hop limit, and delegation matrix.
3. Each agent handles the step and returns a handoff.
4. A write tool pauses the run until a human decides.
5. The same run id resumes after approval.
"""

from __future__ import annotations

import asyncio
import contextlib
import time
from typing import Any

from agents.base import validate_output
from agents.step import Step, ToolLoop
from shared.config import MAX_OUTPUT_CHARS, MAX_TOOLS, TIMEOUT_SECONDS
from shared.contracts import Handoff
from shared.memory.rag import accept_citations
from shared.observability.trace import Timer, TraceLog
from shared.security.limits import check_task_size


class RunCancelled(Exception):
    """A caller asked this run to stop."""


async def start_run(platform, request) -> dict[str, Any]:
    """Create a run, route it, and execute until it finishes or pauses."""
    trace = TraceLog(request.request_id)
    size_error = check_task_size(request.task)
    run = _blank(request, trace)
    if size_error:
        return _fail(platform, run, "schema_invalid", size_error, "router")
    learned = None
    if not request.agents and not request.workflow:
        learned = platform.learning.match_example(request.task)
    decision = platform.router.route(
        request.task,
        {
            "agents": request.agents,
            "workflow": request.workflow,
        },
        set(platform.agents),
        learned,
    )
    if decision["error"]:
        err = decision["error"]
        return _fail(platform, run, err["error_code"], err["message"], "router")
    trace.add(
        "router",
        "ok",
        f"Selected {decision['workflow'] or decision['agents'][0]}.",
        output_summary={"workflow": decision["workflow"], "agents": decision["agents"]},
    )
    if decision["learned_from"]:
        trace.add(
            "router",
            "ok",
            f"learned_from {decision['learned_from']}",
            output_summary={"learned_from": decision["learned_from"]},
        )
    planned = platform.planner.plan(decision["agents"], set(platform.agents))
    if not planned["ok"]:
        stage = "guardrail" if planned["error_code"] == "delegation_denied" else "planner"
        return _fail(platform, run, planned["error_code"], planned["message"], stage, decision)
    trace.add("planner", "ok", "Wrote the step list.", output_summary={"agents": planned["agents"]})
    run["workflow"] = decision["workflow"]
    run["planned_agents"] = planned["agents"]
    run["learned_from"] = decision["learned_from"]
    run["running"] = True
    platform.store.save(run)
    return await advance(platform, run)


async def advance(platform, run: dict[str, Any]) -> dict[str, Any]:
    """Continue from run['cursor'] until the chain ends or a guard stops it."""
    trace = _rehydrate(run)
    agents = run["planned_agents"]
    while run["cursor"] < len(agents):
        if platform.store.is_cancelled(run["request_id"]):
            return _fail(platform, run, "cancelled", "The run was cancelled.", "guardrail")
        if len(run["tool_calls"]) >= MAX_TOOLS:
            return _fail(platform, run, "step_limit", "Tool call budget is exhausted.", "guardrail")
        target_id = agents[run["cursor"]]
        if run["cursor"] > 0:
            source_id = agents[run["cursor"] - 1]
            pair = (source_id, target_id)
            if pair in run["seen_pairs"]:
                return _fail(
                    platform,
                    run,
                    "loop_detected",
                    f"Repeated handoff {source_id} -> {target_id}.",
                    "guardrail",
                )
            allowed, reason = platform.security_can_delegate(source_id, target_id)
            trace.add(
                "guardrail",
                "ok" if allowed else "blocked",
                reason,
                agent_id=target_id,
                error_code="" if allowed else "delegation_denied",
            )
            if not allowed:
                run["status"] = "failed"
                return _close(platform, run)
            run["seen_pairs"].append(pair)
        agent = platform.agents[target_id]
        timer = Timer()
        trace.add("agent", "started", f"{agent.display_name} started.", agent_id=agent.id)
        step = Step(platform, run, agent, run.get("handoff"), trace)
        try:
            outcome = await _wait_for_handler(platform, run, agent.handler(step, []))
        except TimeoutError:
            return _fail(
                platform, run, "timeout", f"{agent.id} exceeded {TIMEOUT_SECONDS}s.", "agent"
            )
        except RunCancelled:
            return _fail(platform, run, "cancelled", "The run was cancelled.", "guardrail")
        except ToolLoop as exc:
            return _fail(
                platform,
                run,
                "loop_detected",
                f"Repeated tool call {exc.tool_name}.",
                "guardrail",
            )
        problem = validate_output(outcome)
        if problem:
            return _fail(platform, run, "schema_invalid", problem, "agent")
        outcome["citations"] = accept_citations(outcome.get("citations") or [])
        run["tool_calls"].extend(step.tool_calls)
        run["citations"].extend(outcome.get("citations") or [])
        if outcome.get("requires_qualified_review"):
            run["requires_qualified_review"] = True
        summary = str(outcome.get("summary", ""))[:MAX_OUTPUT_CHARS]
        trace.add(
            "agent",
            "needs_approval"
            if outcome.get("status") == "needs_approval"
            else "ok"
            if outcome.get("status") != "failed"
            else "failed",
            summary,
            agent_id=agent.id,
            duration_ms=timer.elapsed_ms(),
            error_code="approval_required" if outcome.get("status") == "needs_approval" else "",
        )
        run["visited"].append(agent.id)
        run["result"] = {"summary": summary, "data": outcome.get("data") or {}}
        if outcome.get("status") == "failed":
            run["status"] = "failed"
            return _close(platform, run)
        if outcome.get("status") == "needs_approval":
            pending = outcome.get("pending_tool") or {}
            approval = platform.store.open_approval(
                run_id=run["request_id"],
                agent_id=agent.id,
                action=pending.get("name", "write"),
                summary=summary,
                params=pending.get("arguments") or {},
                impact="This write stays simulated. Nothing is sent outside the process.",
            )
            run["pending_approval_id"] = approval["id"]
            run["pending_tool"] = pending
            run["status"] = "needs_approval"
            trace.add(
                "approval",
                "needs_approval",
                summary,
                agent_id=agent.id,
                tool_name=pending.get("name", ""),
                error_code="approval_required",
            )
            return _close(platform, run)
        nxt = agents[run["cursor"] + 1] if run["cursor"] + 1 < len(agents) else ""
        handoff = Handoff(
            from_agent=agent.id,
            to_agent=nxt,
            summary=summary,
            data=outcome.get("data") or {},
            tool_calls=step.tool_calls,
            citations=outcome.get("citations") or [],
        )
        run["handoff"] = handoff.as_dict()
        run["cursor"] += 1
    run["status"] = "completed"
    return _close(platform, run)


async def resume(platform, approval_id: str, decision: str, actor: str) -> dict[str, Any]:
    """Apply a human decision, then continue the same run when it was approved."""
    record = platform.store.decide(approval_id, decision, actor)
    run = platform.store.get(record["run_id"]) if record.get("run_id") else None
    if record["action"] == "save_note":
        trace = TraceLog(record["id"])
        if record["status"] == "approved":
            note = platform.memory.commit_note(record["params"])
            trace.add("approval", "ok", f"Saved note {note['id']}.", tool_name="save_note")
            return {
                "status": "completed",
                "note": note,
                "approval": record,
                "trace": trace.as_list(),
                "errors": [],
            }
        code = "approval_stale" if record["status"] == "stale" else "approval_rejected"
        trace.add(
            "approval",
            "blocked" if record["status"] != "approved" else "ok",
            record["status"],
            error_code=code,
        )
        return {
            "status": record["status"],
            "approval": record,
            "trace": trace.as_list(),
            "errors": trace.errors(),
        }
    if run is None:
        raise KeyError(approval_id)
    trace = _rehydrate(run)
    if record["status"] == "stale":
        trace.add(
            "approval",
            "blocked",
            "Approval parameters changed.",
            error_code="approval_stale",
            agent_id=record["agent_id"],
        )
        run["status"] = "failed"
        return _close(platform, run)
    if record["status"] == "rejected":
        trace.add(
            "approval",
            "blocked",
            "A human rejected the action.",
            error_code="approval_rejected",
            agent_id=record["agent_id"],
        )
        run["status"] = "failed"
        run["result"]["summary"] = "Rejected. The write was not executed."
        return _close(platform, run)
    pending = run.get("pending_tool") or {}
    agent = platform.agents[record["agent_id"]]
    outcome = await platform.gateway.call(
        agent_id=agent.id,
        permissions=agent.permissions,
        allowed_tools=agent.allowed_tools,
        name=pending["name"],
        arguments=pending.get("arguments") or {},
        trace=trace,
        approved=True,
    )
    run["tool_calls"].append(
        {
            "name": pending["name"],
            "arguments": pending.get("arguments") or {},
            "ok": outcome["ok"],
            "result": outcome["result"],
        }
    )
    trace.add(
        "approval",
        "ok",
        f"{actor} approved {pending['name']}.",
        agent_id=agent.id,
        tool_name=pending["name"],
    )
    record["audit"].append({"event": "executed", "result": "simulated"})
    run["pending_approval_id"] = None
    run["pending_tool"] = None
    run["cursor"] += 1
    run["result"]["data"]["approved_result"] = outcome["result"]
    return await advance(platform, run)


async def _wait_for_handler(platform, run: dict[str, Any], coro):
    """Run one handler until it finishes, the clock expires, or the run is cancelled."""
    task = asyncio.create_task(coro)
    started = time.perf_counter()
    try:
        while True:
            if platform.store.is_cancelled(run["request_id"]):
                task.cancel()
                with contextlib.suppress(asyncio.CancelledError):
                    await task
                raise RunCancelled()
            remaining = TIMEOUT_SECONDS - (time.perf_counter() - started)
            if remaining <= 0:
                task.cancel()
                with contextlib.suppress(asyncio.CancelledError):
                    await task
                raise TimeoutError
            done, _pending = await asyncio.wait({task}, timeout=min(0.05, remaining))
            if done:
                return task.result()
    finally:
        if not task.done():
            task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await task


def _blank(request, trace: TraceLog) -> dict[str, Any]:
    return {
        "request_id": request.request_id,
        "user_id": request.user_id,
        "session_id": request.session_id,
        "task": request.task,
        "context": request.context,
        "mode": request.mode,
        "status": "failed",
        "workflow": None,
        "planned_agents": [],
        "visited": [],
        "cursor": 0,
        "handoff": None,
        "tool_calls": [],
        "citations": [],
        "result": {},
        "learned_from": "",
        "pending_approval_id": None,
        "pending_tool": None,
        "requires_qualified_review": False,
        "seen_pairs": [],
        "running": False,
        "trace": trace,
    }


def _rehydrate(run: dict[str, Any]) -> TraceLog:
    trace = run["trace"]
    if isinstance(trace, TraceLog):
        return trace
    rebuilt = TraceLog(run["request_id"])
    rebuilt.events = trace
    run["trace"] = rebuilt
    return rebuilt


def _fail(
    platform, run, code: str, message: str, stage: str, decision: dict | None = None
) -> dict[str, Any]:
    trace = run["trace"] if isinstance(run["trace"], TraceLog) else _rehydrate(run)
    trace.add(
        stage, "failed" if code != "delegation_denied" else "blocked", message, error_code=code
    )
    run["status"] = "failed"
    if decision:
        run["workflow"] = decision.get("workflow")
        run["learned_from"] = decision.get("learned_from", "")
    run["result"] = {"summary": message, "data": {}}
    return _close(platform, run)


def _close(platform, run: dict[str, Any]) -> dict[str, Any]:
    trace = run["trace"] if isinstance(run["trace"], TraceLog) else _rehydrate(run)
    public = public_run(run, trace)
    stored = dict(public)
    stored["trace"] = trace
    stored["planned_agents"] = run["planned_agents"]
    stored["cursor"] = run["cursor"]
    stored["handoff"] = run["handoff"]
    stored["pending_tool"] = run["pending_tool"]
    stored["seen_pairs"] = run["seen_pairs"]
    stored["visited"] = list(run["visited"])
    stored["user_id"] = run["user_id"]
    stored["session_id"] = run["session_id"]
    stored["task"] = run["task"]
    stored["context"] = run["context"]
    stored["running"] = False
    run["running"] = False
    platform.store.save(stored)
    return public


def public_run(run: dict[str, Any], trace: TraceLog | None = None) -> dict[str, Any]:
    """API payload. Trace events are plain dicts."""
    if trace is None:
        raw = run.get("trace")
        events = raw.as_list() if isinstance(raw, TraceLog) else raw or []
        errors = (
            raw.errors()
            if isinstance(raw, TraceLog)
            else [
                event
                for event in events
                if event.get("status") in {"failed", "blocked", "needs_approval"}
            ]
        )
    else:
        events = trace.as_list()
        errors = trace.errors()
    visited = run.get("visited") or []
    return {
        "request_id": run["request_id"],
        "status": run["status"],
        "selected_agent": visited[0] if visited else (run.get("planned_agents") or [""])[0],
        "agents": visited,
        "planned_agents": run.get("planned_agents") or [],
        "workflow": run.get("workflow"),
        "result": run.get("result") or {},
        "tool_calls": run.get("tool_calls") or [],
        "citations": run.get("citations") or [],
        "requires_approval": run["status"] == "needs_approval",
        "requires_qualified_review": bool(run.get("requires_qualified_review")),
        "approval_id": run.get("pending_approval_id"),
        "learned_from": run.get("learned_from") or "",
        "session_id": run.get("session_id", ""),
        "trace": events,
        "errors": errors,
    }

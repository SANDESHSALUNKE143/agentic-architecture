"""
Agent runner — the shared decide, tool, answer loop.

Every business agent imports this instead of copying a loop. The model
picks the next action. The runner checks permissions, required evidence,
step count, token budget, and the deadline. Lifecycle events record status,
duration, tool name, and token counts. The question and the answer stay out.

Usage:
    runner = AgentRunner(model, tools, instruction, required_before_final=evidence)
    result = await runner.run(context, question)
"""

from __future__ import annotations

import asyncio
import json
import time
import uuid

from agentic_sdk.contracts import Context
from agentic_sdk.contracts.orchestration.types import (
    DecisionModel,
    ExecutionError,
    NullObserver,
    RunObserver,
    RunResult,
)
from agentic_sdk.core.execution.tools import ToolRegistry
from agentic_sdk.core.policies.limits import RunLimits

# ── Run loop ──────────────────────────────────────────────────────────


class AgentRunner:
    """Framework-independent model/tool loop with request-local execution state.

    Compose a DecisionModel, allowlisted tools, instructions and optional observer.
    The same runner can handle independent runs; external clients must be safe for
    the application concurrency model. No durable conversation state is retained."""

    def __init__(
        self,
        model: DecisionModel,
        tools: ToolRegistry,
        instruction: str,
        limits: RunLimits | None = None,
        observer: RunObserver | None = None,
        required_before_final: frozenset[str] = frozenset(),
        gate=None,
    ):
        self.model, self.tools, self.instruction = model, tools, instruction
        self.limits = limits or RunLimits()
        self.observer = observer or NullObserver()
        self.required_before_final = required_before_final
        self.gate = gate

    async def run(
        self,
        ctx: Context,
        question: str,
        *,
        approved_mutations: frozenset[str] = frozenset(),
    ) -> RunResult:
        """Execute a bounded run and return its answer, tool names, usage and run ID.

        Requires agent:invoke. Approval names are supplied by trusted caller code, not
        the model. Invalid model actions, repeated calls and exhausted limits fail closed.
        The observer receives content-free lifecycle events, including a final status.
        An async timeout cannot forcibly terminate a synchronous provider thread."""
        ctx.require("agent:invoke")
        if not isinstance(question, str) or not question.strip() or len(question.encode()) > 8000:
            raise ValueError("question must contain 1..8000 bytes")
        if self.gate is not None:
            self.gate.admit(ctx, question)
        run_id = uuid.uuid4().hex
        started = time.monotonic()
        observations, used, seen = [], [], set()
        input_tokens = output_tokens = reserved = 0
        status = "error"
        self.observer.emit(ctx, run_id, "run.started", {})
        try:
            async with asyncio.timeout(self.limits.timeout_seconds):
                for step in range(1, self.limits.max_steps + 1):
                    visible = self.tools.visible(ctx)
                    context_size = len(
                        json.dumps([self.instruction, question, observations, visible]).encode()
                    )
                    if context_size > self.limits.max_context_bytes:
                        raise ExecutionError("context limit exceeded")
                    reserved += context_size + self.limits.max_output_tokens + 512
                    if reserved > self.limits.token_budget:
                        raise ExecutionError("run budget exceeded")
                    reply = await self.model.decide(
                        self.instruction,
                        question,
                        observations,
                        visible,
                        self.limits.max_output_tokens,
                    )
                    if min(reply.input_tokens, reply.output_tokens) < 0:
                        raise ExecutionError("invalid model usage")
                    input_tokens += reply.input_tokens
                    output_tokens += reply.output_tokens
                    if input_tokens + output_tokens > self.limits.token_budget:
                        raise ExecutionError("reported usage exceeded budget")
                    action = reply.action
                    if not isinstance(action, dict):
                        raise ExecutionError("model action must be an object")
                    if action.get("type") == "final":
                        if not self.required_before_final <= set(used):
                            raise ExecutionError("required evidence tools were not called")
                        if set(action) != {"type", "answer"} or not isinstance(
                            action["answer"], str
                        ):
                            raise ExecutionError("invalid final action")
                        if len(action["answer"].encode()) > self.limits.max_tool_result_bytes:
                            raise ExecutionError("answer too large")
                        status = "ok"
                        return RunResult(
                            run_id,
                            action["answer"],
                            step,
                            tuple(used),
                            input_tokens,
                            output_tokens,
                        )
                    if (
                        set(action) != {"type", "tool", "arguments"}
                        or action["type"] != "tool"
                        or not isinstance(action["tool"], str)
                    ):
                        raise ExecutionError("invalid tool action")
                    signature = json.dumps(action, sort_keys=True)
                    if signature in seen:
                        raise ExecutionError("repeated identical tool call")
                    seen.add(signature)
                    tool = action["tool"]
                    tool_started = time.monotonic()
                    result = await self.tools.invoke(
                        ctx,
                        tool,
                        action["arguments"],
                        approved_mutations,
                        frozenset(used),
                    )
                    if len(json.dumps(result).encode()) > self.limits.max_tool_result_bytes:
                        raise ExecutionError("tool result exceeds limit; narrow request")
                    used.append(tool)
                    observations.append({"tool": tool, "result": result})
                    self.observer.emit(
                        ctx,
                        run_id,
                        "tool.completed",
                        {
                            "tool": tool,
                            "duration_ms": round((time.monotonic() - tool_started) * 1000, 2),
                        },
                    )
                raise ExecutionError("maximum steps exceeded")
        finally:
            if self.gate is not None:
                self.gate.charge(ctx, input_tokens + output_tokens)
            self.observer.emit(
                ctx,
                run_id,
                "run.finished",
                {
                    "status": status,
                    "duration_ms": round((time.monotonic() - started) * 1000, 2),
                    "input_tokens": input_tokens,
                    "output_tokens": output_tokens,
                    "steps": len(used),
                },
            )

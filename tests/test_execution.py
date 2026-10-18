import asyncio
import unittest
from dataclasses import replace

from agentic_sdk.contracts import Context

from agentic_sdk.execution import (
    AgentRunner,
    ExecutionError,
    ModelReply,
    RunLimits,
    ToolRegistry,
    ToolSpec,
)


class SequenceModel:
    def __init__(self, actions):
        self.actions = iter(actions)

    async def decide(self, *args):
        return ModelReply(next(self.actions), 1, 1)


class ExecutionTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.ctx = Context(
            "tenant", "agent", frozenset({"agent:invoke", "data:read", "data:write"})
        )
        self.calls = 0

        async def handler(ctx, args):
            self.calls += 1
            return {"value": 42}

        self.registry = ToolRegistry()
        self.registry.add(
            ToolSpec(
                "read",
                "Read a value",
                "data:read",
                {"type": "object", "additionalProperties": False},
                handler,
            )
        )
        self.registry.add(
            ToolSpec(
                "write",
                "Write a value",
                "data:write",
                {"type": "object"},
                handler,
                read_only=False,
            )
        )

    def runner(self, actions, **kwargs):
        return AgentRunner(SequenceModel(actions), self.registry, "instruction", **kwargs)

    async def test_real_tool_loop(self):
        result = await self.runner(
            [
                {"type": "tool", "tool": "read", "arguments": {}},
                {"type": "final", "answer": "42"},
            ]
        ).run(self.ctx, "question")
        self.assertEqual(result.tools_used, ("read",))
        self.assertEqual(result.steps, 2)

    async def test_missing_permission_no_side_effect(self):
        with self.assertRaises(PermissionError):
            await self.runner([{"type": "tool", "tool": "read", "arguments": {}}]).run(
                replace(self.ctx, permissions=frozenset({"agent:invoke"})), "question"
            )
        self.assertEqual(self.calls, 0)

    async def test_write_requires_approval(self):
        with self.assertRaises(PermissionError):
            await self.runner([{"type": "tool", "tool": "write", "arguments": {}}]).run(
                self.ctx, "question"
            )
        self.assertEqual(self.calls, 0)

    async def test_argument_validation_before_call(self):
        with self.assertRaises(ExecutionError):
            await self.runner(
                [{"type": "tool", "tool": "read", "arguments": {"unexpected": 1}}]
            ).run(self.ctx, "question")
        self.assertEqual(self.calls, 0)

    async def test_repeated_call_stops(self):
        action = {"type": "tool", "tool": "read", "arguments": {}}
        with self.assertRaises(ExecutionError):
            await self.runner([action, action]).run(self.ctx, "question")
        self.assertEqual(self.calls, 1)

    async def test_budget_before_model(self):
        with self.assertRaises(ExecutionError):
            await self.runner([], limits=RunLimits(token_budget=100)).run(self.ctx, "question")

    async def test_step_limit(self):
        with self.assertRaises(ExecutionError):
            await self.runner(
                [{"type": "tool", "tool": "read", "arguments": {}}],
                limits=RunLimits(max_steps=1),
            ).run(self.ctx, "question")

    async def test_required_evidence_before_final(self):
        with self.assertRaises(ExecutionError):
            await self.runner(
                [{"type": "final", "answer": "invented"}],
                required_before_final=frozenset({"read"}),
            ).run(self.ctx, "question")

    async def test_deadline(self):
        class Slow:
            async def decide(self, *args):
                await asyncio.sleep(1)

        with self.assertRaises(TimeoutError):
            await AgentRunner(
                Slow(), self.registry, "x", limits=RunLimits(timeout_seconds=0.01)
            ).run(self.ctx, "question")

    async def test_tool_prerequisite(self):
        async def h(ctx, args):
            self.fail("should not execute")

        self.registry.add(
            ToolSpec(
                "dependent",
                "needs read",
                "data:read",
                {"type": "object"},
                h,
                requires=frozenset({"read"}),
            )
        )
        with self.assertRaises(ExecutionError):
            await self.runner([{"type": "tool", "tool": "dependent", "arguments": {}}]).run(
                self.ctx, "question"
            )

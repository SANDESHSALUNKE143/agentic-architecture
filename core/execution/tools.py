"""
Tool registry — the allowlist the model is allowed to call.

A tool is a name, a description, a permission, a JSON schema, and a handler.
The model sees the description and the schema. It does not see the handler,
credentials, or a server URL. Invocation checks the permission and the schema
before the handler runs.

Usage:
    tools = ToolRegistry()
    tools.add(ToolSpec("read_status", "Read status.", "status:read", schema, handler))
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Awaitable, Callable

from agentic_sdk.contracts import Context
from agentic_sdk.contracts.orchestration.types import ExecutionError


# ── Tool specification ────────────────────────────────────────────────


@dataclass(frozen=True)
class ToolSpec:
    """A registered capability: input schema, permission, handler and evidence prerequisites.

    Handlers receive trusted Context and validated arguments and return a JSON object.
    Side-effecting tools must set read_only=False; approval comes from trusted code."""

    name: str
    description: str
    permission: str
    input_schema: dict
    handler: Callable[[Context, dict], Awaitable[dict]]
    read_only: bool = True
    requires: frozenset[str] = frozenset()

    def public(self):
        """Return model-visible metadata without the callable handler or permission grants."""
        return {
            "name": self.name,
            "description": self.description,
            "input_schema": self.input_schema,
            "read_only": self.read_only,
            "requires": sorted(self.requires),
        }


class ToolRegistry:
    """Explicit tool allowlist used to validate and authorize every invocation."""

    def __init__(self):
        self._tools: dict[str, ToolSpec] = {}

    def add(self, spec: ToolSpec):
        """Register a unique tool after validating its JSON schema; reject duplicates."""
        from jsonschema import Draft202012Validator

        if spec.name in self._tools:
            raise ValueError("duplicate tool")
        Draft202012Validator.check_schema(spec.input_schema)
        self._tools[spec.name] = spec

    def visible(self, ctx: Context):
        """Return metadata only for tools permitted by the supplied trusted context."""
        return [s.public() for s in self._tools.values() if s.permission in ctx.permissions]

    async def invoke(
        self,
        ctx: Context,
        name: str,
        arguments: dict,
        approved_mutations: frozenset[str],
        completed: frozenset[str] = frozenset(),
    ) -> dict:
        """Validate schema, permissions, completed prerequisites and mutation approval.

        Only then await the handler. Unknown tools or invalid inputs raise ExecutionError;
        missing grants or approvals raise PermissionError before external work begins.
        Output-size bounds are enforced by AgentRunner after this method returns."""
        from jsonschema import Draft202012Validator

        spec = self._tools.get(name)
        if spec is None:
            raise ExecutionError("unknown tool")
        ctx.require(spec.permission)
        if not spec.requires <= completed:
            raise ExecutionError("tool prerequisites not satisfied")
        if not spec.read_only and name not in approved_mutations:
            raise PermissionError("mutation requires trusted approval")
        if not isinstance(arguments, dict):
            raise ExecutionError("tool arguments must be an object")
        if not Draft202012Validator(spec.input_schema).is_valid(arguments):
            raise ExecutionError("tool arguments violate schema")
        result = await spec.handler(ctx, arguments)
        if not isinstance(result, dict):
            raise ExecutionError("tool result must be an object")
        return result

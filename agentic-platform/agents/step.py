"""What one agent can see while it handles a step."""

from __future__ import annotations

from typing import Any

from shared.contracts import digest


class ToolLoop(Exception):
    """The same tool and arguments were already used in this step."""

    def __init__(self, name: str) -> None:
        self.tool_name = name
        super().__init__(name)


class Step:
    """Task, previous handoff, memory, and allowlisted tools. Not another agent's code."""

    def __init__(self, platform, run: dict[str, Any], agent, handoff: dict | None, trace) -> None:
        self.platform = platform
        self.run = run
        self.agent = agent
        self.handoff = handoff or {}
        self.trace = trace
        self.task = run["task"]
        self.user_id = run["user_id"]
        self.session_id = run["session_id"]
        self.tool_calls: list[dict[str, Any]] = []
        self._seen_calls: set[tuple[str, str]] = set()

    def remember(self, key: str, value: Any) -> None:
        """Write the session scratchpad and record memory: short_term."""
        self.platform.memory.remember(self.session_id, key, value)
        self.trace.add(
            "memory",
            "ok",
            "memory: short_term",
            agent_id=self.agent.id,
            output_summary={"key": key},
        )

    def recall(self, key: str, default: Any = None) -> Any:
        """Read the session scratchpad."""
        value = self.platform.memory.recall(self.session_id, key, default)
        self.trace.add(
            "memory",
            "ok",
            "memory: short_term",
            agent_id=self.agent.id,
            input_summary={"key": key},
        )
        return value

    def long_term_notes(self) -> list[dict[str, Any]]:
        notes = self.platform.memory.search_notes(self.task)
        if notes:
            self.trace.add(
                "memory",
                "ok",
                "memory: long_term",
                agent_id=self.agent.id,
                output_summary={"ids": [note["id"] for note in notes]},
            )
        return notes

    async def call_tool(
        self, name: str, arguments: dict[str, Any], approved: bool = False
    ) -> dict[str, Any]:
        signature = (name, digest(arguments))
        if signature in self._seen_calls:
            self.trace.add(
                "tool",
                "blocked",
                f"Repeated tool call {name}.",
                agent_id=self.agent.id,
                tool_name=name,
                error_code="loop_detected",
            )
            raise ToolLoop(name)
        self._seen_calls.add(signature)
        outcome = await self.platform.gateway.call(
            agent_id=self.agent.id,
            permissions=self.agent.permissions,
            allowed_tools=self.agent.allowed_tools,
            name=name,
            arguments=arguments,
            trace=self.trace,
            approved=approved,
        )
        self.tool_calls.append(
            {
                "name": name,
                "arguments": arguments,
                "ok": outcome.get("ok", False),
                "result": outcome.get("result", {}),
            }
        )
        return outcome

    def previous(self, key: str, default: Any = None) -> Any:
        data = self.handoff.get("data") or {}
        if key in data:
            return data[key]
        return default

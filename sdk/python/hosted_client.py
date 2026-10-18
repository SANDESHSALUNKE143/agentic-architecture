"""Client adapters for operator-configured hosted platform endpoints."""

from agentic_sdk.execution import ModelReply


class HostedDecisionModel:
    """Delegate model decisions to an authenticated hosted-platform transport."""

    def __init__(self, transport):
        self.transport = transport

    async def decide(self, instruction, question, observations, tools, max_output_tokens):
        """Send the bounded decision context and translate the gateway reply to ModelReply."""
        result = await self.transport.request(
            "POST",
            "/v1/models/decide",
            body={
                "instruction": instruction,
                "question": question,
                "observations": observations,
                "tools": tools,
                "max_output_tokens": max_output_tokens,
            },
        )
        return ModelReply(**result)


class HostedAgentNBackend:
    """Translate the three approved AgentN REST operations to hosted tool calls."""

    def __init__(self, transport):
        self.transport = transport

    async def request(self, method, path, *, body=None, params=None):
        """Map only catalog, status and SQL operations; reject unknown paths or query parameters."""
        names = {
            ("GET", "/api/agent/catalog"): "list_tables",
            ("GET", "/api/agent/status"): "get_data_status",
            ("POST", "/api/agent/sql"): "execute_sql",
        }
        name = names.get((method, path))
        if name is None or params:
            raise ValueError("unsupported hosted tool")
        return await self.transport.request(
            "POST", "/v1/tools/" + name, body={"arguments": body or {}}
        )

    async def aclose(self):
        """Close the shared platform transport after the owning agent shuts down."""
        await self.transport.aclose()

"""Explicit adapters for caller-approved REST/n8n routes and MCP sessions.
Credentials, MCP session lifecycle and grants are supplied by trusted composition.
"""

from agentic_sdk.execution import ToolSpec


def rest_tool(
    name,
    description,
    permission,
    schema,
    transport,
    path,
    *,
    method="POST",
    read_only=False,
    requires=frozenset(),
):
    """Create an explicit ToolSpec over a trusted fixed REST route.

    POST arguments are a JSON body; GET arguments are query parameters. The
    default is a mutation requiring trusted approval in ToolRegistry."""
    if method not in {"GET", "POST"}:
        raise ValueError("only GET and POST are supported")

    async def invoke(ctx, arguments):
        return await transport.request(
            method,
            path,
            body=arguments if method == "POST" else None,
            params=arguments if method == "GET" else None,
        )

    return ToolSpec(name, description, permission, schema, invoke, read_only, requires)


def n8n_tool(name, description, permission, schema, transport, webhook_path):
    """A workflow invocation is a mutation by default and requires trusted approval."""
    if not webhook_path.startswith("/webhook/"):
        raise ValueError("use a fixed production webhook path")
    return rest_tool(
        name, description, permission, schema, transport, webhook_path, read_only=False
    )


def mcp_tool(
    name,
    description,
    permission,
    schema,
    session,
    *,
    remote_name=None,
    read_only=False,
    requires=frozenset(),
):
    """Map an allowlisted tool on an established MCP ClientSession; never auto-import tools."""

    async def invoke(ctx, arguments):
        result = await session.call_tool(remote_name or name, arguments=arguments)
        if result.isError:
            raise RuntimeError("MCP tool failed")
        structured = getattr(result, "structuredContent", None)
        if isinstance(structured, dict):
            return structured
        return {"content": [item.model_dump(mode="json") for item in result.content]}

    return ToolSpec(name, description, permission, schema, invoke, read_only, requires)

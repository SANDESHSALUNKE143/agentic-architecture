# Build another consumer without copying infrastructure

1. Create an independent package with `agentic-foundation-sdk[runtime]==0.3.0` as a dependency. Install a built wheel or your private package registry release. Editable sibling installation is for development only.
2. Define domain tools in the consumer. Each handler accepts Context and a validated argument dictionary, calls a bounded domain API through JsonTransport, and returns a JSON object. Backend permissions still decide data access.
3. Register ToolSpec values: stable name, description, permission, JSON schema, read-only flag and prerequisite tool names. Do not add arbitrary URL, shell execution or database connection tools.
4. Supply domain instructions and domain acceptance tests. Use JsonDecisionModel with a compatible LLM, or implement the DecisionModel protocol for another model/framework.
5. Compose AgentRunner with RunLimits and a RunObserver. For HTTP use AgentBinding and SDK create_app, rather than copying API routes. Keep agent IDs unique in a shared host.

```python
from agentic_sdk.contracts import Context
from agentic_sdk.execution import AgentRunner, ToolRegistry, ToolSpec
from agentic_sdk.run_store import SQLiteRunStore


async def lookup(ctx, args):
    return await transport.request("GET", "/api/catalog", params={"query": args["query"]})


tools = ToolRegistry()
tools.add(
    ToolSpec(
        "lookup",
        "Search the authorized catalog",
        "catalog:read",
        {
            "type": "object",
            "properties": {"query": {"type": "string", "maxLength": 200}},
            "required": ["query"],
            "additionalProperties": False,
        },
        lookup,
    )
)
runner = AgentRunner(
    model,
    tools,
    "Answer from catalog evidence only.",
    observer=SQLiteRunStore(".agentic/runs.db"),
    required_before_final=frozenset({"lookup"}),
)
context = Context("your-tenant", "your-agent", frozenset({"agent:invoke", "catalog:read"}))
# model and transport are constructed once in your trusted composition root.
# result = await runner.run(context, 'Find an item')
```

This snippet illustrates the composition seam; use the separate Agent N consumer for a complete executable project. Generic behavior belongs in the SDK with contract tests, not a new copy in every consumer. Domain-specific metric rules, API route paths and output expectations stay in the consumer. A new provider adapter is reusable; a new business tool usually is not.

Release rule: shared contract changes require an SDK version and consumer compatibility test. The consumer version changes independently. Do not use path modifications or copy SDK source into the consumer. For offline deployment, build wheels in CI and install from an internal wheelhouse.

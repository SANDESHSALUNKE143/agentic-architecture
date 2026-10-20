# How to use the SDK

The SDK is the shared library a business agent imports. It does not contain that agent's screens, instructions, database, or vector store.

Install one version and call it from the agent repository:

```sh
python -m pip install -e '/path/to/agentic-architecture[service]'
```

## What the SDK provides

| Piece | Import | What the agent supplies |
|---|---|---|
| Run loop | `agentic_sdk.core.harness.runner.AgentRunner` | A `DecisionModel`, the instruction text, and the tools |
| Identity and permissions | `agentic_sdk.contracts.Context` | Tenant, agent id, and the grants for this call |
| Tool registry | `agentic_sdk.core.execution.tools.ToolRegistry` | Each tool name, schema, permission, and handler |
| Read-only table port | `agentic_sdk.adapters.sql.read.ReadOnlySql` | An open DB-API connection and the allowlisted table names |
| Retrieval port | `agentic_sdk.contracts` vector store, optional `QdrantStore` | The client, the documents, and the embedding profile |
| Graph port | `agentic_sdk.adapters.graph.neo4j.Neo4jGraphRag` | An open graph session |
| Model port | `agentic_sdk.adapters.inference.registry.ModelRegistry` | The callable registered under a model id |
| Web port | `agentic_sdk.adapters.tools.web.AllowlistedWeb` | The host-to-origin allowlist |
| Traces | `agentic_sdk.adapters.observability.events.PlatformObserver` | Nothing about the question or the answer |
| Request gate | `agentic_sdk.core.policies.admission.RequestGate` | Pass `gate=` on `AgentRunner`. Rate, body cap, and token quota |
| Model usage | `agentic_sdk.adapters.observability.usage.UsageLog` | Attach it to `ResilientLLM` with a context. Prompts are not stored |
| Resilient completion | `agentic_sdk.adapters.llm.resilient.ResilientLLM` | A primary completion port and, optionally, one fallback |
| Scoped credentials | `agentic_sdk.core.context.credentials.CredentialStore` | Scopes for one tenant and agent. The static bearer still works |
| Health and audit | `HealthBoard` and `AuditLog` | A status word, an action name, and a target id |
| Jobs | `agentic_sdk.core.harness.jobs.JobRunner` | A callable and an interval. Due work runs inline on the leader |
| Retrieval policy | `GovernedStore` and `RetrievalCache` | The vector store the agent already opened |
| Workflow check | `agentic_sdk.core.harness.checks.check_workflow` | Required tool names and JSON fields. The check does not grade truth |

`required_before_final` names the evidence tools that must run before an answer. The model cannot add credentials, URLs, permissions, or mutation approval.

## What stays in the agent

- The product screen and any admin screen for that agent.
- Instructions, tool handlers, allowlists, and fixtures.
- The database and the vector database: which product, which server, which schema, which collection, and the credentials. The agent opens those connections and passes them in. The SDK checks the permission, the allowlist, and the row or neighbor cap. It does not create the business schema or choose the database.

## Smallest agent

```python
from agentic_sdk.contracts import Context
from agentic_sdk.contracts.orchestration.types import ModelReply
from agentic_sdk.core.execution.tools import ToolRegistry, ToolSpec
from agentic_sdk.core.harness.runner import AgentRunner


class Model:
    async def decide(self, instruction, question, observations, tools, max_output_tokens):
        if not observations:
            return ModelReply("tool", {"type": "tool", "tool": "read_status", "arguments": {}}, 1, 1)
        return ModelReply("final", {"type": "final", "answer": "ready"}, 1, 1)


async def read_status(ctx, arguments):
    return {"status": "ready"}


tools = ToolRegistry()
tools.add(ToolSpec(
    "read_status",
    "Read the status this agent owns.",
    "status:read",
    {"type": "object", "properties": {}, "required": []},
    read_status,
))
runner = AgentRunner(Model(), tools, "Answer from the status tool.", required_before_final=frozenset({"read_status"}))
context = Context("tenant", "my-agent", frozenset({"agent:invoke", "status:read"}))
# result = await runner.run(context, "Is it ready?")
```

A SQL or retrieval tool is the same shape. The handler calls the port with the connection the agent already opened:

```python
async def query_rows(ctx, arguments):
    return sql.query(ctx, arguments["table"], arguments["limit"])
```

`sql` is a `ReadOnlySql` built in the agent from that agent's connection and table allowlist. Swapping Postgres for another DB-API database does not change the runner.

## Operator console

`services/operator_ui` is a generic console. It lists only the agents in `OPERATOR_AGENTS`. Each entry includes that agent's own `url`. The console does not name a business agent, and it does not open that agent's database or vector store. The agent's own screen stays in the agent repository.

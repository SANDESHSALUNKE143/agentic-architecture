# Physical architecture source layout

The architecture folders contain executable Python, not only documentation.

```text
src/core/context/identity.py              Context identity and permission checks
src/core/harness/runner.py                Bounded model/tool AgentRunner
src/core/harness/rag.py                   Synchronous RAG use case
src/core/execution/tools.py               Tool specifications, validation and invocation
src/core/policies/limits.py               Execution budget/timeout policy
src/contracts/*/types.py                  Provider-neutral typed interfaces
src/adapters/llm/openai_compatible/       Compatible provider client and completion
src/adapters/llm/anthropic/messages.py    Native Messages API adapter
src/adapters/embeddings/compatible.py     Embedding adapter
src/adapters/retrieval/qdrant.py          Qdrant retrieval and index isolation
src/adapters/persistence/                 SQLite metadata and PostgreSQL state
src/adapters/observability/               OTLP/event adapters
src/adapters/tools/                       HTTP, MCP-session and n8n adapters
src/services/agent_registry/routes.py     Versioned registry endpoints
src/services/model_gateway/routes.py      Model invocation and usage endpoints
src/services/tool_gateway/routes.py       Allowlisted tool endpoints
src/services/knowledge_service/           Knowledge endpoints, components and worker
src/services/agent_host/api.py            Reusable agent HTTP API
src/services/app.py                       Local platform composition
src/sdk/python/                           Configuration, CLI and remote clients
src/agentic_sdk/                          Stable backward-compatible import facade
examples/insight_agent/                      Reference agent. Containers in stack/.
examples/sells_agent/                        Second agent. Same modules. No containers.
```

The reference agent imports `agentic_sdk` and is not mapped into the installed package. Library code does not import it. See [the enterprise guide](guide.md).

Setuptools maps each directory under `src/` to its `agentic_sdk` namespace. For example, `src/core/context/identity.py` installs as `agentic_sdk.core.context.identity`. Existing `from agentic_sdk.contracts import Context` and `from agentic_sdk.execution import AgentRunner` imports remain supported and refer to the same classes. No harness is duplicated.

Use editable installation after switching to this layout; do not use PYTHONPATH=src as a substitute for installing the package. Wheels and source distributions contain all mapped packages. Docker builds explicitly copy every source root. Framework-specific and Azure-specific wrapper folders may have no separate implementation where the existing generic adapter is the implementation; their guides identify that fact.

# Physical architecture source layout

The architecture folders contain executable Python, not only documentation.

```text
core/context/identity.py              Context identity and permission checks
core/harness/runner.py                Bounded model/tool AgentRunner
core/harness/rag.py                   Synchronous RAG use case
core/execution/tools.py               Tool specifications, validation and invocation
core/policies/limits.py               Execution budget/timeout policy
contracts/*/types.py                  Provider-neutral typed interfaces
adapters/llm/openai_compatible/        Compatible provider client and completion
adapters/llm/anthropic/messages.py     Native Messages API adapter
adapters/embeddings/compatible.py      Embedding adapter
adapters/retrieval/qdrant.py           Qdrant retrieval and index isolation
adapters/persistence/                 SQLite metadata and PostgreSQL state
adapters/observability/               OTLP/event adapters
adapters/tools/                       HTTP, MCP-session and n8n adapters
services/agent_registry/routes.py     Versioned registry endpoints
services/model_gateway/routes.py      Model invocation and usage endpoints
services/tool_gateway/routes.py       Allowlisted tool endpoints
services/knowledge_service/           Knowledge endpoints, components and worker
services/agent_host/api.py             Reusable agent HTTP API
services/app.py                       Local platform composition
sdk/python/                          Configuration, CLI and remote clients
src/agentic_sdk/                      Stable backward-compatible import facade
```

Setuptools maps each architecture source directory to its `agentic_sdk` namespace. For example, `core/context/identity.py` installs as `agentic_sdk.core.context.identity`. Existing `from agentic_sdk.contracts import Context` and `from agentic_sdk.execution import AgentRunner` imports remain supported and refer to the same classes. No harness is duplicated.

Use editable installation after switching to this layout; do not use PYTHONPATH=src as a substitute for installing the package. Wheels and source distributions contain all mapped packages. Docker builds explicitly copy every source root. Framework-specific and Azure-specific wrapper folders may have no separate implementation where the existing generic adapter is the implementation; their guides identify that fact.

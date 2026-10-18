# Contracts and API entrypoints

The canonical Python contracts are in contracts/*/types.py and contracts/configuration.py. Execution Context is in core/context/identity.py; ToolSpec and ToolRegistry are in core/execution/tools.py. Compatibility exports preserve `agentic_sdk.contracts` and `agentic_sdk.execution` imports.

| Contract | Responsibility | Main constraint |
|---|---|---|
| Context | Trusted tenant/agent identity and grants | Never derived from model output |
| LLM / Completion | Synchronous text and usage | Provider usage must be reported |
| DecisionModel / ModelReply | Async tool/final decision | Runner validates action and policy |
| Embedder / EmbeddingProfile | Vector representation | Entire profile must match the index |
| VectorStore / Document / Hit | Scoped retrieval | Current records do not encode document ACLs |
| RunObserver / Telemetry | Metadata events | Do not record conversation content |
| ToolSpec | Handler, schema, permission and prerequisites | Mutations require trusted approval |
| ConfigSource | Revisioned configuration loading port | No automatic hot-reload promise |

## HTTP surfaces

Use `/openapi.json` or `/docs` on each running API for its request/response schema. Pydantic request models are in services/contracts.py; service response shapes are implemented by their route functions.

- Agent host: health, configuration snapshot, run execution and scoped event history under `/v1/agents/{id}`.
- Registry: GET/PUT `/v1/registry/config`; writes require expected_revision and return 409 on conflict.
- Model gateway: POST `/v1/models/decide`; daily token reservation precedes provider calls.
- Tool gateway: POST `/v1/tools/{name}`; fixed AgentN allowlist, not arbitrary URL execution.
- Knowledge: POST `/v1/knowledge/documents`, GET `/v1/knowledge/jobs/{id}`, POST `/v1/knowledge/search`.
- Usage: GET `/v1/cost/usage`; tokens and reservations, not currency billing.

Identity comes from deployment credential bindings. Errors are scoped/sanitized. The [developer guide](developer-guide.md) describes consumption; [service READMEs](../services/README.md) locate implementations. v1 RAG and v2 agent configuration are distinct schemas; SDK release version 0.3.0 is separate from either schema version.

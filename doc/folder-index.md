# Maintained folder index

Maintained folders were reviewed for purpose, ownership, contents and documentation links. Generated/cache/private state folders are excluded below.

| Folder | Responsibility |
|---|---|
| [.](../README.md) | Project entrypoint, package metadata, license and default local RAG profile. |
| [.github](../.github/README.md) | Repository review and automation metadata. |
| [.github/workflows](../.github/workflows/README.md) | Hosted CI definitions; execution is separate from configuration. |
| [src/adapters](../src/adapters/README.md) | External-system implementations and compatibility exports. |
| [src/adapters/embeddings](../src/adapters/embeddings/README.md) | Compatible-provider vector generation and profile validation. |
| [src/adapters/graph](../src/adapters/graph/README.md) | Neo4j one-hop Graph RAG adapter. |
| [src/adapters/inference](../src/adapters/inference/README.md) | Operator-registered model calls. |
| [src/adapters/llm](../src/adapters/llm/README.md) | Generation-provider implementations grouped by API family. |
| [src/adapters/llm/anthropic](../src/adapters/llm/anthropic/README.md) | Native Messages API mapping. |
| [src/adapters/llm/azure_openai](../src/adapters/llm/azure_openai/README.md) | Azure v1 configuration guide using the shared compatible implementation. |
| [src/adapters/llm/openai_compatible](../src/adapters/llm/openai_compatible/README.md) | Approved client construction and chat completion mapping. |
| [src/adapters/observability](../src/adapters/observability/README.md) | Content-free OTel event export and the smaller RAG telemetry bridge. |
| [src/adapters/orchestration](../src/adapters/orchestration/README.md) | JSON decision adapter; no required agent framework. |
| [src/adapters/persistence](../src/adapters/persistence/README.md) | Scoped SQLite metadata and PostgreSQL platform state/reservations. |
| [src/adapters/retrieval](../src/adapters/retrieval/README.md) | Qdrant collection provisioning, writes and retrieval. |
| [src/adapters/sql](../src/adapters/sql/README.md) | Allowlisted read-only DB-API queries. |
| [src/adapters/tools](../src/adapters/tools/README.md) | Bounded HTTP, explicit MCP-session and n8n webhook integration. |
| [doc/assets](assets/README.md) | Front-page diagram of agent, SDK, and operator ownership. |
| [deployment/config](../deployment/config/README.md) | Public demo and placeholder configuration; no real endpoints/keys. |
| [src/contracts](../src/contracts/README.md) | Provider-neutral data types and compatibility exports. |
| [src/contracts/embeddings](../src/contracts/embeddings/README.md) | Embedding profile identity and vector validation contracts. |
| [src/contracts/graph](../src/contracts/graph/README.md) | One-hop Graph RAG expansion port. |
| [src/contracts/inference](../src/contracts/inference/README.md) | Registered-model prediction port. |
| [src/contracts/models](../src/contracts/models/README.md) | Synchronous model/completion port. |
| [src/contracts/orchestration](../src/contracts/orchestration/README.md) | Async model decisions, run results and observation port. |
| [src/contracts/retrieval](../src/contracts/retrieval/README.md) | Documents, hits and vector-store port. |
| [src/contracts/sql](../src/contracts/sql/README.md) | Read-only allowlisted table port. |
| [src/contracts/telemetry](../src/contracts/telemetry/README.md) | Content-free telemetry port. |
| [src/contracts/tools](../src/contracts/tools/README.md) | Synchronous tool/idempotency contract. |
| [src/core](../src/core/README.md) | Reusable framework-neutral behavior. |
| [src/core/context](../src/core/context/README.md) | Trusted execution identity and permission guard. |
| [src/core/execution](../src/core/execution/README.md) | Registered tool schemas, permissions, prerequisites and approval checks. |
| [src/core/harness](../src/core/harness/README.md) | Async model/tool runner and synchronous RAG example use case. |
| [src/core/policies](../src/core/policies/README.md) | Validated request-level limits. |
| [deployment/earlier](../deployment/earlier/README.md) | Earlier reference infrastructure; not the supported full profile. |
| [deployment/earlier/grafana](../deployment/earlier/grafana/README.md) | Earlier importable dashboard reference. |
| [deployment/earlier/helm](../deployment/earlier/helm/README.md) | Draft values only; no installable Helm chart. |
| [deployment/earlier/otel](../deployment/earlier/otel/README.md) | Earlier optional collector reference. |
| [deployment/earlier/postgres](../deployment/earlier/postgres/README.md) | Earlier illustrative schema; not current platform migrations. |
| [deployment](../deployment/README.md) | Supported local profiles and operating runbooks. |
| [deployment/full](../deployment/full/README.md) | Ten-container local platform and monitoring profile. |
| [deployment/full/dashboards](../deployment/full/dashboards/README.md) | Provisioned operator dashboard definitions. |
| [deployment/full/grafana](../deployment/full/grafana/README.md) | Datasource and dashboard-provider provisioning. |
| [deployment/full/grafana/dashboards](../deployment/full/grafana/dashboards/README.md) | Provider configuration selecting mounted dashboard JSON. |
| [deployment/full/grafana/datasources](../deployment/full/grafana/datasources/README.md) | Stable Grafana datasource names/UIDs. |
| [deployment/local](../deployment/local/README.md) | Smaller AgentN-only profile; shares port 8010 with full profile. |
| [doc/developer-standards](developer-standards/README.md) | Canonical engineering skill and supporting assets. |
| [doc/developer-standards/agent-developer](developer-standards/agent-developer/README.md) | Skill entrypoint and usage boundaries. |
| [doc/developer-standards/agent-developer/agents](developer-standards/agent-developer/agents/README.md) | Skill UI metadata and invocation policy. |
| [doc/developer-standards/agent-developer/assets](developer-standards/agent-developer/assets/README.md) | Illustrative consumer/config layout assets. |
| [doc/developer-standards/agent-developer/assets/agent-template](developer-standards/agent-developer/assets/agent-template/README.md) | Layout illustration; SDK init is the runnable generator. |
| [doc/developer-standards/agent-developer/assets/agent-template/capabilities](developer-standards/agent-developer/assets/agent-template/capabilities/README.md) | Consumer capabilities layout guide; not platform runtime code. |
| [doc/developer-standards/agent-developer/assets/agent-template/deployment](developer-standards/agent-developer/assets/agent-template/deployment/README.md) | Consumer deployment layout guide; not platform runtime code. |
| [doc/developer-standards/agent-developer/assets/agent-template/domain](developer-standards/agent-developer/assets/agent-template/domain/README.md) | Consumer domain layout guide; not platform runtime code. |
| [doc/developer-standards/agent-developer/assets/agent-template/instructions](developer-standards/agent-developer/assets/agent-template/instructions/README.md) | Consumer instructions layout guide; not platform runtime code. |
| [doc/developer-standards/agent-developer/assets/agent-template/tests](developer-standards/agent-developer/assets/agent-template/tests/README.md) | Consumer tests layout guide; not platform runtime code. |
| [doc/developer-standards/agent-developer/assets/agent-template/tests/evaluations](developer-standards/agent-developer/assets/agent-template/tests/evaluations/README.md) | Consumer evaluations layout guide; not platform runtime code. |
| [doc/developer-standards/agent-developer/assets/agent-template/tests/unit](developer-standards/agent-developer/assets/agent-template/tests/unit/README.md) | Consumer unit layout guide; not platform runtime code. |
| [doc/developer-standards/agent-developer/assets/config-templates](developer-standards/agent-developer/assets/config-templates/README.md) | Public local/compatible configuration examples. |
| [doc/developer-standards/agent-developer/references](developer-standards/agent-developer/references/README.md) | Focused architecture, provider, security and operational guidance. |
| [doc/developer-standards/agent-developer/scripts](developer-standards/agent-developer/scripts/README.md) | Explicit-path manifest/config/contract validators. |
| [docs](README.md) | Current implementation guides, references and historical baseline. |
| [doc/adr](adr/README.md) | Numbered architecture decisions with unique IDs. |
| [tests/evaluation](../tests/evaluation/README.md) | Offline RAG smoke evaluation; separate from real answer-quality certification. |
| [examples](../examples/README.md) | Insight reference agent and the smaller RAG script. |
| [examples/insight_agent](../examples/insight_agent/README.md) | Reference business agent: foundation model, perception, planning, memory, action, learning, communication. |
| [examples/insight_agent/host](../examples/insight_agent/host/README.md) | Question page, operator API, settings, and traces. |
| [examples/insight_agent/stack](../examples/insight_agent/stack/README.md) | Compose file, images, and sample data for the insight agent. |
| [examples/insight_agent/stack/fixtures](../examples/insight_agent/stack/fixtures/README.md) | Sample metrics table loaded on first Postgres start. |
| [examples/insight_agent/stack/observability](../examples/insight_agent/stack/observability/README.md) | Collector config for the insight stack. |
| [examples/insight_agent/stack/site](../examples/insight_agent/stack/site/README.md) | Allowlisted public page the reference agent may fetch. |
| [examples/insight_agent/stack/ui](../examples/insight_agent/stack/ui/README.md) | Operator console image for the insight stack. |
| [examples/sells_agent](../examples/sells_agent/README.md) | Second agent: the same seven components, answering one order question. |
| [examples/sells_agent/host](../examples/sells_agent/host/README.md) | In-process shell and content-free trace. No HTTP page. |
| [deployment/schemas](../deployment/schemas/README.md) | v1 RAG and v2 project JSON schemas. |
| [deployment/scripts](../deployment/scripts/README.md) | Validation, full-stack acceptance and local lifecycle helpers. |
| [src/sdk](../src/sdk/README.md) | Python consumer-facing configuration/CLI/client package. |
| [src/sdk/python](../src/sdk/python/README.md) | Developer commands, composition and remote service clients. |
| [src/services](../src/services/README.md) | Local API composition and shared bounded input models. |
| [src/services/agent_host](../src/services/agent_host/README.md) | Generic authenticated agent API with concurrency control. |
| [src/services/agent_registry](../src/services/agent_registry/README.md) | Immutable configuration publication and revision lookup. |
| [src/services/knowledge_service](../src/services/knowledge_service/README.md) | Ingestion submission, job state, retrieval and worker. |
| [src/services/model_gateway](../src/services/model_gateway/README.md) | Decision forwarding, token reservations and usage queries. |
| [src/services/operator_ui](../src/services/operator_ui/README.md) | Loopback screens for agents, configuration, connectors and runs. |
| [src/services/tool_gateway](../src/services/tool_gateway/README.md) | Fixed AgentN tool allowlist and backend forwarding. |
| [source](../src/README.md) | SDK source: contracts, core, adapters, services, the developer client, and compatibility imports. |
| [src/agentic_sdk](../src/agentic_sdk/README.md) | Compatibility facade; no copied runtime. |
| [doc/templates](templates/README.md) | Illustrative adapter contribution template. |
| [tests](../tests/README.md) | Discoverable SDK unittest modules. |
| [tests/compatibility](../tests/compatibility/README.md) | Reading guide to public import and RAG compatibility tests. |
| [tests/contract](../tests/contract/README.md) | Reading guide to parent contract tests. |
| [tests/integration](../tests/integration/README.md) | Reading guide to optional and full-stack tests. |

## Excluded generated and private state

`.git`, `.venv`, `__pycache__`, `.ruff_cache`, `.pytest_cache`, `build`, `dist`, `*.egg-info`, `.agentic` and `.test-state` are not maintained source folders. Environment secrets are never included in the index. Build artifacts are regenerated; runtime volumes/credentials must not be treated as disposable source.

## Keeping the structure current

Run `python deployment/scripts/check_repository.py`, `ruff check .` and `ruff format --check .`. The structural checker verifies README coverage, documented public Python definitions, local Markdown links, package-directory mappings and unique ADR IDs. It does not establish that documentation is factually complete or that external services work.

# Maintained folder index

All 75 maintained folders were reviewed for purpose, ownership, contents and documentation links. Generated/cache/private state folders are excluded below.

| Folder | Responsibility |
|---|---|
| [.](../README.md) | Project entrypoint, package metadata, license and default local RAG profile. |
| [.github](../.github/README.md) | Repository review and automation metadata. |
| [.github/workflows](../.github/workflows/README.md) | Hosted CI definitions; execution is separate from configuration. |
| [adapters](../adapters/README.md) | External-system implementations and compatibility exports. |
| [adapters/embeddings](../adapters/embeddings/README.md) | Compatible-provider vector generation and profile validation. |
| [adapters/llm](../adapters/llm/README.md) | Generation-provider implementations grouped by API family. |
| [adapters/llm/anthropic](../adapters/llm/anthropic/README.md) | Native Messages API mapping. |
| [adapters/llm/azure_openai](../adapters/llm/azure_openai/README.md) | Azure v1 configuration guide using the shared compatible implementation. |
| [adapters/llm/openai_compatible](../adapters/llm/openai_compatible/README.md) | Approved client construction and chat completion mapping. |
| [adapters/observability](../adapters/observability/README.md) | Content-free OTel event export and the smaller RAG telemetry bridge. |
| [adapters/orchestration](../adapters/orchestration/README.md) | JSON decision adapter; no required agent framework. |
| [adapters/persistence](../adapters/persistence/README.md) | Scoped SQLite metadata and PostgreSQL platform state/reservations. |
| [adapters/retrieval](../adapters/retrieval/README.md) | Qdrant collection provisioning, writes and retrieval. |
| [adapters/tools](../adapters/tools/README.md) | Bounded HTTP, explicit MCP-session and n8n webhook integration. |
| [config](../config/README.md) | Public demo and placeholder configuration; no real endpoints/keys. |
| [contracts](../contracts/README.md) | Provider-neutral data types and compatibility exports. |
| [contracts/embeddings](../contracts/embeddings/README.md) | Embedding profile identity and vector validation contracts. |
| [contracts/models](../contracts/models/README.md) | Synchronous model/completion port. |
| [contracts/orchestration](../contracts/orchestration/README.md) | Async model decisions, run results and observation port. |
| [contracts/retrieval](../contracts/retrieval/README.md) | Documents, hits and vector-store port. |
| [contracts/telemetry](../contracts/telemetry/README.md) | Content-free telemetry port. |
| [contracts/tools](../contracts/tools/README.md) | Synchronous tool/idempotency contract. |
| [core](../core/README.md) | Reusable framework-neutral behavior. |
| [core/context](../core/context/README.md) | Trusted execution identity and permission guard. |
| [core/execution](../core/execution/README.md) | Registered tool schemas, permissions, prerequisites and approval checks. |
| [core/harness](../core/harness/README.md) | Async model/tool runner and synchronous RAG example use case. |
| [core/policies](../core/policies/README.md) | Validated request-level limits. |
| [deploy](../deploy/README.md) | Earlier reference infrastructure; not the supported full profile. |
| [deploy/grafana](../deploy/grafana/README.md) | Earlier importable dashboard reference. |
| [deploy/helm](../deploy/helm/README.md) | Draft values only; no installable Helm chart. |
| [deploy/otel](../deploy/otel/README.md) | Earlier optional collector reference. |
| [deploy/postgres](../deploy/postgres/README.md) | Earlier illustrative schema; not current platform migrations. |
| [deployment](../deployment/README.md) | Supported local profiles and operating runbooks. |
| [deployment/full](../deployment/full/README.md) | Ten-container local platform and monitoring profile. |
| [deployment/full/dashboards](../deployment/full/dashboards/README.md) | Provisioned operator dashboard definitions. |
| [deployment/full/grafana](../deployment/full/grafana/README.md) | Datasource and dashboard-provider provisioning. |
| [deployment/full/grafana/dashboards](../deployment/full/grafana/dashboards/README.md) | Provider configuration selecting mounted dashboard JSON. |
| [deployment/full/grafana/datasources](../deployment/full/grafana/datasources/README.md) | Stable Grafana datasource names/UIDs. |
| [deployment/local](../deployment/local/README.md) | Smaller AgentN-only profile; shares port 8010 with full profile. |
| [developer-standards](../developer-standards/README.md) | Canonical engineering skill and supporting assets. |
| [developer-standards/gcpl-agent-developer](../developer-standards/gcpl-agent-developer/README.md) | Skill entrypoint and usage boundaries. |
| [developer-standards/gcpl-agent-developer/agents](../developer-standards/gcpl-agent-developer/agents/README.md) | Skill UI metadata and invocation policy. |
| [developer-standards/gcpl-agent-developer/assets](../developer-standards/gcpl-agent-developer/assets/README.md) | Illustrative consumer/config layout assets. |
| [developer-standards/gcpl-agent-developer/assets/agent-template](../developer-standards/gcpl-agent-developer/assets/agent-template/README.md) | Layout illustration; SDK init is the runnable generator. |
| [developer-standards/gcpl-agent-developer/assets/agent-template/capabilities](../developer-standards/gcpl-agent-developer/assets/agent-template/capabilities/README.md) | Consumer capabilities layout guide; not platform runtime code. |
| [developer-standards/gcpl-agent-developer/assets/agent-template/deployment](../developer-standards/gcpl-agent-developer/assets/agent-template/deployment/README.md) | Consumer deployment layout guide; not platform runtime code. |
| [developer-standards/gcpl-agent-developer/assets/agent-template/domain](../developer-standards/gcpl-agent-developer/assets/agent-template/domain/README.md) | Consumer domain layout guide; not platform runtime code. |
| [developer-standards/gcpl-agent-developer/assets/agent-template/instructions](../developer-standards/gcpl-agent-developer/assets/agent-template/instructions/README.md) | Consumer instructions layout guide; not platform runtime code. |
| [developer-standards/gcpl-agent-developer/assets/agent-template/tests](../developer-standards/gcpl-agent-developer/assets/agent-template/tests/README.md) | Consumer tests layout guide; not platform runtime code. |
| [developer-standards/gcpl-agent-developer/assets/agent-template/tests/evaluations](../developer-standards/gcpl-agent-developer/assets/agent-template/tests/evaluations/README.md) | Consumer evaluations layout guide; not platform runtime code. |
| [developer-standards/gcpl-agent-developer/assets/agent-template/tests/unit](../developer-standards/gcpl-agent-developer/assets/agent-template/tests/unit/README.md) | Consumer unit layout guide; not platform runtime code. |
| [developer-standards/gcpl-agent-developer/assets/config-templates](../developer-standards/gcpl-agent-developer/assets/config-templates/README.md) | Public local/compatible configuration examples. |
| [developer-standards/gcpl-agent-developer/references](../developer-standards/gcpl-agent-developer/references/README.md) | Focused architecture, provider, security and operational guidance. |
| [developer-standards/gcpl-agent-developer/scripts](../developer-standards/gcpl-agent-developer/scripts/README.md) | Explicit-path manifest/config/contract validators. |
| [docs](README.md) | Current implementation guides, references and historical baseline. |
| [docs/adr](adr/README.md) | Numbered architecture decisions with unique IDs. |
| [evaluation](../evaluation/README.md) | Offline RAG smoke evaluation; separate from real answer-quality certification. |
| [examples](../examples/README.md) | Executable minimal RAG example. |
| [schemas](../schemas/README.md) | v1 RAG and v2 project JSON schemas. |
| [scripts](../scripts/README.md) | Validation, full-stack acceptance and local lifecycle helpers. |
| [sdk](../sdk/README.md) | Python consumer-facing configuration/CLI/client package. |
| [sdk/python](../sdk/python/README.md) | Developer commands, composition and remote service clients. |
| [services](../services/README.md) | Local API composition and shared bounded input models. |
| [services/agent_host](../services/agent_host/README.md) | Generic authenticated agent API with concurrency control. |
| [services/agent_registry](../services/agent_registry/README.md) | Immutable configuration publication and revision lookup. |
| [services/knowledge_service](../services/knowledge_service/README.md) | Ingestion submission, job state, retrieval and worker. |
| [services/model_gateway](../services/model_gateway/README.md) | Decision forwarding, token reservations and usage queries. |
| [services/tool_gateway](../services/tool_gateway/README.md) | Fixed AgentN tool allowlist and backend forwarding. |
| [src](../src/README.md) | Stable legacy source/import namespace. |
| [src/agentic_sdk](../src/agentic_sdk/README.md) | Compatibility facade; no copied runtime. |
| [templates](../templates/README.md) | Illustrative adapter contribution template. |
| [tests](../tests/README.md) | Discoverable SDK unittest modules. |
| [tests/compatibility](../tests/compatibility/README.md) | Reading guide to public import and RAG compatibility tests. |
| [tests/contract](../tests/contract/README.md) | Reading guide to parent contract tests. |
| [tests/integration](../tests/integration/README.md) | Reading guide to optional and full-stack tests. |

## Excluded generated and private state

`.git`, `.venv`, `__pycache__`, `.ruff_cache`, `.pytest_cache`, `build`, `dist`, `*.egg-info`, `.agentic` and `.test-state` are not maintained source folders. Environment secrets are never included in the index. Build artifacts are regenerated; runtime volumes/credentials must not be treated as disposable source.

## Keeping the structure current

Run `python scripts/check_repository.py`, `ruff check .` and `ruff format --check .`. The structural checker verifies README coverage, documented public Python definitions, local Markdown links, package-directory mappings and unique ADR IDs. It does not establish that documentation is factually complete or that external services work.

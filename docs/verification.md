# Verification - SDK 0.3.0, 2026-10-18

## Passed

- 39 SDK tests: core/RAG, execution, transport, providers, schema, generated-project safety, native Anthropic mapping, MCP result/error mapping, n8n approval guard, in-memory Qdrant and OTel.
- 5 AgentN tests: embedded execution, scope/auth, redacted persistence, remote client and mocked REST contracts.
- Fresh independent agent generated, installed, validated, executed and evaluated successfully.
- SDK wheel agentic_foundation_sdk-0.3.0-py3-none-any.whl built; the AgentN vendor wheel was refreshed.
- Ten-container local Docker stack started; platform and AgentN health checks passed.
- Platform acceptance passed: anonymous/other-agent access denial, immutable registry revisions and stale-write conflict, idempotent ingestion, worker completion, Qdrant retrieval isolation, hosted AgentN model/tool execution and PostgreSQL token accounting.
- Registry, Qdrant knowledge and usage records survived application image rebuild/restart.
- Twenty concurrent reservation attempts admitted exactly five within a 50-token test budget; all excess attempts were rejected. Synthetic test ledger row removed afterward.
- Actual Prometheus, Loki and Tempo queries confirmed metrics, logs and traces arrived.
- Platform, worker and AgentN run with read-only root filesystems; state uses named volumes.
- Local credential file is ignored by Git and Docker build contexts.

## Limits of the evidence

Default model/backend/embeddings are synthetic. No paid inference, real AgentN backend, OAuth flow, external MCP session or n8n workflow was invoked. Native adapters have contract tests only. Dependency ranges and image tags are not release lockfiles or vulnerability certification. No load test, backup/restore drill, tenant-facing monitoring authorization or multi-node failover test was performed.

Telemetry spans represent content-free events, not a fully propagated distributed request trace across every service. Monitoring is operator-only. API bindings use static per-agent credentials, not production user federation. See release-gates.md.

The full local stack remains running at AgentN :8010, platform :8020 and Grafana :3002 on loopback. An earlier minimal AgentN container was stopped with its volume preserved. Unrelated pre-existing monitoring containers were not changed.

## Architecture source reorganization

Implementation moved into core, contracts, adapters, services and sdk/python with explicit setuptools mappings. Public SDK imports remain re-exports of the same classes. Passed 39 SDK tests and 5 AgentN tests; clean wheel/source builds and full Docker API acceptance passed. See source-layout.md.

## Documentation and organization audit

Reviewed all 75 maintained directories; generated caches, build output and private runtime state are excluded. Each directory has a README with ownership and direct-child navigation. All 130 public definitions in the canonical implementation have docstrings. Ruff lint and format checks, local Markdown links, package mappings and unique ADR identifiers pass. The 39 SDK and 5 AgentN tests pass after import cleanup. The minimal example, offline retrieval evaluation (3/3) and all three configuration fixtures pass. CI now enforces style and repository documentation checks. This is not a production security or live-provider certification.

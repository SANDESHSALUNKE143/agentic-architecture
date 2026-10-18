# Changelog

## 0.3.0 - Full local platform and developer workflow

- Reviewed all maintained folders, documented canonical APIs, added a folder inventory and CI documentation/style checks, corrected stale architecture and developer-skill guidance, and removed orphan documentation.

- Canonical Python implementation now lives directly in architecture folders; compatible SDK imports are maintained through package mappings and re-exports. Docker builds and source distributions include all mapped source roots.

- Runnable project generator and shared validate/run/serve/evaluate commands.
- PostgreSQL revisioned registry, durable ingestion jobs and atomic daily token reservation ledger.
- Model/tool gateway APIs and isolated Qdrant knowledge search; independent worker.
- Hosted AgentN composition using the shared SDK; external instruction files loaded by its CLI/API.
- OTLP content-free events with local Collector, Prometheus, Loki, Tempo and provisioned Grafana dashboard.
- Native Anthropic, explicit MCP-session tool and mutation-gated n8n webhook adapters.
- Full Docker start/test/stop workflow, persisted local credentials, acceptance tests and developer runbook.
- Stronger endpoint validation and queue backpressure. Public verification distinguishes contract tests from live integration.

## 0.2.0 - Reusable execution and independent AgentN

Added bounded async model/tool harness, tool prerequisites and approval gates, REST transport, project configuration, scoped metadata, optional agent HTTP API and remote SDK client. Created the separate AgentN consumer. Added architecture section guides, canonical developer skill and local Docker acceptance workflow.

## 0.1.0 - Initial architecture and RAG baseline

Typed model/embedding/vector contracts, local RAG demonstration, adapter registry, compatible providers, Qdrant/OTel adapters, design documents and prototype infrastructure.

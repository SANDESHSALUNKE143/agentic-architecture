# Release scope and remaining gates

SDK 0.3.0 adds a runnable developer CLI, combined local platform APIs, durable ingestion worker, PostgreSQL registry/token ledger, Qdrant knowledge, hosted AgentN composition, and OTLP metrics/logs/traces with a full local Docker stack.

Local usability does not imply completion of every long-term architecture feature. Remaining work: production OIDC/per-user token delegation; multi-node coordination/HA; currency accounting and billing reconciliation; knowledge deletion/ACL-change lifecycle; general file connectors; live certification of Anthropic/MCP/n8n; custom visual configuration portal; streaming/conversation checkpoints; production Helm; pinned/scanned release artifacts; live provider and existing-backend certification; load/backup/restore/security testing.

The local APIs run with deployment-configured opaque credentials. Monitoring is operator-only, not tenant-query-isolated. Demo reasoning and hash embeddings are synthetic. No claim of production readiness or universal framework/provider certification is made.

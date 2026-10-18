# Deployment

Use deployment/full/compose.yaml and scripts/full-platform.ps1 for full local acceptance. Ten containers cover AgentN, platform APIs, worker, PostgreSQL, Qdrant and the telemetry stack. Use deployment/local only for the smaller alternative, not concurrently on port 8010.

The Python SDK wheel is the reuse boundary. Independent agent Dockerfiles install the pinned wheel. Local secrets live in ignored files or environment/secret stores. Shared telemetry is operator-only. Before Linux remote access, configure TLS/identity and perform live-provider, backup/restore, load and image security validation. Production Helm and HA remain rollout work.

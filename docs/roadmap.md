# Delivery roadmap and acceptance gates

> Phase-one design reference. For current executable behavior and the separate consuming agent, read [the current implementation map](implementation-map.md). Features described as planned here are not automatically implemented by the new agent API.

This order keeps each increment runnable without requiring every hosted component.

| Phase | Deliverable | Exit criteria |
|---|---|---|
| 0 — this repository | Local SDK, contract adapters, architecture | Offline tests/example/evaluation; explicit limitations |
| 1 — integration certification | Provider, Qdrant, PostgreSQL, OTel test environments; dependency locks | Live synthetic-data tests, container startup, timeouts, scoped persistence, telemetry export and restore exercise |
| 2 — authenticated platform | Config/registry APIs and portal, workload identity, versioned hosted schema | Immutable revisions, stale-write conflict, scope denial, secret refs, cache expiry/rollback tests |
| 3 — shared knowledge | Jobs/workers, source manifests and ACLs, object store, batched ingestion | 100k-chunk load test, idempotency, ACL updates/deletes, profile migration and recovery |
| 4 — governed execution | Gateway, durable cost ledger, REST/MCP/n8n adapters | Atomic quotas under concurrent load, ambiguous-call reconciliation, tool policy and replay tests |
| 5 — operations | Secured full telemetry stack, dashboards, SLO alerts, Helm chart | Ingest/query isolation tests, outage drills, multi-node deployment and rollback |

Track each service and its contract as an issue with owner, acceptance tests and operational runbook. Do not label a design document or empty endpoint as implemented. Publish separate SDK and service versions with a compatibility matrix. A framework integration is optional and may be added at any phase after a measured need.

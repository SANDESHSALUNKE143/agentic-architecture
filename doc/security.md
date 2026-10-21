# Security boundaries

This prototype is for trusted local development. Context is constructed by application code and is forgeable by that code. SDK guards prevent accidental scope leaks, but cannot isolate malicious agents in the same process. MemoryStore only isolates whole agents; document/user ACLs are not implemented.

## Roles and enforcement

| Role | Scope | Permissions |
|---|---|---|
| Agent workload | One tenant/agent | invoke, knowledge read, own config read, approved tools |
| Ingestion workload | One src/agent | knowledge write/delete; no config publish |
| Agent maintainer | Owned agents | config draft, evaluation, own telemetry view |
| Platform operator | Assigned environment | provisioning, routing, backups; audited elevation |
| Auditor | Approved scopes | redacted audit read; no content/model credentials |

Map roles to permissions at a verified identity boundary. Default deny. Use short-lived workload tokens and audience restrictions. Provision separate DB roles, collection access proxies and telemetry credentials. Never trust user-supplied tenant headers. Validate scope before embedding/model calls to avoid both leakage and unauthorized cost. Direct SDK mode requires a trusted process; multi-tenant services require separate authenticated enforcement.

For PostgreSQL use a non-owner NOSUPERUSER NOBYPASSRLS application role, FORCE ROW LEVEL SECURITY, transaction-local scope derived by the gateway and separate migration credentials. Pool checkout must reset state; test cross-request leakage. The sample superuser is only bootstrap, and RLS does not protect against it. Qdrant collection naming is not an ACL; use a trusted knowledge service or supported collection-scoped credentials and network isolation.

## Threat controls

| Threat | Required control | Prototype status |
|---|---|---|
| Prompt injection in documents/tools | Untrusted-content boundaries, tool policy independent of model, evaluation | Prompt instruction only; not a defense guarantee |
| SSRF and exfiltration | Fixed endpoint allowlists, DNS/IP validation, deny metadata/private networks unless specifically required, restricted egress | HTTPS syntax check only; full SSRF protection planned |
| Secret leakage | Vault references, short-lived identity, metadata-only logs, secret scanning | Environment secrets and telemetry allowlist |
| Cross-agent access | Verified identity + server-side ACLs + negative tests | Cooperative in-process tests only |
| Malicious files | Size/type checks, malware scanning, parser sandbox | Prechunked text only |
| Supply-chain compromise | Dependency lockfiles, SBOM, vulnerability/license scans, reviewed digests, signed releases | Version ranges/reference tags; release gates planned |
| Tool replay/duplicate writes | Signed requests, expiry and durable idempotency ledger | Contract only |
| Resource exhaustion | Bounded payload/context, token caps, deadlines, concurrency and rate limits | Some local bounds; no server limiter |

No prompts, retrieved passages, completions, credentials or user IDs should be emitted by default. IDs and event names must come from bounded trusted registries. Telemetry metadata can still be sensitive. Redact before egress, not only at dashboards. Enable TLS/mTLS on all remote hops, encrypt disks/backups and define deletion/retention policies. Internal network placement alone is not authentication.

Before external exposure: add OIDC/workload auth, gateway enforcement, scoped data roles, TLS, egress policy, durable quotas, log redaction tests and incident response. Rotate compromised keys, revoke workload identity, stop affected routes, preserve redacted audit evidence and reconcile pending charges. Report vulnerabilities privately using the hosting provider's private vulnerability reporting when configured; do not put secrets in public issues.

# ADR 009: Combined local APIs with separate worker

Status: accepted for the local development release.

Use one API process for registry, model/tool gateways and knowledge endpoints, plus a dedicated durable ingestion worker. This keeps the 8-vCPU/32-GB prototype operable while preserving explicit route/contracts and independent SDK adapters. PostgreSQL owns revisions, jobs and reservation accounting; Qdrant owns embeddings. The consumer still owns domain policy.

Consequences: service boundaries are logical rather than separate scaling units; API blocking calls use FastAPI's thread pool; job processing is intentionally bounded and single-worker by default. Tokens bind fixed tenant/agent scopes. Monitoring is a shared operator plane. Live backend token delegation, independent service scaling and production federation require later work. No new copy of the execution harness is introduced.

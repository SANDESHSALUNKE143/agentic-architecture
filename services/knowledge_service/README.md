# Knowledge service

POST /v1/knowledge/documents, GET /v1/knowledge/jobs/{id}, POST /v1/knowledge/search. PostgreSQL jobs and separate worker; agent/profile-specific Qdrant collections. Identical submissions reuse a job. Versioned content is append-only; deletion and document ACL lifecycle are not implemented.

[Implementation](../app.py) - [Local runbook](../../deployment/full/README.md) - [Developer guide](../../docs/developer-guide.md).

Validation: scripts/test_full_platform.py against the running stack. These APIs share one local process; independent service scaling is future work.


## Folder contents

Ingestion submission, job state, retrieval and worker.

- [components.py](components.py): Operator-configured PostgreSQL, embedding and Qdrant composition.
- [routes.py](routes.py): Scoped ingestion-job submission, status lookup and vector retrieval endpoints.
- [worker.py](worker.py): Durable PostgreSQL job processing with idempotent Qdrant writes.

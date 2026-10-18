# Agent configuration registry

GET/PUT /v1/registry/config. Immutable PostgreSQL revisions with expected_revision conflict control and credential-scoped identity. Publishing does not hot-reload agents. Rollback publishes a prior configuration as a new revision.

[Implementation](../app.py) - [Local runbook](../../deployment/full/README.md) - [Developer guide](../../docs/developer-guide.md).

Validation: scripts/test_full_platform.py against the running stack. These APIs share one local process; independent service scaling is future work.


## Folder contents

Immutable configuration publication and revision lookup.

- [routes.py](routes.py): Immutable configuration publication and scoped revision lookup.

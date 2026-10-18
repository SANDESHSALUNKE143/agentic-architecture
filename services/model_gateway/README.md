# Model gateway

POST /v1/models/decide and GET /v1/cost/usage. Per-agent credentials, bounded context, conservative daily reservations and reported usage. Demo and compatible providers; currency billing remains outside this implementation. Native Anthropic is available through SDK composition.

[Implementation](../app.py) - [Local runbook](../../deployment/full/README.md) - [Developer guide](../../docs/developer-guide.md).

Validation: scripts/test_full_platform.py against the running stack. These APIs share one local process; independent service scaling is future work.


## Folder contents

Decision forwarding, token reservations and usage queries.

- [routes.py](routes.py): Model admission control, decision forwarding and durable token usage queries.

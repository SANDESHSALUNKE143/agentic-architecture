# 04. Platform services

Implemented local service boundaries: revisioned configuration registry, bounded model gateway with durable token reservations, allowlisted read-only tool gateway, knowledge submission/search API and separate PostgreSQL-backed ingestion worker. They are hosted in one FastAPI process plus a worker for efficient local deployment. An agent does not import these services into its decide loop. The operator image starts the operator UI and calls the agent over HTTP.

Canonical implementation: [hosted.py](app.py). Agent hosting remains in [service.py](agent_host/api.py). Start with the [full-stack runbook](../../deployment/full/README.md) and [developer guide](../../doc/developer-guide.md).

Read [model gateway](model_gateway/README.md), [tool gateway](tool_gateway/README.md), [knowledge service](knowledge_service/README.md), and [registry](agent_registry/README.md). See [remaining release gates](../../doc/release-gates.md) before production use.


## Folder contents

Local API composition and shared bounded input models.

- [agent_host/](agent_host/README.md): Generic authenticated agent API with concurrency control.
- [agent_registry/](agent_registry/README.md): Immutable configuration publication and revision lookup.
- [app.py](app.py): Local platform composition and credential binding; route behavior lives in service modules.
- [contracts.py](contracts.py): Closed, bounded HTTP input models shared by platform routes.
- [knowledge_service/](knowledge_service/README.md): Ingestion submission, job state, retrieval and worker.
- [model_gateway/](model_gateway/README.md): Decision forwarding, token reservations and usage queries.
- [operator_ui/](operator_ui/README.md): Loopback screens for agents, configuration, connectors and runs.
- [tool_gateway/](tool_gateway/README.md): Fixed AgentN tool allowlist and backend forwarding.

# Public SDK compatibility facade

These modules preserve existing agentic_sdk imports. Canonical implementation lives in [contracts](../contracts/README.md), [core](../core/README.md), [adapters](../adapters/README.md), [services](../services/README.md), and [sdk/python](../sdk/python/README.md). Do not add a second implementation here. See [source layout](../../doc/source-layout.md).


## Folder contents

Compatibility facade; no copied runtime.

- [config.py](config.py): Compatibility imports; implementation is in sdk/python/config.py.
- [decision_models.py](decision_models.py): Compatibility imports; implementation is in adapters/orchestration/json_decision.py.
- [developer.py](developer.py): Compatibility imports; implementation is in sdk/python/developer.py.
- [execution.py](execution.py): Backward-compatible public execution imports; no copied implementations.
- [hosted.py](hosted.py): Compatibility entrypoints for platform API and worker.
- [hosted_client.py](hosted_client.py): Compatibility imports; implementation is in sdk/python/hosted_client.py.
- [http.py](http.py): Compatibility imports; implementation is in adapters/tools/http.py.
- [observation.py](observation.py): Compatibility imports; implementation is in adapters/observability/events.py.
- [project.py](project.py): Compatibility imports; implementation is in sdk/python/project.py.
- [registry.py](registry.py): Compatibility imports; implementation is in adapters/registry.py.
- [remote_agent.py](remote_agent.py): Compatibility imports; implementation is in sdk/python/remote_agent.py.
- [run_store.py](run_store.py): Compatibility imports; implementation is in adapters/persistence/sqlite.py.
- [runtime.py](runtime.py): Compatibility imports; implementation is in core/harness/rag.py.
- [service.py](service.py): Compatibility imports; implementation is in services/agent_host/api.py.

# 03. Adapters

Translate external systems into stable SDK interfaces. Keep vendor details out of core.

**Status:** Local/compatible-model/Qdrant/OTel adapters exist; individual integrations vary.

## Implementation

[Canonical source / guide](llm/openai_compatible/completion.py). Python in this section is installed under the agentic_sdk package namespace. These folders now contain the canonical implementation, packaged under agentic_sdk.

## Read in order

1. [Language model adapters](llm/README.md)
2. [Embedding adapters](embeddings/README.md)
3. [Retrieval adapters](retrieval/README.md)
4. [Framework integration adapters](orchestration/README.md)
5. [Observability adapters](observability/README.md)
6. [Persistence adapters](persistence/README.md)

## Change rule

Change the linked implementation and its behavior tests together. Record contract changes and distinguish implemented code from planned services. Agent-specific rules belong in consumer repositories.

[Back to the platform reading order](../../00-START-HERE.md).


## Folder contents

External-system implementations and compatibility exports.

- [anthropic.py](anthropic.py): Compatibility exports.
- [embeddings/](embeddings/README.md): Compatible-provider vector generation and profile validation.
- [graph/](graph/README.md): Neo4j one-hop Graph RAG adapter.
- [inference/](inference/README.md): Operator-registered model calls.
- [integrations.py](integrations.py): Compatibility exports.
- [llm/](llm/README.md): Generation-provider implementations grouped by API family.
- [local.py](local.py): Deterministic demonstration adapters; not production semantic models.
- [observability/](observability/README.md): Content-free OTel event export and the smaller RAG telemetry bridge.
- [orchestration/](orchestration/README.md): JSON decision adapter; no required agent framework.
- [otel.py](otel.py): Compatibility exports.
- [persistence/](persistence/README.md): Scoped SQLite metadata and PostgreSQL platform state/reservations.
- [providers.py](providers.py): Compatibility exports for provider consumers.
- [qdrant.py](qdrant.py): Compatibility exports.
- [registry.py](registry.py): Explicit registration; configuration never imports arbitrary code.
- [retrieval/](retrieval/README.md): Qdrant collection provisioning, writes and retrieval.
- [sql/](sql/README.md): Allowlisted read-only DB-API queries.
- [tools/](tools/README.md): Bounded HTTP, explicit MCP-session and n8n webhook integration.

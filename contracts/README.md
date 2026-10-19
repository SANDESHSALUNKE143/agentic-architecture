# 01. Contracts

Provider-neutral interfaces and compatibility rules. Start here before changing implementations.

**Status:** Implemented contracts; some future service contracts remain designs.

## Implementation

[Canonical source / guide](__init__.py). Python in this section is installed under the agentic_sdk package namespace. These folders now contain the canonical implementation, packaged under agentic_sdk.

## Read in order

1. [Model contracts](models/README.md)
2. [Embedding contracts](embeddings/README.md)
3. [Retrieval contracts](retrieval/README.md)
4. [Orchestration contracts](orchestration/README.md)
5. [Telemetry contracts](telemetry/README.md)
6. [Tool contracts](tools/README.md)
7. [SQL contracts](sql/README.md)
8. [Graph RAG contracts](graph/README.md)
9. [Inference contracts](inference/README.md)

## Change rule

Change the linked implementation and its behavior tests together. Record contract changes and distinguish implemented code from planned services. Agent-specific rules belong in consumer repositories.

[Back to the platform reading order](../00-START-HERE.md).


## Folder contents

Provider-neutral data types and compatibility exports.

- [configuration.py](configuration.py): Provider-neutral contract for versioned configuration sources.
- [embeddings/](embeddings/README.md): Embedding profile identity and vector validation contracts.
- [models/](models/README.md): Synchronous model/completion port.
- [orchestration/](orchestration/README.md): Async model decisions, run results and observation port.
- [retrieval/](retrieval/README.md): Documents, hits and vector-store port.
- [telemetry/](telemetry/README.md): Content-free telemetry port.
- [graph/](graph/README.md): One-hop Graph RAG expansion port.
- [inference/](inference/README.md): Registered-model prediction port.
- [sql/](sql/README.md): Read-only allowlisted table port.
- [tools/](tools/README.md): Synchronous tool/idempotency contract.

# Retrieval adapters

## Purpose

MemoryStore is a small scoped linear-scan test store. QdrantStore uses scoped profile-specific collections.

## Current status

Both implemented; Qdrant local-client tests pass, remote server not certified.

## Where to work

[Canonical implementation or design](qdrant.py). This section contains the canonical implementation; update its code and tests together.

## Validation

Run the relevant SDK tests and the consuming agent tests after a contract change. Use synthetic data; live integrations require configured authorized endpoints.

[Parent section](../README.md) · [Reading order](../../00-START-HERE.md)


## Folder contents

Qdrant collection provisioning, writes and retrieval.

- [qdrant.py](qdrant.py): Collection-per-agent/profile adapter; provisioning is an administrator operation.
- [policy.py](policy.py): Cache key, optional ranking, and delete or restrict in front of a vector store.

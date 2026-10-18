# Retrieval contracts

## Purpose

VectorStore provides scoped upsert/search over Document and Hit values. Knowledge-service job contracts remain proposed.

## Current status

Implemented local/Qdrant interfaces; per-document ACL service is planned.

## Where to work

[Canonical implementation or design](../__init__.py). This section contains the canonical implementation; update its code and tests together.

## Validation

Run the relevant SDK tests and the consuming agent tests after a contract change. Use synthetic data; live integrations require configured authorized endpoints.

[Parent section](../README.md) · [Reading order](../../00-START-HERE.md)


## Folder contents

Documents, hits and vector-store port.

- [types.py](types.py): Document, retrieval hit and scope-aware vector-store contracts.

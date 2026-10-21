# Embedding contracts

## Purpose

EmbeddingProfile fixes model, revision, dimension, normalization, distance and preprocessing; ingestion and search must match.

## Current status

Implemented for cosine/L2 profiles. Same dimensions alone are insufficient.

## Where to work

[Canonical implementation or design](../__init__.py). This section contains the canonical implementation; update its code and tests together.

## Validation

Run the relevant SDK tests and the consuming agent tests after a contract change. Use synthetic data; live integrations require configured authorized endpoints.

[Parent section](../README.md) · [Reading order](../../../00-START-HERE.md)


## Folder contents

Embedding profile identity and vector validation contracts.

- [types.py](types.py): Embedding profiles, vector validation and embedder contract.

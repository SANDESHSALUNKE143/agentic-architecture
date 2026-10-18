# Embedding adapters

## Purpose

Use HashEmbedder for deterministic tests or CompatibleEmbedder for configured providers; validate every vector against its profile.

## Current status

Implemented adapter code; no live embedding endpoint certification.

## Where to work

[Canonical implementation or design](../llm/openai_compatible/completion.py). This section contains the canonical implementation; update its code and tests together.

## Validation

Run the relevant SDK tests and the consuming agent tests after a contract change. Use synthetic data; live integrations require configured authorized endpoints.

[Parent section](../README.md) · [Reading order](../../00-START-HERE.md)


## Folder contents

Compatible-provider vector generation and profile validation.

- [compatible.py](compatible.py): Compatible embeddings endpoint adapter with strict profile validation.

# Inference adapter

A registry of callables. predict accepts only registered model ids. Training pipelines are not part of this adapter.

## Current status

Implemented. The consumer registers its own functions when it composes the agent.

## Where to work

[Registry implementation](registry.py).

[Parent section](../README.md) · [Inference contract](../../contracts/inference/README.md)

## Folder contents

- [registry.py](registry.py): Operator-registered model calls.

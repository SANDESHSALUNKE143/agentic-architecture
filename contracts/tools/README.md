# Tool contracts

## Purpose

ToolSpec declares name, input schema, permission, read-only policy, prerequisites and async handler.

## Current status

Implemented JSON Schema validation and fail-closed invocation.

## Where to work

[Canonical implementation or design](../../core/harness/runner.py). This section contains the canonical implementation; update its code and tests together.

## Validation

Run the relevant SDK tests and the consuming agent tests after a contract change. Use synthetic data; live integrations require configured authorized endpoints.

[Parent section](../README.md) · [Reading order](../../00-START-HERE.md)


## Folder contents

Synchronous tool/idempotency contract.

- [types.py](types.py): Synchronous tool contract with caller-managed idempotency identity.

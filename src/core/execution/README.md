# Execution lifecycle

## Purpose

Validate request, reserve estimate, call model, validate action, authorize tool, execute, observe, repeat or finish.

## Current status

Implemented steps, timeout, context/output bounds and repeated-call detection.

## Where to work

[Canonical implementation or design](tools.py). This section contains the canonical implementation; update its code and tests together.

## Validation

Run the relevant SDK tests and the consuming agent tests after a contract change. Use synthetic data; live integrations require configured authorized endpoints.

[Parent section](../README.md) · [Reading order](../../../00-START-HERE.md)


## Folder contents

Registered tool schemas, permissions, prerequisites and approval checks.

- [tools.py](tools.py): Explicit tool allowlist, schema validation and authorization before handler invocation.

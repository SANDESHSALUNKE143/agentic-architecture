# Execution policies

## Purpose

Reject unknown/schema-invalid tools, missing scopes, unsatisfied prerequisites and unapproved mutations before side effects.

## Current status

Implemented local guards; durable monetary quotas and policy administration are planned.

## Where to work

[Canonical implementation or design](limits.py). This section contains the canonical implementation; update its code and tests together.

## Validation

Run the relevant SDK tests and the consuming agent tests after a contract change. Use synthetic data; live integrations require configured authorized endpoints.

[Parent section](../README.md) · [Reading order](../../00-START-HERE.md)


## Folder contents

Validated request-level limits.

- [limits.py](limits.py): Validated run-level step, byte, token and time limits.

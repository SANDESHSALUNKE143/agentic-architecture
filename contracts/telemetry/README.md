# Telemetry contracts

## Purpose

RunObserver.emit receives scoped metadata. Telemetry.record supports the earlier RAG path. Never include prompt or result content by default.

## Current status

SQLite run observer and older OTel adapter exist; a unified exported run-observer pipeline is planned.

## Where to work

[Canonical implementation or design](../../adapters/persistence/sqlite.py). This section contains the canonical implementation; update its code and tests together.

## Validation

Run the relevant SDK tests and the consuming agent tests after a contract change. Use synthetic data; live integrations require configured authorized endpoints.

[Parent section](../README.md) · [Reading order](../../00-START-HERE.md)


## Folder contents

Content-free telemetry port.

- [types.py](types.py): Content-free telemetry recording contract.

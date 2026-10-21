# Persistence adapters

## Purpose

SQLiteRunStore stores scoped metadata. PostgreSQL starter SQL belongs to future config/control-plane persistence.

## Current status

SQLite implemented; PostgreSQL application adapter planned.

## Where to work

[Canonical implementation or design](sqlite.py). This section contains the canonical implementation; update its code and tests together.

## Validation

Run the relevant SDK tests and the consuming agent tests after a contract change. Use synthetic data; live integrations require configured authorized endpoints.

[Parent section](../README.md) · [Reading order](../../../00-START-HERE.md)


## Folder contents

Scoped SQLite metadata and PostgreSQL platform state/reservations.

- [postgres.py](postgres.py): PostgreSQL persistence and atomic scope/day token reservations.
- [sqlite.py](sqlite.py): Persistent content-free run telemetry for a single-host prototype.

# SQL adapter

Read-only DB-API adapter. The operator supplies the connection and the table allowlist. PostgreSQL uses paramstyle pyformat so the adapter can set a statement timeout. SQLite tests use qmark.

## Current status

Implemented. Business rows stay in the consumer database, not in this package.

## Where to work

[Read implementation](read.py).

[Parent section](../README.md) · [SQL contract](../../contracts/sql/README.md)

## Folder contents

- [read.py](read.py): Allowlisted single-table reads with a row cap.

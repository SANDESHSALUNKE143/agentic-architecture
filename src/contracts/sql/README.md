# SQL contracts

Read-only table access. The model may name an allowlisted table and a row limit. It cannot supply a connection string or a statement.

## Current status

`SqlRead.query` is the port. The DB-API adapter lives in adapters/sql.

## Where to work

[Canonical types](types.py).

[Parent section](../README.md) · [Reading order](../../../00-START-HERE.md)

## Folder contents

- [types.py](types.py): Read-only SQL port.

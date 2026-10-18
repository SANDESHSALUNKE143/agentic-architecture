# Observability adapters

## Purpose

SafeTelemetry is in-memory; OTelTelemetry is an optional bridge; SQLiteRunStore persists content-free run events.

## Current status

Implemented components; full backend export and scoped dashboards require deployment work.

## Where to work

[Canonical implementation or design](otel.py). This section contains the canonical implementation; update its code and tests together.

## Validation

Run the relevant SDK tests and the consuming agent tests after a contract change. Use synthetic data; live integrations require configured authorized endpoints.

[Parent section](../README.md) · [Reading order](../../00-START-HERE.md)


## Folder contents

Content-free OTel event export and the smaller RAG telemetry bridge.

- [events.py](events.py): Content-free run telemetry with optional OTLP traces, metrics and logs.
- [otel.py](otel.py): Optional traces/metrics bridge; exporter lifecycle belongs to the application.

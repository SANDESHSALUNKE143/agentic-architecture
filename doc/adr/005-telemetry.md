# OpenTelemetry and optional OSS backends

Status: Accepted design; bridge implemented.

## Context

Many independently developed agents must share infrastructure on a constrained prototype server, with a future hybrid deployment.

## Decision

Use portable telemetry contracts and content-free defaults.

## Alternatives

Couple observability to an orchestration framework.

## Consequences

Exporter configuration and backend access controls remain deployment work.

## Revisit when

Measured scale, new trust boundaries or incompatible provider requirements invalidate the assumptions. Record a superseding ADR rather than silently rewriting the decision.

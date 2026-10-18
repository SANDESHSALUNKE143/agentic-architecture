# Server-side tenant and agent authorization

Status: Accepted design; local guards implemented.

## Context

Many independently developed agents must share infrastructure on a constrained prototype server, with a future hybrid deployment.

## Decision

Derive scope from verified credentials and enforce it in storage and query gateways.

## Alternatives

Trust dashboard filters, caller headers or collection names.

## Consequences

More platform work; prototype remains trusted-process only.

## Revisit when

Measured scale, new trust boundaries or incompatible provider requirements invalidate the assumptions. Record a superseding ADR rather than silently rewriting the decision.

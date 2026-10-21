# Compose now, Helm after service boundaries stabilize

Status: Accepted.

## Context

Many independently developed agents must share infrastructure on a constrained prototype server, with a future hybrid deployment.

## Decision

Use a bounded single-host prototype with optional external stateful services.

## Alternatives

Run Kubernetes immediately or claim single-node HA.

## Consequences

Faster iteration; migration requires explicit storage, identity and operational work.

## Revisit when

Measured scale, new trust boundaries or incompatible provider requirements invalidate the assumptions. Record a superseding ADR rather than silently rewriting the decision.

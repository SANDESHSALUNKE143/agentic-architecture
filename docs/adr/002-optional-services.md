# Optional control plane and data plane

Status: Accepted design; services planned.

## Context

Many independently developed agents must share infrastructure on a constrained prototype server, with a future hybrid deployment.

## Decision

Start embedded; add authenticated hosted services where centralized enforcement is needed.

## Alternatives

Deploy every component immediately on the single host.

## Consequences

Lower prototype footprint; direct SDK guards cannot enforce global policy.

## Revisit when

Measured scale, new trust boundaries or incompatible provider requirements invalidate the assumptions. Record a superseding ADR rather than silently rewriting the decision.

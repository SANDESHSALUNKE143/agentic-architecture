# Reserve before paid work

Status: Accepted; local guard only.

## Context

Many independently developed agents must share infrastructure on a constrained prototype server, with a future hybrid deployment.

## Decision

Enforce distributed reservations at a gateway and reconcile usage after completion.

## Alternatives

Only display a cost dashboard after calls are billed.

## Consequences

Durable ledger and fail-closed behavior trade availability for budget protection.

## Revisit when

Measured scale, new trust boundaries or incompatible provider requirements invalidate the assumptions. Record a superseding ADR rather than silently rewriting the decision.

# Immutable embedding/index profiles

Status: Accepted and partially implemented.

## Context

Many independently developed agents must share infrastructure on a constrained prototype server, with a future hybrid deployment.

## Decision

Bind every index to full model/revision/preprocessing/dimension/distance identity.

## Alternatives

Accept any same-dimensional embedding or silently switch models.

## Consequences

Reindexing costs storage and compute but prevents invalid similarity search.

## Revisit when

Measured scale, new trust boundaries or incompatible provider requirements invalidate the assumptions. Record a superseding ADR rather than silently rewriting the decision.

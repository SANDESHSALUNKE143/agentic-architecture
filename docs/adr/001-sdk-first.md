# Versioned SDK and hexagonal ports

Status: Accepted.

## Context

Many independently developed agents must share infrastructure on a constrained prototype server, with a future hybrid deployment.

## Decision

Centralize shared behavior in an installable package; keep frameworks at the application edge.

## Alternatives

Copying templates with provider code or imposing one orchestration framework.

## Consequences

Less duplication and stable contracts; maintainers own compatibility and releases.

## Revisit when

Measured scale, new trust boundaries or incompatible provider requirements invalidate the assumptions. Record a superseding ADR rather than silently rewriting the decision.

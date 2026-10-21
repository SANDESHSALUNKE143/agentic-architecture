---
name: agent-developer
description: Build or extend an agent consuming Agentic Foundation, validate its manifest and contracts, or add a shared adapter while preserving platform and consumer boundaries.
---

Use this as engineering guidance, not runtime authorization. Work within the user's requested repositories; invoking the skill does not authorize publication or external access grants.

Read [architecture](references/architecture.md) and [design patterns](references/design-patterns.md) for ownership. Use [provider catalog](references/provider-catalog.md), [model selection](references/model-selection.md), and [embedding/retrieval](references/embedding-retrieval.md) for adapters. For integration use [API endpoints](references/api-endpoints.md) and [security](references/security.md). For operating changes use [observability](references/observability.md), [deployment](references/deployment.md), and [testing standards](references/testing-standards.md).

Keep consumers small: manifest, instructions, domain capabilities, composition, tests and deployment. Import the pinned SDK or call its APIs. Never copy the harness or credential plumbing. Canonical platform Python lives in `src/`. `src/agentic_sdk` is a compatibility facade.

SDK 0.3.0 includes local model/tool APIs, immutable registry revisions, ingestion worker, Qdrant retrieval, token ledger, native Anthropic, MCP-session and n8n adapters, and the local telemetry stack. External provider/session certification, OIDC, a custom portal, knowledge deletion and production Helm remain separate release gates. Check the current implementation map before changing a component; fake tests do not certify live services.

Generate a runnable consumer with `python -m agentic_sdk.developer init <new-path> --name <slug>`, install it, then use validate/run/evaluate/serve. The assets illustrate layout; the SDK generator is the runnable source of truth. Use scripts/validate-agent.py, scripts/validate-config.py and scripts/check-contracts.py with explicit consumer/config/platform paths and the declared SDK dependencies installed.

Resolve secrets from approved environment references. Preserve backend grants and SQL safeguards. Model output cannot grant permission; mutations need trusted approval and a reconciliation design. An embedding profile change requires reindexing. Report actual checks and unverified live integration boundaries.

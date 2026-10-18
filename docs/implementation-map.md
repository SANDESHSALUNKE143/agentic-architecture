# Executable implementation map - 0.3.0

| Responsibility | Canonical code | Evidence |
|---|---|---|
| Typed execution, tool permissions, prerequisites and budgets | core/harness/runner.py + core/execution/tools.py + core/policies/limits.py | tests/test_execution.py |
| Configuration/provider composition | project.py, decision_models.py, adapters/providers.py | config/provider tests |
| Authenticated bounded transport | http.py | transport tests |
| Scoped agent API/history | service.py, run_store.py | AgentN tests |
| Generate/validate/run/serve/evaluate agents | sdk/python/developer.py | tests/test_developer.py and generated-agent smoke |
| Registry, model/tool gateway, knowledge API, token ledger | services/*/routes.py + adapters/persistence/postgres.py | scripts/test_full_platform.py |
| Persistent ingestion worker | services/knowledge_service/worker.py | full-stack job acceptance |
| Agent-scoped vector retrieval | adapters/retrieval/qdrant.py | local Qdrant and full-stack tests |
| Hosted consuming adapters | hosted_client.py | AgentN full-stack smoke |
| Content-free OTLP signals | adapters/observability/events.py | backend query acceptance |
| Complete local infrastructure | deployment/full | Compose startup + endpoint checks |

The architecture folders link to these modules; there are no duplicate harnesses. Logical service boundaries share one API process for the prototype. [Developer guide](developer-guide.md), [full local runbook](../deployment/full/README.md), and [remaining gates](release-gates.md) define the supported operating scope.

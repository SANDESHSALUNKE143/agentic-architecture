# Current architecture

The versioned SDK is the reuse boundary. Framework-neutral contracts and policies support agents that own only domain instructions, capabilities and composition. Shared gateways are optional; the local full-stack profile demonstrates them with AgentN.

```mermaid
flowchart TB
  Consumer[Agent repository: domain and instructions] --> Harness[core/harness: AgentRunner]
  Harness --> Context[core/context: trusted identity]
  Harness --> Policy[core/policies: run limits]
  Harness --> Tools[core/execution: authorized tools]
  Harness --> Ports[contracts: model and tool protocols]
  Ports --> Adapters[adapters: providers, HTTP, persistence, telemetry]
  Adapters --> Hosted[services: model and tool routes]
  Hosted --> Store[(PostgreSQL: configuration, jobs, token ledger)]
  Knowledge[services/knowledge_service] --> Store
  Worker[Ingestion worker] --> Store
  Worker --> Vector[(Qdrant: scope/profile collections)]
  Adapters --> Collector[OpenTelemetry Collector]
  Collector --> Monitoring[Prometheus, Loki, Tempo and Grafana]
```

## Source ownership

- `contracts/` defines ports and typed records without provider clients.
- `core/context`, `core/execution`, `core/harness`, `core/policies` implement trusted identity, authorized invocation, the loop and limits.
- `adapters/` implements external systems and explicit factories.
- `services/` owns API boundaries, credential binding and background ingestion.
- `sdk/python/` owns validated configuration, project commands and service clients.
- `src/agentic_sdk/` preserves public import compatibility through re-exports. Setuptools maps canonical folders into one installed namespace; no code is copied into agent repositories.

See [physical source layout](source-layout.md) and [the folder audit index](folder-index.md) for exact files.

## Execution and trust

The host resolves a credential to a fixed tenant/agent context. AgentRunner checks context size, deadline and conservative token reservation before asking DecisionModel for a tool/final action. ToolRegistry validates the JSON schema, permission, prerequisites and trusted mutation approval before invoking the handler. Final answers may require evidence tools. Per-request state is isolated; durable conversation memory is not implemented.

Consumers can use direct SDK adapters or HostedDecisionModel and an approved tool gateway. AgentN business grants and SQL validation remain the existing backend's responsibility. Model output never supplies credentials or permissions. Static local credentials are not end-user federation, and context guards do not sandbox malicious in-process code.

## Local services and data

The platform API process hosts separate registry/model/tool/knowledge route modules. PostgreSQL stores immutable configuration revisions, ingestion jobs and atomic token reservations. A separate worker processes bounded text chunks into agent/profile-specific Qdrant collections. Identical content/profile submissions reuse a job. Content versions are append-only; deletion and document-level ACL lifecycle remain gaps. Publishing configuration does not hot-reload agents.

AgentN run metadata uses a scoped SQLite store. OTLP export sends content-free events to the operator monitoring stack. Event spans are not a fully propagated distributed trace, and shared dashboard labels are not tenant query authorization.

## Ready locally versus release gates

The full local profile is exercised with synthetic model, backend and embedding data. Compatible and native provider adapters exist, but paid/live integrations require separate validation. OIDC delegation, HA, production Helm, knowledge deletion, release artifact certification and operational drills remain [release gates](release-gates.md). Start with the [developer guide](developer-guide.md) and [local runbook](../deployment/full/README.md).

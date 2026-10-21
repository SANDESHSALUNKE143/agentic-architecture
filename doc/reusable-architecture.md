# Reusable architecture: platform, application and execution

The [enterprise guide](guide.md) is the reading path. The reference agent is [insight](../examples/insight_agent/README.md). The library never imports that agent.

## Why v0.1 was incomplete as a project foundation

The initial example ingested one text chunk into memory, searched and echoed a prompt. That demonstrated ports but did not provide an agent execution lifecycle, a consumer package, a hosted interface or persistent run visibility. v0.2 introduced those pieces; v0.3 adds local gateways, registry, ingestion and telemetry. The reference agent in this repository is examples/insight_agent. It does not equate a full enterprise platform with this single-host implementation.

## Physical and logical ownership

| Layer | Repository/package | Owns | Does not own |
|---|---|---|---|
| Agentic domain/contracts | SDK | DecisionModel, ModelReply, ToolSpec, RunLimits, Context, RunResult | Advertiser rules or SQL catalog |
| Execution/application | SDK | Step loop, guard ordering, schema validation, deadlines, result limits | Business conclusions or arbitrary tools |
| Infrastructure adapters | SDK | Model clients, REST transport, scoped run storage, optional Qdrant/OTel | Business database schema |
| Optional API host | SDK routes + consumer bindings | Token-to-agent mapping, run endpoint, config snapshot, scoped history | User identity federation or dynamic portal |
| Business agent | examples/insight_agent | Instruction, tool handlers, evidence prerequisites, product page | Duplicated retry/auth/logging framework |
| System of record | Existing Agent N backend | Advertiser grants, read-only SQL validation, actual metrics, refresh policy | LLM reasoning |
| External AI integration | Existing MCP server | OAuth/MCP discovery and existing tool surface | New SDK-hosted reasoning service |

Dependencies point inward: consumer -> SDK ports; adapters -> ports. The SDK never imports Agent N. The new consumer never imports backend implementation modules or uses its database connection. No framework dependency is required by the execution engine. LangGraph can later call these components when durable graph checkpoints justify it.

## Runtime sequence

```mermaid
sequenceDiagram
  participant U as Caller
  participant H as Consumer CLI / SDK API
  participant R as SDK AgentRunner
  participant M as DecisionModel
  participant T as Tool registry
  participant B as Agent N API
  participant O as Scoped metadata store
  U->>H: Question (+ API bearer credential)
  H->>H: Resolve fixed trusted agent context
  H->>R: run(context, question)
  R->>O: run.started (no question)
  loop Until final or execution limit
    R->>R: Reserve estimate; check context and deadline
    R->>M: Instructions + schemas + bounded observations
    M-->>R: Tool action or final action
    R->>T: Validate schema / scope / prerequisites / mutation approval
    T->>B: Fixed REST route + authorized backend token
    B->>B: Verify current grants / advertiser scope / SQL policy
    B-->>T: Data + freshness
    T-->>R: Bounded observation
    R->>O: tool metadata
  end
  R->>O: run.finished + usage/status
  R-->>U: Answer + run ID + tool names + usage
```

The final branch returns without invoking another tool. In the Agent N consumer, final output requires catalog and freshness evidence. SQL additionally requires both tools to have completed. These prerequisites are enforced by code, not only prompt wording. Freshness qualification and non-additive reach reasoning still require domain evaluation; tool ordering does not guarantee truthful model prose.

## Agent lifecycle

On boot validate config -> resolve environment secret references -> construct model/transport -> register tools -> construct runner -> bind HTTP credential if serving. Each request creates isolated observations, usage counters and duplicate-call state. Client objects may be shared, but conversation history is not global. On completion write metadata; on shutdown close clients. State survives restarts only for metadata, not conversational memory or resumable execution.

Tools can execute only when registered, schema-valid, permitted and prerequisite-complete. Non-read-only tools additionally require trusted caller approval outside model output. The stock Agent N composition does not register refresh; its optional definition is available for an intentionally approved future workflow. Transport never retries mutations. Identical repeated calls terminate; intentional polling needs a separate bounded workflow with delay and distinct poll policy, not an unrestricted loop.

## Trust boundaries

CLI is a trusted operator process. The prototype HTTP service uses one random opaque bearer credential per agent binding. That credential grants the bound backend workload identity's access. It does not preserve arbitrary end-user identities: do not give a broad backend-token binding to multiple users with different grants. Before multi-user deployment, add verified OIDC and per-user token resolution, with no shared broad credential. Backend authorization remains mandatory on every request.

The generic REST transport rejects non-HTTPS except explicit loopback or operator-approved Docker hosts, credentials in URLs, arbitrary absolute paths and redirects. Its configured host is trusted operator configuration; it is not a full DNS-based SSRF defense. Backend and model endpoints must be egress-allowlisted by deployment. TLS termination, body-size/rate limits and OIDC are production edge responsibilities not supplied by this prototype API.

## Cost and timeout semantics

Per-run reservation uses conservative serialized-context bytes plus output allowance, not a provider tokenizer or money ledger. Reported provider usage is accumulated. Failed/ambiguous provider calls can still be charged. The JSON decision adapter currently wraps synchronous model calls in a thread: the async deadline stops the run, but cannot forcibly stop that provider call, which has its own timeout. No subsequent tool executes after timeout. The hosted gateway additionally persists conservative daily token reservations. Neither mechanism guarantees currency settlement or cancels an in-flight provider charge.

SQLite stores metadata only and performs indexed scoped queries. It is suitable for a single host with modest write concurrency; no HA or unlimited retention. Define pruning/backups. The RAG OTel bridge remains optional. PlatformObserver exports content-free event spans, metrics and logs; deployment/full provisions the operator monitoring stack.

## Deployment topology

Prototype: existing backend/database continue where they are; new agent process/container calls backend over HTTPS and remote model endpoint; local metadata volume stores execution history. An agent API is optional for CLI-only projects. Later: externalize observability and durable state, add workload/user federation and distributed admission control, then scale stateless workers. See retained resource-budget and Helm migration guidance; this change creates no production Helm chart.

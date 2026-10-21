# NFRs, performance and cost governance

> Phase-one design reference. For current executable behavior and the separate consuming agent, read [the current implementation map](implementation-map.md). Features described as planned here are not automatically implemented by the new agent API.

These are initial acceptance targets, not measured promises. The offline sample is not a server and has no availability SLO.

| Attribute | Prototype target / measurement | Production change |
|---|---|---|
| Latency | Warm retrieval p95 <300ms; end-to-end p95 <10s at 5 concurrent callers | Measure per model, region, context length; enforce deadlines |
| Throughput | Sweep 1/5/10 concurrency against 100k representative chunks | Load-test admission and provider quotas, avoid unbounded queues |
| Availability | Single host, planned downtime accepted | Redundant nodes and managed/durable services; negotiated 99.9% target |
| Recovery | Target RPO 24h / RTO 4h, verified restore exercise | WAL shipping, replicated storage and regional recovery |
| Isolation | No cross-agent hits in negative tests | Verified identity + document ACL and backend query enforcement |
| Quality | Offline recall@1 3/3 smoke fixture | Domain recall@k, groundedness, citation correctness and refusal thresholds |
| Security | No real secrets/endpoints committed | SAST, dependency/image scans, SBOM, threat review |

Measure with realistic document lengths and ACL filters. Report hardware, versions, cold/warm caches, corpus/chunk count, concurrency, p50/p95/p99, errors, 429s, tokens, cost and peak memory. Isolate ingestion from query benchmarks. Run failure injection for provider timeout, rate limit, partial ingestion, profile mismatch, disk pressure, stale config and telemetry outage. Release gates must be based on agreed domain thresholds rather than the toy fixture.

## Performance controls

Bound question bytes (4,000), chunk bytes (16,000), top-k (3 in runtime; store allows 1..20), assembled context (12,000 characters) and output limit (1..4,096). Full tokenizer-aware prompt budgets and provider context-window checks are planned. Use shared client pools, query batching where appropriate, bounded concurrency, token buckets and circuit breakers in hosted components. Current runtime is synchronous and memory store is a linear scan; use Qdrant for larger corpora. Do not treat memory scan benchmarks as Qdrant performance.

Cache embedding results by scope/profile/content hash and retrieval by scope/ACL revision/index revision/query. Never cache across agents by query text alone. Invalidate on source deletion/ACL updates. Model response caching is opt-in for deterministic authorized requests. Set TTLs and bounded size. Caching, rate limiting and circuit breakers are design requirements, not implemented features.

## Budgeting

The SDK Budget reserves conservative byte-based token estimates under a process-local lock. It never refunds failed calls, persists nothing and can be bypassed by another process. It is a demo guard, not a financial control. Generation reserves input bytes + output cap + framing allowance; embeddings reserve text bytes. Provider usage is recorded for generation only. Tokenization, reasoning tokens and hidden provider overhead require model-specific accounting before hard caps can be claimed.

The planned gateway checks agent/tenant daily and monthly limits, per-request caps, model allowlists and concurrency before forwarding. Atomically reserve worst-case cost; settle actual usage with unique provider request ID; keep ambiguous timeouts reserved until reconciled. Use integer microcurrency units or decimals, never floating point money. Price tables are versioned and effective-dated, with currency, input/output/cached/embedding rates and provider/deployment. Do not embed current prices in source.

Estimated request cost = input_tokens * input_rate_per_million / 1e6 + output_tokens * output_rate_per_million / 1e6 + embedding charges + allocated infrastructure. Track billed vs estimated separately; costs may be delayed. Include Azure compute, disks, snapshots, database, egress and telemetry retention. Self-hosted open-source software still consumes infrastructure and operations effort.

Route low-risk requests to a cheaper evaluated model, cap tool iterations, halt at deadline/budget, and require explicit policy for fallback to a more expensive model. Warn at 80%, deny at 100% unless a separately authorized override exists. Ingestion has its own budget; reindexing must be estimated and reserved before bulk execution. No automatic provider failover is implemented.

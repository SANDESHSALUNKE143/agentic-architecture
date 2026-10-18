# Agent N: integration decision and migration boundary

The supplied existing checkout contains backend, frontend and MCP repositories. The MCP documentation mentions a separate LangGraph service, but that service was not present in the inspected checkout. The new `agent-n-assistant` is a separate consumer repository; the existing code is not rewritten.

## What was verified in source

The backend exposes `/api/agent/catalog`, `/api/agent/status`, `/api/agent/sql`, `/api/agent/refresh` and refresh-run polling. Its route layer checks scopes; its domain services retain advertiser access and SQL safety. The MCP surface presents `list_tables`, `execute_sql`, `get_data_status` and `refresh_data`. Its runtime already centralizes rate/concurrency guards, account resolution, envelopes and observability. These are useful architectural patterns, but existing private source was not copied into the SDK.

## New mapping

| Existing capability | New consumer binding | Shared SDK responsibility |
|---|---|---|
| Catalog/views + connection | list_tables -> GET /api/agent/catalog | Transport, schema, response bound |
| Freshness/readiness | get_data_status -> GET /api/agent/status | Tool permissions and per-run evidence tracking |
| Read-only SQL | execute_sql -> POST /api/agent/sql | Require catalog+status, validate string size; backend still validates SQL |
| Feed refresh | Optional ToolSpec only; not registered in default app | Mutation approval gate; no automatic retries |
| Model reasoning | New consumer decision model | Compatible adapter, loop, limits, usage |
| Agent serving | Thin consumer binding | Shared /config, /runs and /events routes |

Do not extract advertiser scopes, reach arithmetic or SQL allowlists into the generic SDK. Do not weaken existing MCP OAuth/grant enforcement. A backend access token and an MCP access token have different audiences. The new direct REST integration requires a currently valid backend access token; OAuth token exchange and renewal are not implemented. No service-secret bypass or spoofed user header is introduced.

## Adoption steps

Run synthetic CLI and HTTP tests first. Deploy the new agent separately with a restricted backend identity and a configured model. Run contract tests against a nonproduction backend with known advertiser grants, compare answers against existing MCP/backend results, evaluate stale/missing data and non-additive metrics, and only then route users to the new agent. Keep the old MCP path available for rollback. No business data/schema migration is required for this first consumer because all access remains through existing APIs.

The current agent is read-only. Add refresh as a separately reviewed workflow with explicit approval, existing backend cooldown/deduplication and bounded polling; a prompt asking the model to be careful is insufficient. Add end-user token delegation before a multi-user UI connects to a single agent service. No live backend or paid model calls were made during this implementation.

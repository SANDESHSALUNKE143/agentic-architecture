# Architecture review

This review is based on the code in this repository. [agentic_operations_configuration_center_v4.html](agentic_operations_configuration_center_v4.html) is the visual reference for the console. Its script saves form fields in the browser and does not call the API. The console does not copy that save path.

## Current state

The platform is one API process and one React console. Agents are YAML contracts. [agentic/04-loops/runtime/runtime.py](../agentic/04-loops/runtime/runtime.py) is the only loop. [agentic/05-tools/mcp/tool-gateway/gateway.py](../agentic/05-tools/mcp/tool-gateway/gateway.py) is the only tool gate. Writes are simulated and still wait for approval. Mock mode is the default. A live model call happens only when the process is in live mode and a model key is set.

The console can edit an agent contract and can store a host URL, connection string, username, and password. The password is written to `data/connections.json` and is not returned. SQL, n8n, Qdrant, AWS, Grafana, and OpenTelemetry are marked configured when an address or environment variable is set. This build still uses the local index, the local fixture, and the platform model. It does not call those hosts. The gateway is an in-process registry. It is not a remote MCP server.

There is no list of past runs. A run can be read by id while the process is up. There is no agent draft or publish state, no token budget, no role list, and no tenant boundary.

## Findings

### P0 — Do not store configuration in the browser

The HTML prototype writes settings with `localStorage.setItem`. That includes endpoints and secret references. A browser store is not a secret manager, and a refresh of this console must not be the source of truth.

The React console saves through `PUT /settings/agents/{id}` and `PUT /settings/connections/{id}`. The connection response includes `password_set` and does not include the password. The model key is reported only as set or not set. The unit test `test_connection_url_is_saved_and_password_stays_hidden` covers the password rule.

### P1 — Configured is not healthy

An address in the connection file marks a host configured. Nothing in this process opens Qdrant, AWS, Grafana, OpenTelemetry, n8n, or a warehouse and reports success. The console must say "Address saved" or "Mock". It must not say "Healthy".

Conversation state, saved notes, and retrieval are three different stores. Conversation state is the session turn list. Notes are the in-process note list. Retrieval is the document index, with an optional Qdrant or AWS address that this build does not call. The configuration screen keeps those three apart.

### P2 — Enterprise controls that are not in this runtime

Agent versioning, draft and publish states, token budgets, provider routing, role-based access, tenant isolation, and a durable secret manager are not implemented. [agentic/02-guardrails/credentials.py](../agentic/02-guardrails/credentials.py) keeps values in memory and is not the connection store. These stay on the roadmap.

### P3 — Vendors named only in the prototype

Databricks, Snowflake, Synapse, BigQuery, Redshift, Anthropic, and Gemini appear in the HTML reference. This runtime has one SQL port, and it still returns the local read-only fixture. The model choice is the platform model, an OpenAI-compatible host, or AWS. Those extra vendors are not offered as working connections.

## Information architecture

The console follows the reference layout.

| Screen | What it controls |
| --- | --- |
| Agent chat | One selected agent, a transcript, the live whisper, the answer, and the execution panel |
| Agent library | The eight contracts, each opening that agent's chat |
| Run history | Runs started in this browser session, because the API has no run list |
| Approvals | The real approval queue |
| Configuration | Agents, the SQL warehouse, connectors, memory, models, security, and runtime |
| Docs | This review, the implementation guide, and the operations pages |

## Roadmap

1. Keep secrets on the server and label every external host as mock or address saved.
2. Keep the chat, library, and configuration screens on the existing run and settings APIs.
3. Add a real run list only when the API stores runs beyond this process.
4. Add publishing, budgets, roles, and tenants only with backend enforcement.
5. Add another warehouse or model vendor only when a driver and a health check exist.

## Acceptance

A saved connection response has no password. The console has no field that stores a model key in the browser. Mock mode is labeled on the chat screen. SQL remains read-only. A write still waits for a different actor to approve it.

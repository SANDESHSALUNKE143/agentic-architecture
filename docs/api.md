# API

`agentic/01-entry/app.py` mounts this API. The JSON bodies are in `agentic/01-entry/bodies.py`. FastAPI checks a body before the route runs. The same descriptions appear on the interactive page. Runs, approvals, the catalog, settings, MCP servers, and the guide each live in their own route module.

| Where you are | Interactive docs | Calls |
| --- | --- | --- |
| Laptop | <http://127.0.0.1:8090/docs> | <http://127.0.0.1:8090> |
| Server | <http://127.0.0.1:5173/docs> | The console port. Nginx proxies these paths |

Send `Authorization: Bearer <token>` on every route except `GET /guide/assets/{name}`. The sample token is `local-dev-token-not-for-production`. A missing or wrong token is `401`. `PLATFORM_ENV=production` refuses to start while that sample token is still set.

A client that sends more than `PLATFORM_RATE_LIMIT` requests in `PLATFORM_RATE_WINDOW` seconds receives `429` and `Retry-After`. The defaults are 120 requests and 60 seconds. A body larger than `PLATFORM_MAX_BODY` bytes receives `413`. The default is 262144. An unexpected failure is `500` with the detail `The server could not complete the request.` The response does not include a stack trace. Responses send `X-Content-Type-Options: nosniff`, `X-Frame-Options: DENY`, and `Cache-Control: no-store`.

The console in `ui/admin-dashboard` is the caller. `ui/admin-dashboard/src/api.ts` attaches the token. Chat uses `src/stream.ts`.

A public run has `request_id`, `session_id`, `workflow`, `status`, `error`, `error_code`, `agents`, and `approval_id` when a write is waiting. Each agent entry has `agent_id`, `status`, `result`, `tool_calls`, and `requires_approval`.

## Health

| | |
| --- | --- |
| `GET /health` | Process status, model mode, and the agent count. The console sidebar uses this. |

## Platform

| | |
| --- | --- |
| `GET /platform` | The seven steps, security, observability, the live workflow sequences, the n8n tool, and the files a business team edits. The Workflows tab reads `workflows` from this body. |

## Runs

`RunBody` is the body for both start routes.

| Field | Required | Meaning |
| --- | --- | --- |
| `task` | yes | The brief. Phrases in it select a workflow when `workflow` and `agents` are empty |
| `user_id` | no | Defaults to `local-development-user` |
| `session_id` | no | Empty starts a new session |
| `workflow` | no | A sequence such as `product-discovery`, or a specialist such as `research` |
| `agents` | no | An explicit list. When set, it wins over `workflow` and over the phrases |

| Route | What happens |
| --- | --- |
| `POST /agent-runs` | Runs the plan and returns the public run |
| `POST /agent-runs/stream` | Same run as server-sent events. Chat uses this. Events are `activity`, `plan`, `step`, `done`, and `error` |
| `GET /agent-runs/{run_id}` | The stored run. `404` when this process does not have that id |
| `POST /agent-runs/{run_id}/cancel` | Asks a running plan to stop. `409` when it is not running |
| `POST /agent-runs/{run_id}/feedback` | `FeedbackBody`: `helpful` and an optional `note`. Records a score. It does not change model weights |

Example:

```bash
curl -s -H "Authorization: Bearer local-dev-token-not-for-production" \
  -H "Content-Type: application/json" \
  -d '{"task":"Find a blue trail jacket under $150"}' \
  http://127.0.0.1:8090/agent-runs
```

## Approvals

| Route | Body | What happens |
| --- | --- | --- |
| `GET /approvals` | | The queue of paused writes |
| `POST /approvals/{approval_id}/decision` | `DecisionBody` | `decision` is `approve` or `reject`. `actor` defaults to `local-operator` |

`403` when the actor is the agent that asked. `409` when the approval is missing, already decided, or stale. Approve resumes the write and any agents still left in the sequence.

## Agents and tools

| Route | What it returns |
| --- | --- |
| `GET /agents` | Name, description, and tools for every loaded contract |
| `GET /tools` | Every plugin in the gateway: name, group, summary, permission, write flag, and argument schema |

## Plugins, RAG, and observability

`PluginBody` is `{ "agents": ["catalog-agent"] }`. The named agents must already have the permission for that plugin. A write stays behind approval. A refused connection is `422`.

| Route | What it changes |
| --- | --- |
| `GET /plugins` | The catalog, which agents are connected, and the port status |
| `PUT /plugins/{name}` | Connects that plugin to the listed agents |
| `PUT /settings/rag/{kind}/{choice}` | Sets a vector, embedding, or model choice on those agents |
| `PUT /settings/observability/{sink_id}` | Adds that sink to those agents' contracts |

## Settings

`ContractBody` is a partial agent contract. Omitted fields stay as they are. The console gear saves through this route. `422` when the change would grant a write permission the agent does not have, or would clear approval on a write. `404` when the agent id is unknown.

| Field | Meaning |
| --- | --- |
| `instructions` | The lines in the contract |
| `tools` | Plugin names the agent may call |
| `memory` | Conversation state, notes, and `long_term_memory` |
| `approval` | `required_for` and, for orders, `amount_gte` |
| `permissions` | Flags such as `catalog_read` |
| `observability` | Sink ids, including `platform_trace` and `evaluation` |
| `rag` | `retrieve`, `capture`, vector, and embedding |
| `model` | `provider` |

| Route | What it returns |
| --- | --- |
| `GET /settings/platform` | Mode, timeout, hop limit, whether a model key is set, the data directory, observability, and RAG choices. The key value is omitted |
| `GET /settings/agents/{agent_id}` | The contract view, including `output_schema` |
| `PUT /settings/agents/{agent_id}` | Writes the contract file and reloads it |
| `GET /settings/agents/{agent_id}/file` | The YAML file |
| `GET /settings/connections` | Connector addresses. A saved password is reported as set and is not returned |
| `PUT /settings/connections/{endpoint_id}` | `EndpointBody`: `url`, `connection_string`, `username`, `password`. A blank password keeps the stored one |
| `POST /settings/mcp-servers` | `McpServerBody`: `title`, `purpose`, `url`, `username`, `password`. Saves one MCP server. The token is not returned |
| `PUT /settings/mcp-servers/{server_id}` | Same body. A blank password keeps the stored token |
| `POST /settings/mcp-servers/{server_id}/check` | Sends the MCP initialize call and records whether the server answered |
| `DELETE /settings/mcp-servers/{server_id}` | Removes one onboarded MCP server |

## Memory

| Route | Body | What happens |
| --- | --- | --- |
| `POST /memory/notes` | `NoteBody` | `user_id` and `text`. `text` is at most 500 characters. Stores a note for later retrieval |

## Guide

| Route | Auth | What it returns |
| --- | --- | --- |
| `GET /guide` | bearer | Every `docs/*.md` page: `id`, `title`, and `markdown`. The Docs screen renders this |
| `GET /guide/assets/{name}` | none | One file from `docs/assets`, such as the architecture diagram |

## Add a route

1. Add a class in `agentic/01-entry/bodies.py` when the new call has a JSON body. Describe each field. That text is what `/docs` shows.
2. Add the route in the matching module: `agentic/01-entry/routes/runs.py`, `agentic/01-entry/routes/approvals.py`, `agentic/01-entry/routes/catalog.py`, `agentic/01-entry/routes/settings.py`, `agentic/01-entry/routes/mcp.py`, or `agentic/01-entry/routes/guide.py`. Check the bearer token. Call `platform`, the gateway, or another module under `agentic/`. Do not call a plugin from a route.
3. Name the console function that will send it, in the route's docstring.
4. Add the path to the console proxy in `ui/admin-dashboard/vite.config.ts` and in `infrastructure/nginx.conf`.
5. Add a case in `tests/integration/test_api.py`.
6. Add a row to this page.

A new agent is `agentic/04-loops/specialists/<name>/agent.yaml`. A new workflow is `agentic/03-workflows/sequences/<name>/workflow.py`. Neither one is a new body class.

# One server

Two images run on the server you operate. `agentic-api` is the platform process. `agentic-console` is the page operators open, on port 5173. The API is not published on the host. Approvals, traces, notes, and evaluation stay in that one API process.

`GET /platform` on the console port returns this map. The same fields are labels on the images. The sample token is `local-dev-token-not-for-production` until you set a private `PLATFORM_DEV_TOKEN`.

```bash
docker compose up -d --build
./deploy/smoke.sh
```

Open <http://127.0.0.1:5173>. `CONSOLE_PORT` changes that port. Health is `/health`. The seven steps, security, and observability are `/platform`. Interactive API docs are `/docs` on that same port.

`./start-local.sh` remains the laptop path. It binds the API to `127.0.0.1` and does not build an image.

## What the API image contains

| Step | Path | Role |
| --- | --- | --- |
| 1. Perception | `agentic/01-entry` | Turns the HTTP body into an `AgentRequest` |
| 2. Planning | `orchestrator` | Orders the agents and checks hops and delegation |
| 3. Foundation model | `agentic/04-loops/llm` | Chooses the next step. Mock mode needs no key |
| 4. Memory | `agentic/04-loops/memory` | Session, notes, and retrieval |
| 5. Action | `agentic/05-tools/mcp/tool-gateway` | The only plugin caller |
| 6. Learning | `agentic/07-observability/evaluation` | Status, tool names, and duration |
| 7. Communication | `agentic/08-response/contracts` | The `AgentResponse` the console shows |

Security is `agentic/02-guardrails`, the bearer check in `agentic/02-guardrails/auth/auth.py`, and the approval check in `agentic/05-tools/mcp/tool-gateway/gateway.py`. Observability is `agentic/07-observability`. The trace records the agent, the tool name, the status, and the duration. It does not store the raw question. OpenTelemetry, a log store, and Grafana are addresses on the contract. This process still keeps the record.

The console image is `ui/admin-dashboard`. It holds no secrets. Nginx proxies `/health`, `/platform`, `/agent-runs`, `/approvals`, `/plugins`, `/settings`, `/guide`, and `/memory` to the API.

## Where a business team edits

The retail fixtures are the worked example. Replace the data. Keep the runtime.

| Change | File |
| --- | --- |
| Instructions, tools, permissions, output schema | `agentic/04-loops/specialists/<name>/agent.yaml` |
| Catalog, order, billing, or support behavior | `agentic/05-tools/mcp/<domain>-tools/tools.py` |
| Register a plugin | `agentic/05-tools/mcp/tool-gateway/gateway.py` |
| SQL, web, or n8n stand-in | `agentic/05-tools/mcp/tool-gateway/ports.py` |
| Who may hand work to whom | `agentic/02-guardrails/policy/delegation.py` |
| Words that select a workflow | `agentic/03-workflows/router/router.py` |
| Agent order in a workflow | `agentic/03-workflows/sequences/<name>/workflow.py` |
| Evaluation case | `tests/agent-evaluation/cases.json` |

The router loads the agent order from the workflow file. A new specialist is a YAML file plus a plugin the gateway already knows. `agentic/04-loops/runtime/runtime.py` stays the only loop. A write stays in `approval.required_for`.

`GET /platform` includes `workflows` and `n8n`. The three sequences run in `agentic/03-workflows/engine`. n8n is the `invoke_n8n` tool, and that call waits for approval. The guide is [Workflows](workflows.md).

## Production on this server

1. Put a private token in `.env` as `PLATFORM_DEV_TOKEN`. Copy the names from `.env.example`.
2. Set `PLATFORM_ENV=production`. The sample token refuses to start.
3. Leave `PLATFORM_LLM_MODE=mock` until `MODEL_API_KEY` points at a model host you already run.
4. Rebuild with `docker compose up -d --build`.
5. Run `./deploy/smoke.sh` with that token in the environment.

`PLATFORM_DATA_DIR` is the `agentic-data` volume. Connection addresses survive a restart. Runs and traces still live in the API process and clear when that container is replaced. Set `MODEL_API_KEY`, `SQL_CONNECTION`, `WEB_ALLOWLIST`, `N8N_BASE_URL`, `QDRANT_URL`, and `NEO4J_URL` on the API service when those hosts exist. The console shows that a variable is set and does not show the value.

## Tests before you ship the image

```bash
.venv/bin/python -m unittest tests.unit.test_runtime tests.integration.test_api tests.security.test_security
.venv/bin/python tests/agent-evaluation/run.py
.venv/bin/python -m ruff check agentic tests
docker compose up -d --build
./deploy/smoke.sh
```

The unit suite checks the route, the plugins, the schema, a denied call, injection text, and approval. The smoke script checks the published port: eight agents, all seven steps, security, observability, and a catalog run that calls `search_products`.

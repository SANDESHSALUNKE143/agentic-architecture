# Operations

Observability, the tool ports, and the host stay for the life of the platform. An agent added years later uses the same trace, the same ports, and the same two processes.

## RAG

Each agent contract has a `rag` block and a `model` block. `retrieve` means the agent reads the index. `capture` means the agent stores a redacted note from the turn. Both start off, except the research agent, which reads the index and does not capture.

| Choice | Values | Variable |
| --- | --- | --- |
| Vector | local, Qdrant, AWS | `QDRANT_URL`, `AWS_VECTOR_INDEX` |
| Embedding | local, OpenAI-compatible, AWS Bedrock | `EMBEDDING_MODEL`, `AWS_EMBEDDING_MODEL` |
| Model | platform, OpenAI-compatible, AWS Bedrock | model key, `AWS_BEDROCK_MODEL` |

Local is the document index in this process. A set variable marks Qdrant or AWS configured. This build still answers from the local index and does not call AWS. The console does not show a password. Settings and Plugins edit the choice on the agent.

## Connection configuration

This repository does not host n8n, Grafana, Qdrant, or AWS. Plugins has a form for each system: direct URL, connection string, username, and password.

| System | What the URL is |
| --- | --- |
| n8n | The n8n you already run. There is no n8n process in this repository. |
| Grafana | The dashboard address. The password is saved locally and is not returned by the API. |
| OpenTelemetry | The collector endpoint. |
| Qdrant | The vector database used when an agent selects Qdrant. |
| AWS vector | The AWS endpoint. The access key is the username and the secret key is the password. |
| Embedding model and model host | The direct URL of each model service. |
| SQL | The connection string. A string typed in the console is shown again. A string that exists only in the environment is not shown. |
| Neo4j | The graph URL, username, and password. |

The file is `data/connections.json`. That directory is not committed. A blank password on save keeps the password already stored.

## Observability

Each agent contract names the observability tools it uses. The list is `observability` in `agent.yaml`. The Settings Observability tab and the Plugins page edit that list. The Settings Connectors tab stores the URL, connection string, username, and password. A saved password is not shown again.

| Tool | Variable | This reference |
| --- | --- | --- |
| Platform trace | In this process | Records the agent, the tool name, and the status. The raw question is not stored. |
| Evaluation | In this process | Records status, tool names, and duration. It does not change model weights. |
| OpenTelemetry | `OTEL_EXPORTER_OTLP_ENDPOINT` | Marks the collector configured. The trace stays in this process. |
| Log store | `OBSERVABILITY_LOG_URL` | Marks the store configured. The trace stays in this process. |

The record lives in the API process. `agentic/07-observability/trace/trace.py` keeps the trace. `agentic/07-observability/evaluation` keeps the score. The console shows both while a run is open. This repository does not ship events to a vendor product.

| Stage | What is stored |
| --- | --- |
| `load_instructions` | Agent id and the tool names on its contract |
| `tool` | Agent id, tool name, and status |
| `reason` | Agent id |
| `persist` | Agent id and the response status |

The evaluation row stores the run id, agent id, status, tool names, and duration in milliseconds. `POST /agent-runs/{run_id}/feedback` stores whether the answer was helpful and a note of at most 240 characters. The live Run screen shows activity, the plan, each step, each tool, and the finished response. `GET /health` returns status, model mode, and the agent count. Settings shows the mode, the timeout, the hop limit, whether `MODEL_API_KEY` is set, and the data directory. It does not show the key.

The raw question is not stored. A secret value is not stored. Model weights are not changed. When the API process stops, the trace, the evaluation rows, the runs, the approvals, and the notes are gone. `TraceLog.export` returns the JSON for one run. A later log store reads that shape and still omits the raw question.

`agentic/06-jobs/queue/checks.py` runs a named check inside this same process. It is not a second service and it is not a queue.

## Tools you configure over years

The contract names the plugin. The environment names the system behind it. Changing the host does not change `agent.yaml`, the permission, or the approval rule. The console Plugins page shows whether each variable is set. It never shows the value.

| Port | Variables | This reference, when the variable is set | What you replace later |
| --- | --- | --- | --- |
| Model | `PLATFORM_LLM_MODE=live`, `MODEL_API_KEY`, `MODEL_BASE_URL`, `MODEL_NAME` | Calls an OpenAI-compatible `/chat/completions` endpoint. Copies `model`, `total_tokens`, and `cost` when the provider sends them. | Point `MODEL_BASE_URL` at your model host. Leave mock mode until that host exists. |
| SQL | `SQL_CONNECTION` | Marks the port configured. `query_sql` still returns the local read-only row. A statement that is not a `SELECT` is rejected. | The body of `query_sql` in `agentic/05-tools/mcp/tool-gateway/ports.py`. Keep the `SELECT` limit. |
| Web | `WEB_ALLOWLIST` | The host must be on the list, or the call is denied. The page body is still the local fixture. The default list is `example.test`. | The body of `fetch_url`. Keep the allowlist. |
| n8n | `N8N_BASE_URL`, `N8N_TOKEN` | Marks the port configured. `invoke_n8n` does not call n8n. `submitted` stays false and `simulated` stays true. The write still waits for approval. The token stays in the API environment. | The body of `invoke_n8n`, after approval, using `N8N_TOKEN` from the environment. |
| Vector search | `QDRANT_URL` | Marks the port configured and returns a short configured message. With no URL, search uses the local document index. | `VectorPort.query` in `agentic/04-loops/memory`. |
| Graph | `NEO4J_URL` | Marks the port configured and returns a short configured message. It does not open a Neo4j session. With no URL, `GraphPort` returns nothing. Memory retrieval still uses the local entity graph in `agentic/04-loops/memory/corpus.py`. | `GraphPort.query` in `agentic/04-loops/memory`. |

No agent may call `query_sql`, `fetch_url`, or `invoke_n8n` until its contract sets `sql_read`, `web_read`, or `n8n_write`. The console cannot grant that permission and cannot paste a tool URL.

Catalog, orders, billing, support, documents, and `agentic/04-loops/memory/fixtures/sales.csv` are the reference domain. Years later you replace the function behind the same tool name. The agent files that already list that name stay as they are.

Leave every port on its local stand-in until the real host exists. Turn on one variable, prove the evaluation case, then turn on the next.

## Infrastructure

### Reference host

`./start-local.sh` runs both processes on the machine in front of you. Nothing in this repository is published to another network.

| Process | Where it listens | What it is |
| --- | --- | --- |
| API | `127.0.0.1:8090` | `agentic/01-entry/main.py`. Another machine cannot open this port. |
| Console | `127.0.0.1:5173` | `ui/admin-dashboard`. The browser talks only to this port. The console proxies `/health`, `/platform`, `/agent-runs`, `/plugins`, `/approvals`, `/settings`, `/guide`, and `/memory` to the API. |

The interpreter is `.venv` in the repository root. The sample token is `PLATFORM_DEV_TOKEN`, default `local-dev-token-not-for-production`, sent as `Authorization: Bearer`. Health is `GET /health`. Interactive API docs are `GET /docs` on the API.

`PLATFORM_DATA_DIR` defaults to the `data/` directory next to the code. That directory is the place for files the process creates. Runs and traces are not written there in this reference. They stay in the API process.

`docker compose up -d --build` is the same two processes on one server. The console image publishes port 5173. The API image stays on the server network. [One server](server.md) names the seven steps, security, observability, and the files a business team edits. `GET /platform` returns that map. `./deploy/smoke.sh` proves the published port.

### Industry host

Keep the same two processes when you leave the laptop.

1. Run one API process on a private address inside your network. `docker compose` does this: the `agentic-api` service has no host port. Approvals, traces, notes, and evaluation live in that process. A second copy would not see a pending approval. Add a shared store before you run more than one API.
2. Run the console where operators open a browser. Point its proxy at the private API. The console build holds no secrets.
3. Put secrets only in the API environment: `PLATFORM_DEV_TOKEN`, `MODEL_API_KEY`, `N8N_TOKEN`, and `SQL_CONNECTION`.
4. Set `PLATFORM_ENV=production` only with a private token. The sample token refuses to start.
5. Leave the model, SQL, n8n, Qdrant, and Neo4j as other hosts you already run. This repository does not install them. Set the matching variable when that host exists. Until then the local fixture remains.
6. Put `PLATFORM_DATA_DIR` on a disk that survives a process restart when you start writing files there. The in-memory trace still clears on restart until you export it.

The check before a host change is the same suite the repository already runs: unit, API, security, evaluation, and Ruff.

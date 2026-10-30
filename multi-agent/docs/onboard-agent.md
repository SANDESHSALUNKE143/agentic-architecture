# Onboard an agent

State the problem. One command writes the agent, the tool, and the workflow. You replace the tool body with the system that solves the problem. The retail agents are a sample. They are not part of the path you extend.

The runtime loads every folder under `agentic/04-loops/specialists/`, every `workflow.yaml`, and every `TOOLS` map under `agentic/05-tools/mcp/`.

Restart the API after a file change. A save from the console reloads that one contract without a restart.

## Start from the problem

```bash
./new-agent.sh claims "Look up whether a claim is open and explain the next step"
```

That writes:

| File | What you do with it |
| --- | --- |
| `agentic/04-loops/specialists/claims-agent/agent.yaml` | The contract. The description is the problem. Change instructions, the output fields, or the phrase when the problem needs it. |
| `agentic/05-tools/mcp/claims-tools/tools.py` | The only file that talks to your system. Replace `lookup_claims`. Keep the `TOOLS` entry, or add another tool beside it. |
| `agentic/03-workflows/sequences/claims/workflow.yaml` | The phrase `claims` selects this agent. Add more agents to `agents` when the problem needs a sequence. |
| `tests/agent-evaluation/cases.json` | One case that expects `lookup_claims`. |

Restart the API and send the task `claims`. Mock mode calls `lookup_claims` and returns the brief, with an explanation that the function body is still the stand-in. When that function calls your system, the same run returns your system's answer. The console lists the new agent. Chat offers the phrase as the sample brief.

A permission that the contract sets to false stays off. The console cannot turn it on. A write tool stays in `approval.required_for`.

## Add an agent that uses tools you already have

1. Run `./new-agent.sh`, or copy `agentic/04-loops/specialists/catalog-agent/agent.yaml` to `agentic/04-loops/specialists/<name>/agent.yaml`.
2. Set `name` to the folder name. Change the instructions, the `tools` list, the `permissions`, and the `output_schema`. Name only tools the gateway already loaded.
3. Add `examples` when the console should offer sample briefs. The chat reads those lines from `GET /agents`.
4. Add a `route` block when a task phrase should select this agent by itself:

```yaml
route:
  id: claims
  priority: 15
  phrases:
    - claim status
    - my claim
```

Lower `priority` is checked first. A workflow file with a lower number wins over this agent.

5. Leave `delegation.handoff` unset, or set it to `read`, when this agent may hand work to any other read agent. Set `handoff: write` when a hop to this agent must be named. On the agent that may call it, list the target:

```yaml
delegation:
  handoff: write
  delegates_to:
    - billing-agent
```

A write tool still waits for approval inside the gateway. `handoff` only decides who may be next in the plan. The sample order agent is `write`. The sample support agent stays `read` because the refund tool waits for approval and the next agent is a read hop.

6. Add one case in `tests/agent-evaluation/cases.json` with the tool the run must call.
7. Restart the API. The agent appears on the dashboard. Authentication, logging, errors, and run state stay in the shared runtime.

## Add a tool

1. Create `agentic/05-tools/mcp/<domain>-tools/tools.py`.
2. Export `TOOLS`. Each entry needs `permission`, `write`, `fn`, `schema`, and a short `summary`. Set `mcp_purpose` when the call goes to an MCP server, or `endpoint` when it uses a saved connection.
3. Put `permission: true` on the agent contract, and add the tool name to `tools`. A write also belongs in `approval.required_for`.
4. Restart the API. The Plugins page lists the tool. The console can connect it only to an agent that already has the permission.

Shared ports such as SQL, web, and n8n stay in `agentic/05-tools/mcp/tool-gateway/ports.py`. They use the same `TOOLS` shape.

## Add a workflow

Create `agentic/03-workflows/sequences/<name>/workflow.yaml`:

```yaml
name: claims-review
order: 4
priority: 25
agents:
  - claims-agent
  - billing-agent
phrases:
  - open claim
  - claim review
```

`agents` is the order LangGraph runs. `phrases` select this file when the request does not name a workflow or an agents list. `order` is the console list. `priority` is the phrase check: a lower number is tested first.

A caller can also send `"workflow": "claims-review"` and skip the phrases. An `agents` list on the request wins over both.

Read agents may hand work to each other. A hop into an agent with `handoff: write` must be listed on the source contract under `delegation.delegates_to`.

## What stays untouched

| Do not edit this to add an agent | The process reads this instead |
| --- | --- |
| `agentic/03-workflows/router/router.py` | `workflow.yaml` phrases and each contract `route` |
| `agentic/02-guardrails/policy/delegation.py` | `delegation` on `agent.yaml` |
| `agentic/05-tools/mcp/tool-gateway/registry.py` | `TOOLS` in the domain `tools.py` |
| `agentic/04-loops/runtime/runtime.py` | The same loop runs every contract |

## Prove the path with no model key

Mock mode is the default. It needs no key and it calls the same tools, the same gateway, and the same trace as a live model.

```bash
./start-local.sh
```

Open <http://127.0.0.1:5173>. The header says **Mock mode**. The token is `local-dev-token-not-for-production`.

Send:

```text
Find a blue trail jacket under $150
```

You should see the plan `product-discovery`, then shopping, catalog, and inventory, and a `search_products` tool event. The trace records the agent, the tool name, the status, and the duration. It omits the question.

`./start-local.sh` also starts the sample merchant at <http://127.0.0.1:8091/mcp>. Catalog, order, billing, and support tools read that process. A new agent with its own tool does not need the merchant. It needs whatever system that tool calls.

## Prove the path with Azure OpenAI

The key is not enough. The API has to know which Azure resource and which deployment to call, and the run has to be allowed enough time to finish.

Put this in `.env` in the repository root. Do not commit that file. `./start-local.sh` loads it. Docker Compose reads the same names.

```text
PLATFORM_LLM_MODE=live
MODEL_API_KEY=your-azure-openai-key
MODEL_BASE_URL=https://YOUR_RESOURCE.openai.azure.com/openai/v1
MODEL_NAME=YOUR_DEPLOYMENT_NAME
PLATFORM_TIMEOUT_SECONDS=120
```

| You provide | Why |
| --- | --- |
| Azure OpenAI key | `MODEL_API_KEY`. The console shows that a key is set and does not show the value. |
| Resource endpoint | `MODEL_BASE_URL`. Use the OpenAI-compatible path ending in `/openai/v1`. The client sends `Authorization: Bearer` and Azure's `api-key` header. |
| Deployment name | `MODEL_NAME`. This is the deployment, not the model catalog name, unless they are the same. |
| A tool-calling chat deployment | The loop is LangChain `create_agent` through `langchain-openai`. The deployment must accept tool calls. Reinstall the project if this environment was created before that package was required: `.venv/bin/pip install -e .` |
| A longer timeout | The mock default is 8 seconds. A live model plus tool calls needs `PLATFORM_TIMEOUT_SECONDS=120` or the run ends before the model returns. |
| The sample token, until you replace it | `Authorization: Bearer local-dev-token-not-for-production` while `PLATFORM_ENV` stays `development`. |
| The sample merchant, for the retail tools | `./start-local.sh` starts it and sets `MERCHANT_MCP_URL`. |

You do not need SQL, Qdrant, Neo4j, n8n, Grafana, or an OpenTelemetry collector for this check. Leave those variables unset.

Restart with `./start-local.sh`. Confirm the process is live before you send a task:

```bash
curl -s -H "Authorization: Bearer local-dev-token-not-for-production" http://127.0.0.1:8090/health
```

`mode` is `live`. The console header says **Live model**. The dashboard Mode metric says the same.

Send the jacket task again, or send one agent only so you can watch a single loop:

```bash
curl -s -H "Authorization: Bearer local-dev-token-not-for-production" \
  -H "Content-Type: application/json" \
  -d '{"task":"Find a blue trail jacket under $150","agents":["catalog-agent"]}' \
  http://127.0.0.1:8090/agent-runs
```

In the console chat, the page updates as the run moves: the agent loaded its instructions, it is choosing a step, then each tool name and status. The finished run lists `agents`, `tool_calls`, and `trace`. A trace stage is `load_instructions`, `reason`, `tool`, or `persist`. The question is not in the trace.

A live model chooses its own tool calls. If it never calls a tool, or the result misses `output_schema`, that agent's status is `failed` and `errors` includes `schema_invalid`. The trace still shows how far the loop got. Pin one agent with `"agents": ["catalog-agent"]` when you want a shorter live check than the three-agent discovery workflow.

On one server, the same variables belong in `.env` beside `docker-compose.yml`. Compose passes `MODEL_API_KEY`, `MODEL_BASE_URL`, `MODEL_NAME`, and `PLATFORM_TIMEOUT_SECONDS` into the API container. `docker compose up -d --build` restarts it with the key.

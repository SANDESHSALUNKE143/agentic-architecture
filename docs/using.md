# Using this repository

This is the reference an industry team runs and then copies. The retail agents are the worked example. The contract, the gateway, and the approval rule stay. Start here. The [implementation guide](implementation-guide.md) is the page to read before you change code. The [API](api.md) lists every route.

Each source file opens with its purpose and who calls it. `agentic/01-entry/app.py` mounts the routes. The JSON bodies live in `agentic/01-entry/bodies.py`. Run flow is `agentic/03-workflows/runs.py`. Contract saves are `agentic/platform/contract_edit.py`. Plugin listing is `agentic/platform/catalog.py`.

## Start it

On a laptop, from the repository root:

```bash
./start-local.sh
```

Open <http://127.0.0.1:5173>. The API is <http://127.0.0.1:8090>. The token is `local-dev-token-not-for-production`. Send it as `Authorization: Bearer`.

`start-local.sh` also starts the example merchant MCP server at <http://127.0.0.1:8091/mcp> and sets `MERCHANT_MCP_URL` for the API. That process owns the sample products, orders, and discounts in `examples/merchant-mcp/records.json`. Catalog, order, billing, and support tools call it. To use another system, open that tool on Plugins and save its Server URL, or set `MERCHANT_MCP_URL` to its address.

On one server:

```bash
docker compose up -d --build
./deploy/smoke.sh
```

Operators open port 5173. `CONSOLE_PORT` changes that port. The API is on the server network. Health, the platform map, this guide, and the interactive API page are all on the console port: `/health`, `/platform`, `/guide`, and `/docs`.

Copy names from `.env.example` when you leave the sample token. `PLATFORM_ENV=production` refuses that token until `PLATFORM_DEV_TOKEN` is private.

## Walk the console

| Page | What you do |
| --- | --- |
| Dashboard | See the loaded agents, pending approvals, and runs from this browser session |
| Agent chat | Brief one agent and read the answer |
| Agent library | Open a contract in its chat |
| Run history | See runs started in this browser session |
| Approvals | Approve or reject a paused write. The actor must differ from the agent |
| Plugins | List every tool, save its server URL, and save host connection strings |
| Configuration | Edit one agent's contract. The gear on any screen opens this page for that agent |
| Docs | Read this page, the API reference, and the standard |

The gear is `GearButton` from `ui/packages/controls`. Text boxes, checkboxes, radios, and dropdowns come from that same package.

On an agent's Configuration page, the Workflows tab shows the sequences that include that agent. The list comes from `GET /platform`.

## Run a task

In Agent chat, with the catalog agent or with no agent pinned, send:

```text
Find a blue trail jacket under $150
```

The router matches `product-discovery`. Shopping runs, then catalog, then inventory. Catalog calls `search_products`. The trace shows the agent, the tool name, the status, and the duration. It omits the raw question.

Send this when you want to see approval:

```text
Place an order for the jacket at $129
```

That matches `order-processing`. The order agent calls `prepare_order`. The amount meets `amount_gte` on the order contract, default 100, so the run pauses. Open Approvals, set the actor to a name other than the order agent, and approve. Billing then looks for a discount.

You can also name the sequence yourself. `POST /agent-runs` accepts `workflow`. An `agents` list wins over that name and over the phrases. The rules are in [Workflows](workflows.md).

## Call the API

From the laptop, talk to port 8090. From the server, talk to the console port. The console proxies the API paths.

```bash
TOKEN=local-dev-token-not-for-production
curl -s -H "Authorization: Bearer $TOKEN" http://127.0.0.1:8090/health
curl -s -H "Authorization: Bearer $TOKEN" http://127.0.0.1:8090/platform
curl -s -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d '{"task":"Find a blue trail jacket under $150"}' \
  http://127.0.0.1:8090/agent-runs
```

Open <http://127.0.0.1:8090/docs> on the laptop, or <http://127.0.0.1:5173/docs> on the server. That page is generated from the bodies in `agentic/01-entry/bodies.py` and the routes beside `app.py`. Authorize with the bearer token, then try a route. The written list, including errors, is [docs/api.md](api.md).

## Change the example

| You want to | Open |
| --- | --- |
| Change what an agent may say and which tools it has | `agentic/04-loops/specialists/<name>/agent.yaml`, or the gear in the console |
| Change a catalog, order, billing, or support result | `agentic/05-tools/mcp/<domain>-tools/tools.py` |
| Add a plugin | Register it in `agentic/05-tools/mcp/tool-gateway/gateway.py`, then name it on a contract that already has the permission |
| Change who may hand work to whom | `agentic/02-guardrails/policy/delegation.py` |
| Change which words select a workflow | `agentic/03-workflows/router/router.py` |
| Change the agent order | `agentic/03-workflows/sequences/<name>/workflow.py` |
| Attach n8n later | `invoke_n8n` in `agentic/05-tools/mcp/tool-gateway/ports.py`, after the contract has `n8n_write` and approval |

Restart the API after a file change. A save from the console reloads that one contract without a restart.

`agentic/04-loops/runtime/runtime.py` stays the only loop. The gateway stays the only plugin caller. A write stays in `approval.required_for`.

## Check it

```bash
.venv/bin/python -m unittest tests.unit.test_runtime tests.integration.test_api tests.security.test_security
.venv/bin/python tests/agent-evaluation/run.py
.venv/bin/python -m ruff check agentic tests
npm test --prefix ui/admin-dashboard
docker compose up -d --build && ./deploy/smoke.sh
```

## Read next

| Page | Use it when |
| --- | --- |
| [API](api.md) | You are calling a route or adding a body class |
| [Workflows](workflows.md) | A sequence is required, or you are placing n8n |
| [One server](server.md) | You are running the two images |
| [Implementation guide](implementation-guide.md) | You are changing the platform and must keep the standard |
| [Operations](operations.md) | You are setting a model, SQL, web, n8n, Qdrant, or Neo4j host |
| [Agent catalog](agent-catalog.md) | You are copying a specialist |
| [Tool contracts](tool-contracts.md) | You need a plugin's permission and whether it waits |
| [Console controls](ui-controls.md) | You are adding a field to the console |

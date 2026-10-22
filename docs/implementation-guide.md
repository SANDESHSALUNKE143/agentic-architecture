# Implementation guide

This repository is the reference an industry team copies when it builds the agentic platform it has announced. The retail specialists are the worked example. The folders, the contract, the gateway, and the approval rule are the standard. Replace the example data. Keep the standard.

## What you adopt

| Keep | Replace with your industry |
| --- | --- |
| One `agent.yaml` per specialist | The names, instructions, and output fields |
| `agents/runtime.py` | Nothing. Every agent uses this loop |
| `mcp/tool-gateway` | Your plugins, registered the same way |
| Approval before a write | The amount or action that must wait |
| Secrets only in the environment | `MODEL_API_KEY`, SQL, web, n8n, Qdrant, Neo4j |
| Evaluation of status, tools, and duration | Your cases in `tests/agent-evaluation/cases.json` |

The reference does not place an order, send a refund, or dispatch work. A write returns a simulated result until your team deliberately connects a real system, and it still waits for approval.

## Standard an implementation must meet

1. **Contract before code.** Responsibility, tools, permissions, and the output schema are in `agent.yaml` before a reasoning loop is written. LangChain does not own that file.
2. **One runtime.** Authentication, logging, errors, and run state stay in `shared/` and `orchestrator/`. A new agent does not copy them.
3. **One gateway.** A plugin runs only when the contract lists it and the permission is true. The model cannot widen that list.
4. **Writes wait.** `approval.required_for` names every write plugin. The console cannot clear that requirement. The order example reads `amount_gte` from the order contract. The default is 100.
5. **Permissions stay on the contract.** The console can connect a plugin only to an agent that already has the permission. It cannot grant `order_write` to a read-only agent, and it cannot add a tool URL.
6. **Results match the schema.** The runtime rejects a result that does not match `output_schema`.
7. **Memory is retrieved, not invented.** `long_term_memory: optional` means the agent may read a saved note. It must not claim a memory it did not retrieve. Citations must be known source ids.
8. **The trace is operational.** It records status, tool name, and duration. It does not store the raw question, and it does not change model weights.
9. **Untrusted text is not an instruction.** Lines that try to override the contract are removed before the model sees them.
10. **An operator cannot approve their own agent.** The actor on the approval must be different from the agent that asked.
11. **Production refuses the sample token.** `PLATFORM_ENV=production` with `local-dev-token-not-for-production` does not start.
12. **Tests name the control.** Ship a case for the correct route, the correct plugin, schema validation, a denied plugin, ignored injection text, a blocked write, and any threshold read from the contract.

Ruff checks the Python with the rules in `pyproject.toml`. Line length is 100.

## Where each change goes

| Change | Place it here |
| --- | --- |
| New specialist | `agents/<name>/agent.yaml` |
| New plugin | A function in the matching `mcp/<domain>-tools/tools.py`, then one entry in `mcp/tool-gateway/gateway.py` |
| Who may call whom | `shared/security/delegation.py` |
| Which words select a workflow | `orchestrator/router/router.py` |
| A fixed sequence of agents | `workflows/<name>/workflow.py` and the same list in the router |
| A regression | `tests/unit`, `tests/integration`, `tests/security`, or `tests/agent-evaluation/cases.json` |
| Operator-facing explanation | `docs/` |

Do not put a second tool loop in an agent folder. Do not call a plugin from the API. Do not store a key in YAML or in the dashboard.

## Build sequence

1. Run `./start-local.sh` and complete the jacket task. Read the trace.
2. Read `agents/catalog-agent/agent.yaml` until the contract fields are familiar.
3. Name your specialists and the permissions they need. Copy the catalog contract and change only those fields.
4. Register each industry plugin in the gateway with a permission and `write: true` or `write: false`.
5. Connect the plugin in the console only to agents that already have that permission.
6. Add one evaluation case that names the plugin the test must see.
7. Turn on one long-lived port at a time. The order is model, SQL, web allowlist, n8n, Qdrant, Neo4j. Leave the others on the local fixture. See [Operations](operations.md).
8. Set `PLATFORM_ENV=production` only with a private `PLATFORM_DEV_TOKEN`, and only on the private API host described in [Operations](operations.md).

## Reference domain

The eight agents are a retail desk: shopping, catalog, inventory, support, orders, billing, analysis, and research. Use them to prove the platform, then swap the fixtures.

| Your system | Reference plugin | Local stand-in |
| --- | --- | --- |
| Product search | `search_products`, `get_product_details`, `compare_products` | Three products in `mcp/catalog-tools` |
| Stock | `check_stock` | Stock on those products |
| Orders | `get_order_status`, `prepare_order` | Orders 1001 and 1002. Prepare never submits |
| Discounts | `get_eligible_discounts` | One rule: the local user and the blue jacket |
| Case work | `request_approval` | A refund request that waits |
| Documents | `search_documents` | `shared/memory` corpus |
| Reporting | `analyze_dataset` | `shared/fixtures/sales.csv` |
| Warehouse SQL | `query_sql` | A local `SELECT` until `SQL_CONNECTION` is set |
| Allowed sites | `fetch_url` | `example.test` until `WEB_ALLOWLIST` is set |
| Existing automation | `invoke_n8n` | Simulated. `N8N_BASE_URL` only marks the port configured. The call still waits for approval |

## Observability

Every run writes a trace in the API process: the agent, the tool name, the status, and the duration. The console shows that trace while the run is open. The raw question is not stored. A secret is not stored. Model weights are not changed. The record is gone when the API process stops. `TraceLog.export` is the JSON a later log store may read. The field list, the feedback call, and the health check are in [Operations](operations.md).

## Tools that stay configurable

These ports are how the platform grows without a new runtime. The contract keeps the plugin name. The environment points at the host. You can attach each one years later.

| Port | Variable | This reference |
| --- | --- | --- |
| Model | `MODEL_API_KEY` and `PLATFORM_LLM_MODE=live` | Calls the model host |
| SQL | `SQL_CONNECTION` | Marks SQL configured. The call stays on the local `SELECT` fixture |
| Web | `WEB_ALLOWLIST` | Denies a host that is not listed. The page body stays local |
| n8n | `N8N_BASE_URL` and `N8N_TOKEN` | Does not call n8n. The write stays simulated and still needs approval |
| Vector search | `QDRANT_URL` | Marks Qdrant configured. Empty means the local document index |
| Graph | `NEO4J_URL` | Marks Neo4j configured. It does not open a Neo4j session. Memory retrieval still uses the local entity graph |

`N8N_TOKEN` and the other secrets stay in the API environment. The console shows that a variable is set and does not show the value. No agent calls SQL, web, or n8n until its contract already has `sql_read`, `web_read`, or `n8n_write`.

## Where it is hosted

The reference host is the machine you start with `./start-local.sh`. The API listens on `127.0.0.1:8090`. The console listens on `127.0.0.1:5173` and is the only page a browser opens. The API is not reachable from another machine. There is no container file and no cloud account in this repository.

An industry host keeps those two processes. The API stays on a private address, as one process, because approvals and traces live in that process. The console is what operators open, and its proxy points at that private API. The model, the database, n8n, Qdrant, and Neo4j are separate hosts you already run. You set one variable when that host is ready. The placement rules are in [Operations](operations.md).

## Operate it

| Console page | Operator uses it to |
| --- | --- |
| Run | Send a task, choose automatic routing, a workflow, or specific agents, and read the live trace |
| Agents | See each contract and start a run with that agent |
| Plugins | Connect a registered plugin to an allowed agent |
| Approvals | Approve or reject a paused write |
| Settings | Edit instructions, connected plugins, memory, and the approval amount |
| Docs | Read this standard, operations, the folder map, the architecture, the catalog, and the tool list |

## Definition of done

An industry implementation is ready to show when a new agent is only a YAML file plus a registered plugin, a denied plugin never runs, a write stays paused until a different actor approves it, the output matches the schema, and the evaluation case fails if the expected plugin is missing.

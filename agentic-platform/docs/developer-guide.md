# Developer guide

This file is the index of every runnable example. Architecture, the agent catalog, and the tool contracts link here.

Install the platform extras from the repository root:

```sh
python -m pip install -e '.[runtime,service,dev]'
```

LangChain and LangGraph samples also need:

```sh
python -m pip install -e '.[frameworks]'
```

A missing frameworks extra stops those runners with that install command.

## How to run one example

Replace `EXAMPLE` with an id from the tables below.

```sh
python agentic-platform/examples/python/run.py EXAMPLE
python agentic-platform/examples/langchain/run.py EXAMPLE
python agentic-platform/examples/langgraph/run.py EXAMPLE
```

The dashboard Examples screen starts the same ids through `POST /agent-runs` with `example_id`.

## Workflows

| Example | Agents | Trace should show |
| --- | --- | --- |
| `product-discovery` | shopping, catalog, inventory | `search_products`, then `check_stock`, short-term memory |
| `customer-support` | customer service, support, billing | `get_order_status`, then discounts |
| `order-processing` | order, billing | pause with `approval_required` before submit |
| `agent-chain` | catalog, inventory | the caller's list, both tool calls |
| `field-response` | coordinator, satellite, social, simulation, logistics | four reads, then a dispatch approval |

## Agents

Each `agent-<id>` example runs that specialist's sample task. Ids:

`catalog-agent`, `shopping-agent`, `customer-service-agent`, `support-agent`, `inventory-agent`, `order-agent`, `billing-agent`, `personal-shopping-agent`, `data-analysis-agent`, `research-agent`, `scientific-research-agent`, `enterprise-admin-agent`, `software-agent`, `marketing-agent`, `coordinator-agent`, `satellite-agent`, `social-media-agent`, `simulation-agent`, `logistics-agent`, `supplier-agent`, `agriculture-agent`, `healthcare-agent`.

Write samples stop at `needs_approval`. Healthcare sets `requires_qualified_review`.

## Memory, loop, review, feedback, learning

| Example | What the trace shows |
| --- | --- |
| `short-term-memory` | `memory: short_term` from catalog to inventory |
| `long-term-memory` | an approved note, then `memory: long_term` on the next jacket run |
| `agent-loop` | two `search_documents` calls and an observe step |
| `human-review` | order pauses, approval continues into billing |
| `feedback` | a feedback id stored on the run |
| `self-learning` | the next jacket task has `learned_from` and starts at catalog |

Learning changes the next route only. It does not add tools or skip approval.

## RAG

| Example | Pattern | Citation |
| --- | --- | --- |
| `rag-classic` | retrieve, then answer | `doc-jackets` |
| `rag-agentic` | search, observe, search again | chunks from the second search |
| `rag-graph` | one named-entity hop | `graph:Jacket:...` |
| `rag-hybrid` | keyword plus hash embedding | `signals` includes `keyword` |
| `rag-corrective` | empty retrieval stays empty | summary says the sources do not establish it |
| `rag-multi-hop` | search, expand, search | document id and a graph id |

Local hash embeddings and an in-memory graph are what this prototype searches. `QDRANT_URL` and a Neo4j session are not connected here.

## Trace and n8n

| Example | Trace |
| --- | --- |
| `failed-run` | healthcare to order is `delegation_denied`. Earlier router and planner steps remain. |
| `n8n-chain` | `POST /webhook/product-discovery` runs product discovery in process |

Importable n8n files live in `workflows/n8n/`. A live outbound webhook uses `N8N_BASE_URL` and still requires approval. The model cannot choose the URL.

## MCP stdio server

The HTTP API is not an MCP server. Read-only tools are also exposed by a stdio server that uses the installed MCP SDK (`MCPServer` on mcp 2.x, `FastMCP` on mcp 1.x):

```bash
python -m pip install 'mcp'
python agentic-platform/mcp/tool-gateway/server.py
```

An MCP client connects over stdin/stdout. The server registers `search_products`, `get_product_details`, `check_stock`, `get_order_status`, `get_eligible_discounts`, `search_documents`, and `analyze_dataset`. Writes stay on the HTTP approval flow. If `mcp` is not installed, the process exits and prints the install command.

## What a failure looks like

`GET /agent-runs/{id}` always returns `trace` and `errors`. `errors` lists failed, blocked, and approval-waiting steps with `error_code` and `message`. The Trace screen puts those in **What went wrong**. `POST /agent-runs/{id}/cancel` stops a run that is still executing. The trace then shows `cancelled`.

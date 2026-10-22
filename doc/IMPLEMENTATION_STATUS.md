# Implementation status

The runnable prototype lives in `agentic-platform/`. The existing `agentic_sdk` package under `src/` is unchanged. This repository keeps docs in `doc/`, so this file is the status report named by the implementation plan.

Verified on 2026-10-21 with the repo virtualenv `.venv` (Python 3.12) and Node for the dashboard.

## What runs

A local mock platform: FastAPI on `127.0.0.1:8090`, a Vite React TypeScript dashboard on `127.0.0.1:5173`, and a CLI. No LLM key, Qdrant, Neo4j, or live n8n server is required. Writes stop at `needs_approval` and do not call the tool until a different actor approves. Healthcare cannot hand off to order, billing, logistics, or enterprise-admin.

22 agent folders are loaded and exposed by `GET /agents`. The router is `orchestrator/router`, not an agent folder. Named workflows are product-discovery, customer-support, order-processing, and field-response. `agent-chain` runs an explicit allowlisted list. Self-handoff is blocked. The hop cap is 6. Repeated agent pairs stop with `loop_detected`.

Retrieval is local keyword overlap plus a hash embedder, with an in-memory graph. Citations are returned only for retrieved chunks or graph neighbors. Empty retrieval says the sources do not establish the answer. `QDRANT_URL` and Neo4j are not wired.

Learning can change the next route only. It cannot add tools, skip approval, or edit the delegation matrix. A feedback note that mentions catalog and is rated `not_helpful` stores a jacket-to-catalog example. The next jacket task that does not name a workflow uses that route. The live API showed this: after that feedback, “Find a jacket and check whether it is available” completed as `catalog-agent` only, with `learned_from` set.

## Commands and results

| Command | Result |
| --- | --- |
| `.venv/bin/ruff check agentic-platform` | All checks passed |
| `cd agentic-platform && ../.venv/bin/python -m unittest discover -s tests -q` | 27 tests, OK (0.636s) |
| `python agentic-platform/tests/agent-evaluation/run.py` | discover, support, and research passed |
| `python agentic-platform/examples/python/run.py product-discovery` | `completed`, summary `p-jacket-blue is in stock.` |
| `python agentic-platform/examples/langchain/run.py rag-classic` | `completed`, cited the jacket passage |
| `python agentic-platform/examples/langgraph/run.py human-review` | `completed`, `10% off p-jacket-blue (trail-club).` |
| `cd agentic-platform/apps/admin-dashboard && npm install && npm run build` | `tsc --noEmit` and Vite build succeeded. npm audit: 0 vulnerabilities |
| MCP server smoke (`mcp` 2.3.0, `MCPServer.run` patched to list tools) | Registered the 7 read-only tools |
| `python -m unittest discover -s tests -q` after the follow-up | 36 tests, OK. Includes timeout, cancel, step limit, repeated tool call, output schema, unknown citation, usage copy, and an in-process MCP `list_tools` handshake |

Headless Chrome against `http://127.0.0.1:5173` (API already on 8090):

- Run submitted the default jacket task, opened Trace, and showed a completed catalog result after the learned route.
- Agents rendered 22 cards. Run sample opened a trace.
- Examples listed the RAG, memory, learning, and trace buttons. Failed run showed **What went wrong** with `delegation_denied` and “Healthcare cannot hand off into order submission.”
- Order processing paused at `needs_approval`. Approve on the trace completed the run. A second order was rejected from Approvals and the trace status was `rejected`.
- Graph RAG showed `graph:Jacket` citations. Save feedback returned no error banner.
- A 390px-wide viewport of the Run screen did not scroll horizontally.

`pip-audit` is not installed, so a Python advisory scan did not run.

## Still open

These need a credential or a service this prototype must not call:

- A live model call (`PLATFORM_LLM_MODE=live` and `MODEL_API_KEY`). The client copies `model`, `total_tokens`, and `cost` when a response includes them. No key is configured, so that path is not executed against a provider.
- Qdrant and Neo4j. Retrieval stays on the local corpus and graph.
- A real n8n instance. Inbound webhooks are the local mock.
- Production OIDC. Local runs use the dev token, which production startup rejects.
- Real purchases, refunds, dispatch, provisioning, or clinical actions. Writes stay simulated and approval-gated.

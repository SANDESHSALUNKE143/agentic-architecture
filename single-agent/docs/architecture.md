# Architecture

`desk-agent` is the only specialist. A request walks the numbered folders in order.

![How one brief becomes an answer](assets/architecture.svg)

1. **Perception.** `agentic/01-entry` turns the body into a task, a user, and a session.
2. **Guardrails.** `agentic/02-guardrails` checks the bearer token, the rate limit, the task size, and strips instruction-like lines.
3. **Harness.** `agentic/03-harness/runtime.py` reads `harness` on `agentic/04-loops/specialists/desk-agent/agent.yaml` and calls one adapter. The console settings panel writes that field through `PUT /settings/harness`.
   - `langchain.py` is LangChain `create_agent`. No key uses the mock model.
   - `claude.py` is the Claude Agent SDK, `query()`. It is the provisional live harness. It needs `ANTHROPIC_API_KEY`.
   - `deepagent.py` is Deep Agents, `create_deep_agent`. It is the shadow run. It needs a live model key.
4. **Contract and memory.** `agentic/04-loops` holds the instructions, the session turns, and the model choice. Earlier turns in the session are sent into the adapter.
5. **Action.** `agentic/05-tools/mcp/tool-gateway` calls `search_products`, `get_product_details`, `compare_products`, and `check_stock`. A name that is not on the contract is denied. A successful read can be reused. A repeated call stops.
6. **Learning.** `agentic/06-jobs` enqueues the trace. The question is not stored.
7. **Observability.** `agentic/07-observability` stores the agent, the tool, the status, the duration, and the harness name.
8. **Response.** `agentic/08-response` projects tool results onto `output_schema` and keeps the model reply.

Only one adapter runs. Claude does not call Deep Agents. Deep Agents does not call the Claude SDK. Neither one is a workflow of several agents.

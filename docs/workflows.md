# Workflows

A workflow is a fixed order of agents. LangGraph in `agentic/03-workflows/engine` runs that order. n8n is a different thing: one write tool an agent may call after approval. The sequence is not drawn in n8n, and this repository does not host an n8n process.

`GET /platform` returns the live sequences under `workflows` and the n8n tool under `n8n`. The console Workflows tab reads that list.

## When a workflow is required

A run needs a list of agents before any tool is called. The router in `agentic/03-workflows/router/router.py` builds that list in this order:

1. An `agents` list on the request wins. The workflow name is ignored. The run is called `agent-chain`.
2. A `workflow` name on the request selects that sequence, or one of the single specialists `billing`, `research`, and `data-analysis`.
3. With neither field, the task text is matched against the phrases in the router. The first match wins.
4. With no match, the planner stops the run. The error is `ambiguous_intent`: "The request did not match a workflow."

The planner then checks the list. Every name must be a loaded `agent.yaml`. The list cannot be longer than the hop limit, which is 6. Each handoff must be allowed by `agentic/02-guardrails/policy/delegation.py`. A refused handoff is `delegation_denied`.

The engine then runs the agents one at a time. Each agent loads its own contract and may call only the tools named there. A write that is in `approval.required_for` pauses the sequence. A different actor approves or rejects it. After approval, the engine continues with the remaining agents.

## Sequences in this reference

| Workflow | Agents, in order | Task phrases that select it |
| --- | --- | --- |
| `product-discovery` | shopping, catalog, inventory | jacket, boot, lamp, stock, shop, product |
| `customer-support` | support, billing | refund, return, order status, order 1001, order 1002 |
| `order-processing` | order, billing | place an order, prepare an order, checkout, `buy ` |

The order is the `AGENTS` list in `agentic/03-workflows/sequences/<name>/workflow.py`. The router loads that list. The phrases stay in the router.

`billing`, `research`, and `data-analysis` are single specialists. They have phrases and no workflow file. Research and data analysis are not a step in the three sequences. Billing is a step in support and in order processing, and it can also run alone.

Example: the task "Find a blue trail jacket under $150" matches `product-discovery`. Shopping runs, then catalog, then inventory. Catalog calls `search_products`. No write is waiting, so the sequence finishes.

Example: "Place an order for the jacket at $129" matches `order-processing`. The order agent calls `prepare_order`. The amount is at least `amount_gte` on the order contract, default 100, so the sequence pauses. An operator approves it. Billing then looks up a discount.

## Add a workflow

1. Create `agentic/03-workflows/sequences/<name>/workflow.py` with `AGENTS = ["first-agent", "second-agent"]`.
2. Add that name to `WORKFLOWS` in `agentic/03-workflows/router/router.py` with `_agents("<name>")`.
3. Add a phrase row to `RULES` when the task text should select it. A caller can also send `"workflow": "<name>"` and skip the phrases.
4. Allow each handoff in `agentic/02-guardrails/policy/delegation.py`. Read-only agents may hand work to each other. A hop into a write agent must be an allowlisted pair.
5. Add one case in `tests/agent-evaluation/cases.json` with that workflow name and the tool the test must see.
6. Restart the API. `GET /platform` and the console Workflows tab then show the new order.

## Where n8n fits

n8n is the tool `invoke_n8n`. The permission is `n8n_write`. The gateway marks it as a write, so it stays in `approval.required_for`. No reference agent lists that permission today. The mock model knows the tool name, and it would pass the path `/webhook/product-discovery` only after an agent contract includes the tool.

Set `N8N_BASE_URL` and `N8N_TOKEN` on the API when you already run n8n. The console stores the URL on the Connectors tab and shows that the address is set. It does not show the token. `invoke_n8n` in `agentic/05-tools/mcp/tool-gateway/ports.py` still returns `submitted: false` and `simulated: true`. The function does not send the webhook.

To attach a real webhook later:

1. Add `n8n_write: true` on one agent contract, and add `invoke_n8n` to its tools and to `approval.required_for`. The console can connect the tool only when that permission is already true.
2. Keep the approval pause. The engine calls the tool only after a different actor approves.
3. Replace the body of `invoke_n8n` so that, after approval, it posts to the saved n8n URL with `N8N_TOKEN` from the API environment. Leave `submitted` false until that post succeeds.

The workflow file stays the order of agents. The n8n URL stays the address of an automation you already run.

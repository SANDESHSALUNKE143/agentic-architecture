# Repository

Use this map when you place new code. The standard for what you keep and what you replace is the [implementation guide](implementation-guide.md). This repository is the whole platform. There is no separate SDK package.

## Folder structure

The console is `ui`. The request path is `agentic`, numbered in the order a request moves. `agentic/platform` holds configuration and composition. It is not a request step.

```text
agentic-architecture/
├── ui/
│   ├── admin-dashboard/
│   │   └── src/
│   │       ├── views
│   │       ├── agent
│   │       ├── plugins
│   │       └── config
│   └── packages/
│       └── controls/
│           └── src
├── agentic/
│   ├── platform
│   ├── 01-entry/
│   │   └── routes
│   ├── 02-guardrails/
│   │   ├── auth
│   │   ├── limits
│   │   ├── policy
│   │   └── connections
│   ├── 03-workflows/
│   │   ├── router
│   │   ├── sequences
│   │   ├── engine
│   │   └── state
│   ├── 04-loops/
│   │   ├── runtime
│   │   ├── llm
│   │   ├── memory
│   │   └── specialists
│   ├── 05-tools/
│   │   └── mcp/
│   │       ├── tool-gateway
│   │       ├── catalog-tools
│   │       ├── order-tools
│   │       ├── billing-tools
│   │       └── support-tools
│   ├── 06-jobs/
│   │   ├── queue
│   │   └── workers
│   ├── 07-observability/
│   │   ├── trace
│   │   ├── evaluation
│   │   └── sinks
│   └── 08-response/
│       ├── contracts
│       └── project
├── mocks/
│   └── merchant
├── infrastructure
├── docs
└── tests
```

`ui/admin-dashboard` is the screen you are using. `agentic/01-entry` receives the task. The router in `agentic/03-workflows/router` chooses the agents. The planner in `agentic/02-guardrails/policy` stops a plan that is too long or that hands work to an agent that is not allowed. The engine in `agentic/03-workflows/engine` runs that plan and pauses when a write needs approval. The store in `agentic/03-workflows/state` keeps the run.

Each specialist is a folder such as `agentic/04-loops/specialists/catalog-agent/` with a single `agent.yaml`. `agentic/04-loops/runtime/runtime.py` loads the file and runs the same LangChain loop for every agent.

`agentic/05-tools/mcp/tool-gateway` is the only code that calls a plugin. Catalog, orders, billing, and support are the clients. Stock, documents, and the sales file are registered from `agentic/04-loops/memory`. The mock merchant, an outside store, is `mocks/merchant`.

`agentic/06-jobs` accepts runs onto two workers and writes traces on a separate worker. `tests` checks routes, tools, schema, denied calls, injection text, and approval. `docs` is what this page renders.

## How a run moves

1. The console sends the task, and optionally a workflow or a list of agents.
2. The router picks who runs. A selected agent overrides the automatic route.
3. The planner refuses a hop the delegation rules do not allow.
4. Each agent loads its YAML contract and may call only the plugins connected to it.
5. A write plugin pauses until an operator approves it.
6. The response and the trace come back to the console. The trace does not include the raw question.

## Plugins

A plugin is a tool in the gateway registry. Connecting it adds that tool to an agent's contract. The agent must already have the matching permission. A write plugin keeps its approval requirement. The console cannot add a tool URL or reveal a secret.

SQL, web, n8n, Qdrant, and Neo4j are long-lived ports. Setting the variable marks the port configured. What each port actually calls, and where the API and console are hosted, is in [Operations](operations.md).

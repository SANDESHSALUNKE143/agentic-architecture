# Repository

Use this map when you place new code. The standard for what you keep and what you replace is the [implementation guide](implementation-guide.md). This repository is the whole platform. There is no separate SDK package.

## Folder structure

The repository root is the platform. Each top-level folder has one job. A request starts in `apps`, is planned in `orchestrator`, runs a contract from `agents`, and may call a plugin from `mcp`. Shared behavior lives in `shared`.

```text
agentic-architecture/
├── apps/                  What people open
│   ├── agent-api/         HTTP API on port 8090
│   └── admin-dashboard/   This console on port 5173
├── orchestrator/          Who runs, and in what order
│   ├── router/            Picks a workflow or the agents you selected
│   ├── planner/           Checks hops and whether a handoff is allowed
│   ├── workflow-engine/   Runs the agents and pauses for approval
│   └── state-manager/     Stores the run and the approval decision
├── agents/                One folder and one agent.yaml per specialist
│   └── runtime.py         Loads the YAML and runs the LangChain loop
├── mcp/                   Plugins. The gateway is the only caller
│   ├── tool-gateway/      Allowlist, permission, and approval checks
│   ├── catalog-tools/     Client for the product MCP server
│   ├── order-tools/       Order status and a simulated order
│   ├── billing-tools/     The local discount rule
│   └── support-tools/     A refund request that waits for approval
├── shared/                Used by every agent, so a new agent does not rewrite it
│   ├── llm/               Mock model, or a live model when MODEL_API_KEY is set
│   ├── memory/            Conversation notes and the document index
│   ├── security/          Permissions, delegation, and redaction
│   ├── evaluation/        Status, tool names, and duration
│   ├── contracts/         AgentRequest and AgentResponse
│   └── observability/     The trace
├── workflows/             The three sequences: discovery, support, and orders
├── tests/                 Unit, API, security, and evaluation cases
└── docs/                  The pages in this section
```

### apps

`apps/agent-api` receives the task and returns the response. `apps/admin-dashboard` is the screen you are using: Run, Agents, Plugins, Approvals, Settings, and Docs.

### orchestrator

This folder decides the path before any tool runs. The router chooses the agents. The planner stops a plan that is too long or that hands work to an agent that is not allowed. The workflow engine runs that plan and pauses when a write needs approval. The state manager keeps the run so an operator can approve or reject it later.

### agents

Each specialist is a folder such as `agents/catalog-agent/` with a single `agent.yaml`. That file names the instructions, the plugins, the permissions, and the output shape. `agents/runtime.py` loads the file and runs the same loop for every agent. Adding an agent means copying that YAML, not writing a new runtime.

### mcp

Plugins live here. `mcp/tool-gateway` is the only code that calls one. It refuses a plugin that is not listed on the agent, or that the agent's permission does not allow. The other folders are the plugin packages: catalog, orders, billing, and support. Stock, documents, and the sales file are registered by the gateway from `shared/` so they do not need extra packages.

### shared

Code that every agent needs. The model, memory, security checks, evaluation record, and trace stay here. A new agent does not copy them.

### workflows, tests, and docs

`workflows` names the three fixed sequences: product discovery, customer support, and order processing. `tests` checks routes, tools, schema, denied calls, injection text, and approval. `docs` is what this page renders.

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

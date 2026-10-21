# Enterprise guide

This is the reading path for anyone who builds, operates, or reviews an agent on this platform. The library is `agentic-foundation-sdk`. The reference agent is [insight](../examples/insight_agent/README.md). A platform fix is a version bump. The next agent copies the reference and replaces the instruction and the tools.

![The agent keeps the business. The SDK in the middle runs the loop, enforces the rules, and calls SQL, Qdrant, Neo4j, a model, and the web.](assets/hero-light.svg)

## Who this is for

Three people use the same standard.

- The person who writes an agent owns the instruction, the screen, the tools, and which database to open.
- The person who operates the platform watches runs, limits, and traces. The operator console does not edit the agent and does not own its data.
- The person who reviews guardrails checks permissions, allowlists, quotas, and the rule that prompts, answers, and secrets stay out of traces.

## One agent

Every agent in this standard has the same seven components. The reason loop that calls them is the library harness. Insight is the reference that follows the list.

1. **Foundation model.** The brain. [cognition/brain.py](../examples/insight_agent/cognition/brain.py) decides the next reply. A later agent can put a provider model here. The loop stays in [core/harness](../src/core/harness/README.md).
2. **Perception.** The senses. [perception](../examples/insight_agent/perception/README.md) turns the HTTP body into one question.
3. **Planning.** The strategist. [cognition/planning.py](../examples/insight_agent/cognition/planning.py) orders the evidence steps. It does not write the answer.
4. **Memory.** The notebook. [cognition/memory.py](../examples/insight_agent/cognition/memory.py) holds the instruction and the evidence required before an answer. Tool results of the current question stay with the run.
5. **Action.** The hands. [action](../examples/insight_agent/action/README.md) runs the harness. `tools.py` in that package is the only tools it can call, against [environment](../examples/insight_agent/environment/README.md).
6. **Learning.** The feedback loop. [learning](../examples/insight_agent/learning/README.md) records status, tool names, and duration. It does not store the question or the answer, and it does not change model weights.
7. **Communication.** The voice. [communication](../examples/insight_agent/communication/README.md) shapes the payload. [host](../examples/insight_agent/host/README.md) carries it on the question page and the operator API.

```text
People
  -> communication
  -> perception
  -> foundation model
       planning + memory
  -> action
  -> tools
  -> environment
  -> learning
  -> communication
```

## Agent as a service

Each agent has its own address, its own instruction, and its own permissions. Insight listens on port 8010 for the operator and port 8030 for the question page. Another agent gets another address. The [operator console](../src/services/operator_ui/README.md) reads the running configuration. It does not write the agent's settings.

## What the library owns

The library is the shared control. Import it. Do not copy it.

| Control | Where it lives |
|---|---|
| Decide, tool, answer loop | [core/harness](../src/core/harness/README.md) |
| Permissions and trusted identity | [core/context](../src/core/context/README.md) |
| Request rate, body size, token quotas | [core/policies](../src/core/policies/README.md) |
| Scoped credentials that can be revoked | [core/context](../src/core/context/README.md) |
| Retries, one fallback, structured JSON | [adapters/llm](../src/adapters/llm/README.md) |
| Usage receipt and one content-free trace | [adapters/observability](../src/adapters/observability/README.md) |
| SQL, Qdrant, Neo4j, model, allowlisted web | [adapters](../src/adapters/README.md) |

A trace records status, duration, tool names, and token counts. The question, the answer, and every secret stay in the agent process. The same rule applies to the audit event.

## How an agent uses the library

Every agent imports the library from the same files. The library never imports the agent.

| Agent file | Library call |
|---|---|
| `runtime.py` | `AgentRunner`, `RequestGate`, and `Context`. When `OTEL_EXPORTER_OTLP_ENDPOINT` is set, it also attaches `PlatformObserver`. |
| `cognition/brain.py` | `ModelReply`, the reply the harness accepts. |
| `action/tools.py` | `ToolRegistry` and `ToolSpec`. The registry checks permission and schema. |
| `action` | `ExecutionError`, mapped to the caller's status. |
| `environment` | The adapters this agent opens. Insight opens SQL, Qdrant, Neo4j, the model registry, and the allowlisted web. Sells keeps its book in memory and imports none of those. |
| `communication/observe.py` | Receives the harness events. It does not call a platform service. |

[services/](../src/services/README.md) is the platform HTTP: the operator, the registry, and the gateways. The insight operator image starts `agentic_sdk.services.operator_ui` and calls the agent over HTTP. The agent process does not import that service, the model gateway, or the tool gateway.

Both agents use this layout:

```text
examples/<agent>/
  runtime.py            composition root. Builds AgentRunner.
  perception/           senses
  cognition/            foundation model, planning, memory
  action/               one run, plus the allowlisted tools
  environment/          the stores this agent opens
  learning/             content-free outcome
  communication/        spoken payload and the content-free trace
  host/                 HTTP page, only when the agent has one
  stack/                containers, only when the agent needs them
```

## LangChain, LangGraph, and n8n

These three call the harness. They are not components inside insight or sells.

| Caller | Where |
|---|---|
| LangChain | [langchain.py](../src/adapters/orchestration/langchain.py) turns one question into a tool. The tool calls `AgentRunner`. |
| LangGraph | [langgraph.py](../src/adapters/orchestration/langgraph.py) is a one-node graph. The node calls `AgentRunner`. |
| n8n | [n8n_tool](../src/adapters/tools/integrations.py) posts to a fixed `/webhook/` path. The call is a mutation, so trusted code must approve it. |

Run all three from the repository root after `python -m pip install -e '.[frameworks]'`:

```sh
python examples/frameworks.py
```

## What the agent owns

The agent owns the business. In the reference, that is the city question, the five tools, the scripted decision sequence, the product page, and the evidence required before an answer: `query_metrics` and `search_analyses`. A question whose text is `skip evidence` returns immediately, and the harness rejects it because those tools were not called.

The decision model in the reference is scripted. It reports one input token and one output token so the harness, the quota, and the operator card have a number. A later agent can put a provider model in the foundation-model step. The loop stays the library's.

## A system of agents

Two coordination patterns sit on top of the single-agent shape.

- **Orchestration.** One manager agent calls specialist agents and returns one answer. The manager is an agent. Each specialist is an agent with its own address and tools.
- **Choreography.** Agents react to a shared event. No manager holds the whole flow.

This repository ships one reference agent so the shape is visible. When a second agent repeats a file, that repeated code is the candidate to move into the library. Until then it stays in the agent.

## How to build the next agent

1. Copy [examples/insight_agent](../examples/insight_agent/README.md).
2. Keep the seven components: foundation model, perception, planning, memory, action, learning, and communication.
3. Replace the instruction in `memory.py` and the handlers in `tools.py`.
4. Pin one SDK version. Install it from this checkout during development:

```sh
python -m pip install -e '.[runtime,service,dev]'
```

5. Read [how to use the SDK](how-to-use.md) for the import surface and the [developer guide](developer-guide.md) for hosting.

The library never imports the agent. The agent imports `agentic_sdk`.

## How to run and check it

The reference runs as one local stack from `examples/insight_agent/stack`:

```sh
docker compose --env-file .env.example up --build
```

- Question page: `http://insight.localhost:8030`
- Operator console: `http://operator.localhost:8020`
- Grafana: `http://grafana.localhost:3002`
- Langfuse: `http://langfuse.localhost:3003`
- MLflow: `http://mlflow.localhost:5000`

Ask: `Which city is rising, and what did the last analysis conclude?`

The supported platform profiles live under [deployment](../deployment/README.md). Earlier drafts live under [deployment/earlier](../deployment/earlier/README.md). The same ownership rules are what a larger deployment keeps: the agent owns the business, the library owns the loop, and the operator watches.

## Where to read next

| Order | Chapter |
|---|---|
| 1 | [Folder map](folder-index.md) |
| 2 | [Source layout](source-layout.md) |
| 3 | [Architecture](architecture.md) |
| 4 | [Contracts and trust](security.md) |
| 5 | [How to use the SDK](how-to-use.md) |
| 6 | [Developer guide](developer-guide.md) |
| 7 | [Reference agent](../examples/insight_agent/README.md) |

The repository tree is five folders:

```text
src/          SDK source. Import it as agentic_sdk.
examples/     agents
doc/          guides, diagrams, developer standards, and the adapter sketch
deployment/   stacks, settings, schemas, and run scripts
tests/        unit tests and the retrieval check
```

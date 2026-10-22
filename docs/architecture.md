# Architecture

This is the reference architecture an industry implementation keeps. A request moves through seven components. Each one has a folder. Replacing a retail fixture does not replace the component.

![Request path](assets/architecture.svg)

1. **Perception.** `apps/agent-api` turns the HTTP body into an `AgentRequest` with `request_id`, `user_id`, `task`, `context`, and `permissions`.
2. **Planning.** `orchestrator/planner` chooses the agents, checks the hop limit, and checks delegation before any tool runs.
3. **Foundation model.** `shared/llm` chooses the next step inside the LangChain loop. Mock mode needs no key. Live mode uses `MODEL_API_KEY`.
4. **Memory.** `shared/memory` holds conversation state and optional long-term notes. Tool results stay on the run. Qdrant and Neo4j are optional adapters.
5. **Action.** `mcp/tool-gateway` calls only the tools named in `agent.yaml`. SQL, web, n8n, Qdrant, and Neo4j are local ports. Setting the environment variable marks the port configured. In this reference, only the model port calls out. n8n stays simulated and still waits for approval. The port list is in [Operations](operations.md).
6. **Learning.** `shared/observability` and `shared/evaluation` record the agent, the tool name, the status, and the duration. They do not store the raw question or change model weights. The record stays in the API process.
7. **Communication.** The `AgentResponse` is what the API returns and what the admin dashboard shows: status, result, citations, tool calls, errors, and `requires_approval`.

The runtime in `agents/runtime.py` loads instructions, resolves permitted tools, runs the reasoning loop, validates `output_schema`, and the state manager persists the response.

LangChain `create_agent` is the per-agent loop. LangGraph sequences product discovery, customer support, and order processing, and it stops when a write needs approval.

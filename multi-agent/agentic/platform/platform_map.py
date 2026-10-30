"""What one server runs, and which files a business team edits.

Purpose: one map for the seven steps, security, observability, the live workflows, and the n8n tool.
Used by: GET /platform, the console Workflows tab, and the labels on the API image.
"""

from __future__ import annotations


def _workflows() -> list[dict]:
    from workflows.router.router import load_sequences

    return [
        {
            "id": item["name"],
            "agents": item["agents"],
            "phrases": item["phrases"],
            "path": item["path"],
            "engine": "agentic/03-workflows/engine",
        }
        for item in load_sequences()
    ]


def describe_platform() -> dict:
    return {
        "host": "One server. Two images. Operators open the console. The API stays on the server network.",
        "images": [
            {
                "name": "agentic-api",
                "published": False,
                "role": "Perception, planning, the model, memory, action, learning, communication, security, and observability.",
            },
            {
                "name": "agentic-console",
                "published": True,
                "port": 5173,
                "role": "The operator page. It proxies to the API and holds no secrets.",
            },
        ],
        "steps": [
            {
                "step": 1,
                "id": "perception",
                "title": "Perception",
                "path": "agentic/01-entry",
                "role": "Turns the HTTP body into an AgentRequest.",
            },
            {
                "step": 2,
                "id": "planning",
                "title": "Planning",
                "path": "agentic/03-workflows",
                "role": "Chooses the agents, checks hops, and checks delegation before a tool runs.",
            },
            {
                "step": 3,
                "id": "foundation_model",
                "title": "Foundation model",
                "path": "agentic/04-loops/llm",
                "role": "Chooses the next step. Mock mode needs no key. Live mode uses MODEL_API_KEY.",
            },
            {
                "step": 4,
                "id": "memory",
                "title": "Memory",
                "path": "agentic/04-loops/memory",
                "role": "Holds the session, optional notes, and retrieval. A note is stored only when rag.capture is true.",
            },
            {
                "step": 5,
                "id": "action",
                "title": "Action",
                "path": "agentic/05-tools/mcp/tool-gateway",
                "role": "Calls a plugin only when the contract lists it and the permission is true.",
            },
            {
                "step": 6,
                "id": "learning",
                "title": "Learning",
                "path": "agentic/07-observability/evaluation",
                "role": "Records status, tool names, and duration. It does not store the raw question or change model weights.",
            },
            {
                "step": 7,
                "id": "communication",
                "title": "Communication",
                "path": "agentic/08-response/contracts",
                "role": "The AgentResponse is what the API returns and what the console shows.",
            },
        ],
        "security": [
            {
                "id": "authentication",
                "path": "agentic/02-guardrails/auth/auth.py",
                "role": "Every route except guide assets requires the bearer token. A wrong token is 401. Production refuses the sample token.",
            },
            {
                "id": "rate_limit",
                "path": "agentic/02-guardrails/limits/rate_limit.py",
                "role": "Each client is limited per minute. Extra calls receive 429. An oversized body receives 413.",
            },
            {
                "id": "delegation",
                "path": "agentic/02-guardrails/policy/delegation.py",
                "role": "A read agent may hand work to another read agent. A write hop runs only when the source contract lists that target.",
            },
            {
                "id": "redaction",
                "path": "agentic/02-guardrails/policy/redact.py",
                "role": "Instruction-like lines in a task or a document are removed before the model sees them.",
            },
            {
                "id": "approval",
                "path": "agentic/05-tools/mcp/tool-gateway/gateway.py",
                "role": "A write named in approval.required_for waits for a different actor.",
            },
            {
                "id": "limits",
                "path": "agentic/02-guardrails/limits/task.py",
                "role": "Task size and the other request limits.",
            },
        ],
        "observability": [
            {
                "id": "platform_trace",
                "path": "agentic/07-observability/trace/trace.py",
                "role": "The request enqueues the stage. A background worker stores the agent, the tool name, the status, and the duration. The raw question is omitted.",
            },
            {
                "id": "evaluation",
                "path": "agentic/07-observability/evaluation",
                "role": "Records the score for the run. Model weights stay unchanged.",
            },
            {
                "id": "sinks",
                "path": "agentic/07-observability/sinks/sinks.py",
                "role": "OpenTelemetry, the log store, and Grafana are marked configured when their address is set. The record stays in this process.",
            },
            {
                "id": "selection",
                "path": "agentic/04-loops/specialists/<name>/agent.yaml",
                "role": "The observability list on the contract. Settings writes that list for one agent.",
            },
        ],
        "business": [
            {
                "change": "Scaffold an agent from the problem it should solve",
                "path": "new-agent.sh",
            },
            {
                "change": "Specialist instructions, tools, permissions, output schema, route phrases, and handoffs",
                "path": "agentic/04-loops/specialists/<name>/agent.yaml",
            },
            {
                "change": "A plugin, its permission, and the function that answers it",
                "path": "agentic/05-tools/mcp/<domain>-tools/tools.py",
            },
            {
                "change": "SQL, web, or n8n stand-in behind the same tool name",
                "path": "agentic/05-tools/mcp/tool-gateway/ports.py",
            },
            {
                "change": "Agent order and the words that select a workflow",
                "path": "agentic/03-workflows/sequences/<name>/workflow.yaml",
            },
            {
                "change": "A case the evaluation run must pass",
                "path": "tests/agent-evaluation/cases.json",
            },
        ],
        "workflows": _workflows(),
        "n8n": {
            "role": "An optional write tool on one agent. The workflow engine does not run inside n8n.",
            "tool": "invoke_n8n",
            "permission": "n8n_write",
            "path": "agentic/05-tools/mcp/tool-gateway/ports.py",
            "calls_host": False,
            "approval": True,
        },
        "unchanged": [
            {"path": "agentic/04-loops/runtime/runtime.py", "role": "The only reasoning loop. A new agent does not copy it."},
            {"path": "agentic/03-workflows/engine", "role": "Runs the plan and pauses for approval."},
            {"path": "agentic/03-workflows/state", "role": "Keeps the run so another actor can approve it."},
            {"path": "agentic/08-response/contracts", "role": "AgentRequest and AgentResponse."},
        ],
    }

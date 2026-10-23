"""What one server runs, and which files a business team edits.

The API image holds every step because approvals, traces, and notes live in
that process. The console image is the page operators open.
"""

from __future__ import annotations


def _workflows() -> list[dict]:
    from orchestrator.router.router import RULES, WORKFLOWS

    phrases = {name: list(words) for name, words in RULES}
    return [
        {
            "id": name,
            "agents": agents,
            "phrases": phrases.get(name, []),
            "path": f"workflows/{name}/workflow.py",
            "engine": "orchestrator/workflow-engine",
        }
        for name, agents in WORKFLOWS.items()
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
                "path": "apps/agent-api",
                "role": "Turns the HTTP body into an AgentRequest.",
            },
            {
                "step": 2,
                "id": "planning",
                "title": "Planning",
                "path": "orchestrator",
                "role": "Chooses the agents, checks hops, and checks delegation before a tool runs.",
            },
            {
                "step": 3,
                "id": "foundation_model",
                "title": "Foundation model",
                "path": "shared/llm",
                "role": "Chooses the next step. Mock mode needs no key. Live mode uses MODEL_API_KEY.",
            },
            {
                "step": 4,
                "id": "memory",
                "title": "Memory",
                "path": "shared/memory",
                "role": "Holds the session, optional notes, and retrieval. A note is stored only when rag.capture is true.",
            },
            {
                "step": 5,
                "id": "action",
                "title": "Action",
                "path": "mcp/tool-gateway",
                "role": "Calls a plugin only when the contract lists it and the permission is true.",
            },
            {
                "step": 6,
                "id": "learning",
                "title": "Learning",
                "path": "shared/evaluation",
                "role": "Records status, tool names, and duration. It does not store the raw question or change model weights.",
            },
            {
                "step": 7,
                "id": "communication",
                "title": "Communication",
                "path": "shared/contracts",
                "role": "The AgentResponse is what the API returns and what the console shows.",
            },
        ],
        "security": [
            {
                "id": "authentication",
                "path": "apps/agent-api/app.py",
                "role": "Every route except guide assets requires the bearer token. Production refuses the sample token.",
            },
            {
                "id": "delegation",
                "path": "shared/security/delegation.py",
                "role": "Who may hand work to whom. This is the delegation file a team edits.",
            },
            {
                "id": "redaction",
                "path": "shared/security/redact.py",
                "role": "Instruction-like lines in a task or a document are removed before the model sees them.",
            },
            {
                "id": "approval",
                "path": "mcp/tool-gateway/gateway.py",
                "role": "A write named in approval.required_for waits for a different actor.",
            },
            {
                "id": "limits",
                "path": "shared/security/limits.py",
                "role": "Task size and the other request limits.",
            },
        ],
        "observability": [
            {
                "id": "platform_trace",
                "path": "shared/observability/trace.py",
                "role": "Records the agent, the tool name, the status, and the duration. The raw question is omitted.",
            },
            {
                "id": "evaluation",
                "path": "shared/evaluation",
                "role": "Records the score for the run. Model weights stay unchanged.",
            },
            {
                "id": "sinks",
                "path": "shared/observability/sinks.py",
                "role": "OpenTelemetry, the log store, and Grafana are marked configured when their address is set. The record stays in this process.",
            },
            {
                "id": "selection",
                "path": "agents/<name>/agent.yaml",
                "role": "The observability list on the contract. Settings writes that list for one agent.",
            },
        ],
        "business": [
            {
                "change": "Specialist instructions, tools, permissions, and output schema",
                "path": "agents/<name>/agent.yaml",
            },
            {
                "change": "Catalog, order, billing, or support behavior",
                "path": "mcp/<domain>-tools/tools.py",
            },
            {
                "change": "Register a plugin before a contract names it",
                "path": "mcp/tool-gateway/gateway.py",
            },
            {
                "change": "SQL, web, or n8n stand-in behind the same tool name",
                "path": "mcp/tool-gateway/ports.py",
            },
            {
                "change": "Who may hand work to whom",
                "path": "shared/security/delegation.py",
            },
            {
                "change": "Words that select a workflow or a specialist",
                "path": "orchestrator/router/router.py",
            },
            {
                "change": "Agent order inside a workflow",
                "path": "workflows/<name>/workflow.py",
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
            "path": "mcp/tool-gateway/ports.py",
            "calls_host": False,
            "approval": True,
        },
        "unchanged": [
            {"path": "agents/runtime.py", "role": "The only reasoning loop. A new agent does not copy it."},
            {"path": "orchestrator/workflow-engine", "role": "Runs the plan and pauses for approval."},
            {"path": "orchestrator/state-manager", "role": "Keeps the run so another actor can approve it."},
            {"path": "shared/contracts", "role": "AgentRequest and AgentResponse."},
        ],
    }

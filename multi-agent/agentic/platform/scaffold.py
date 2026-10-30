"""Create one agent from a problem statement.

Purpose: write the contract, the tool package, the workflow, and one evaluation case.
Used by: new-agent.sh. A team replaces the tool body with the system that solves the problem.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

from agentic.platform.config import ROOT

_NAME = re.compile(r"^[a-z][a-z0-9-]{1,40}$")


def create(name: str, problem: str, root: Path | None = None) -> dict:
    base = _base(name)
    problem = " ".join(problem.split())
    if len(problem) < 8:
        raise ValueError("Describe the problem in a sentence.")
    root = Path(root or ROOT)
    agent_id = f"{base}-agent"
    phrase = base.replace("-", " ")
    tool = "lookup_" + base.replace("-", "_")
    permission = base.replace("-", "_") + "_read"
    _available(root, agent_id, base, phrase)
    agent_path = root / "agentic" / "04-loops" / "specialists" / agent_id / "agent.yaml"
    tool_path = root / "agentic" / "05-tools" / "mcp" / f"{base}-tools" / "tools.py"
    workflow_path = root / "agentic" / "03-workflows" / "sequences" / base / "workflow.yaml"
    case_path = root / "tests" / "agent-evaluation" / "cases.json"
    agent_path.parent.mkdir(parents=True, exist_ok=True)
    tool_path.parent.mkdir(parents=True, exist_ok=True)
    workflow_path.parent.mkdir(parents=True, exist_ok=True)
    agent_path.write_text(_contract(agent_id, problem, tool, permission, phrase), encoding="utf-8")
    tool_path.write_text(_plugin(base, tool, permission, problem), encoding="utf-8")
    workflow_path.write_text(_workflow(base, agent_id, phrase), encoding="utf-8")
    _case(case_path, base, agent_id, tool, phrase)
    return {
        "agent": str(agent_path.relative_to(root)),
        "tool": str(tool_path.relative_to(root)),
        "workflow": str(workflow_path.relative_to(root)),
        "phrase": phrase,
        "tool_name": tool,
    }


def _base(name: str) -> str:
    slug = name.strip().lower().removesuffix("-agent")
    if not _NAME.match(slug):
        raise ValueError("Use a short lowercase name, such as claims or invoice-review.")
    return slug


def _available(root: Path, agent_id: str, base: str, phrase: str) -> None:
    agent = root / "agentic" / "04-loops" / "specialists" / agent_id
    workflow = root / "agentic" / "03-workflows" / "sequences" / base
    if agent.exists() or workflow.exists():
        raise ValueError(f"{agent_id} already exists.")
    for path in (root / "agentic" / "03-workflows" / "sequences").glob("*/workflow.yaml"):
        if phrase in path.read_text(encoding="utf-8"):
            raise ValueError(f"The phrase {phrase!r} is already used. Choose another name.")


def _contract(agent_id: str, problem: str, tool: str, permission: str, phrase: str) -> str:
    summary = json.dumps(problem)
    instruction = json.dumps(f"Solve this problem: {problem}")
    return f"""name: {agent_id}
description: {summary}
instructions:
  - {instruction}
  - Call {tool} and return only what that tool reports.
  - Do not invent a result the tool did not return.
tools:
  - {tool}
memory:
  conversation_state: true
  long_term_memory: optional
permissions:
  {permission}: true
output_schema:
  type: object
  properties:
    answer:
      type: string
    explanation:
      type: string
    sources:
      type: array
  required:
    - answer
    - explanation
    - sources
approval:
  required_for: []
rag:
  retrieve: false
  capture: false
  vector: local
  embedding: local
model:
  provider: platform
observability:
  - platform_trace
  - evaluation
evaluation:
  expect_tools:
    - {tool}
route:
  id: {agent_id.removesuffix("-agent")}
  priority: 5
  phrases:
    - {phrase}
examples:
  - {phrase}
"""


def _plugin(base: str, tool: str, permission: str, problem: str) -> str:
    summary = json.dumps(problem)
    return f'''"""Tool for {base}.

Purpose: answer {summary}.
Replace the body of {tool} with the system that solves that problem.
The gateway loads TOOLS from this file. Do not register the name anywhere else.
"""

from __future__ import annotations


def {tool}(query: str) -> dict:
    text = query.strip()
    if not text:
        return {{"answer": "", "explanation": "The request was empty.", "sources": [], "error": "empty"}}
    return {{
        "answer": text[:500],
        "explanation": "Replace this function with the system that solves the problem.",
        "sources": [{{"source_id": "local:{base}", "location": "agentic/05-tools/mcp/{base}-tools/tools.py"}}],
    }}


TOOLS = {{
    "{tool}": {{
        "group": "{base}",
        "summary": {summary},
        "permission": "{permission}",
        "write": False,
        "fn": {tool},
        "schema": {{"query": "string"}},
    }},
}}
'''


def _workflow(base: str, agent_id: str, phrase: str) -> str:
    return f"""name: {base}
order: 50
priority: 5
agents:
  - {agent_id}
phrases:
  - {phrase}
"""


def _case(path: Path, base: str, agent_id: str, tool: str, phrase: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    rows = json.loads(path.read_text(encoding="utf-8")) if path.exists() else []
    rows.append({
        "name": f"{base} answers the brief",
        "task": phrase,
        "workflow": base,
        "agent_id": agent_id,
        "expect_tools": [tool],
    })
    path.write_text(json.dumps(rows, indent=2) + "\n", encoding="utf-8")

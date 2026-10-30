"""HTTP API assembly.

Purpose: create one FastAPI app and mount each route group. The groups own the bodies and the checks.
Used by: agentic/01-entry/main.py and the API tests. Interactive docs are /docs. The written list is docs/api.md.
"""

from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI

from agentic.platform.composition import Platform
from agentic.platform.config import assert_runtime_config
from agentic.platform.loader import load_module

assert_runtime_config()
platform = Platform()
app = FastAPI(
    title="Agentic architecture",
    version="1.0.0",
    description=(
        "One API process for every agent. Send Authorization: Bearer on every route "
        "except guide images. POST /agent-runs starts work. A workflow name or an "
        "agent list chooses who runs. A write pauses until a different actor approves it. "
        "The written reference is docs/api.md."
    ),
    openapi_tags=[
        {"name": "Health", "description": "Process status."},
        {"name": "Platform", "description": "Steps, security, observability, workflows, and edit paths."},
        {"name": "Runs", "description": "Start, stream, read, cancel, and score a run."},
        {"name": "Approvals", "description": "Paused writes. A different actor decides."},
        {"name": "Agents", "description": "Loaded contracts and the tool registry."},
        {"name": "Plugins", "description": "Connect a tool, a RAG choice, or an observability sink."},
        {"name": "Settings", "description": "Contracts and connector addresses."},
        {"name": "Memory", "description": "Redacted notes."},
        {"name": "Guide", "description": "Markdown pages from docs/."},
    ],
)

_HERE = Path(__file__).resolve().parent
_AGENTIC = _HERE.parent
load_module(_AGENTIC / "02-guardrails" / "limits" / "guard.py", "agent_api_guard").install(app)
for _name in ("catalog", "runs", "approvals", "settings", "mcp", "guide"):
    load_module(_HERE / "routes" / f"{_name}.py", f"agent_api_routes_{_name}").mount(app, platform)

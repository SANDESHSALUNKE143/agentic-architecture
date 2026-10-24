"""Composition root.

Purpose: wire the gateway, memory, trace, run flow, and contract catalog. Adding an agent does not copy this file.
Used by: agentic/01-entry/app.py. Run behavior is agentic/03-workflows/runs.py. Contract saves are agentic/platform/catalog.py.
"""

from __future__ import annotations

import os

from guardrails.connections.credentials import CredentialStore
from jobs.queue.checks import JobRunner
from jobs.queue.runs import RunQueue
from loops.memory.rag import describe as describe_rag
from loops.memory.service import MemoryService
from loops.runtime.runtime import Runtime
from observability.evaluation.log import EvaluationLog
from observability.sinks.sinks import describe
from observability.trace.trace import TraceLog
from response.contracts import load_contract
from workflows.runs import RunFlow

from agentic.platform.catalog import Catalog
from agentic.platform.config import MAX_HOPS, ROOT, TIMEOUT_SECONDS, data_dir, llm_mode
from agentic.platform.loader import load_module

_gateway_mod = load_module(ROOT / "agentic" / "05-tools" / "mcp" / "tool-gateway" / "gateway.py", "tool_gateway")
_store_mod = load_module(ROOT / "agentic" / "03-workflows" / "state" / "store.py", "run_store")
AGENT_DIR = ROOT / "agentic" / "04-loops" / "specialists"


class Platform(RunFlow, Catalog):
    def __init__(self) -> None:
        self.gateway = _gateway_mod.ToolGateway()
        self.memory = MemoryService()
        self.traces = TraceLog()
        self.evaluation = EvaluationLog()
        self.credentials = CredentialStore()
        self.jobs = JobRunner()
        self.run_queue = RunQueue()
        self.store = _store_mod.RunStore()
        self.runtime = Runtime(self.gateway, self.memory, self.traces, self.evaluation)
        self.reload()

    def reload(self) -> None:
        self.contracts = {
            path.parent.name: load_contract(path)
            for path in sorted(AGENT_DIR.glob("*/agent.yaml"))
        }

    def health(self) -> dict:
        return {"status": "ok", "mode": llm_mode(), "agents": len(self.contracts)}

    def platform_settings(self) -> dict:
        return {
            "mode": llm_mode(),
            "timeout_seconds": TIMEOUT_SECONDS,
            "max_hops": MAX_HOPS,
            "model_api_key_set": bool(os.environ.get("MODEL_API_KEY")),
            "data_dir": str(data_dir()),
            "observability": describe(os.environ),
            "rag": describe_rag(os.environ),
        }

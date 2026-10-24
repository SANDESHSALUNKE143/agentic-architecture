"""Composition root.

Purpose: wire the gateway, memory, trace, run flow, and contract catalog. Adding an agent does not copy this file.
Used by: apps/agent-api/app.py. Run behavior is orchestrator/runs.py. Contract saves are orchestrator/catalog.py.
"""

from __future__ import annotations

import os

from agents.runtime import Runtime
from shared.config import MAX_HOPS, ROOT, TIMEOUT_SECONDS, data_dir, llm_mode
from shared.contracts import load_contract
from shared.evaluation import EvaluationLog
from shared.jobs import JobRunner
from shared.loader import load_module
from shared.memory.rag import describe as describe_rag
from shared.memory.service import MemoryService
from shared.observability.sinks import describe
from shared.observability.trace import TraceLog
from shared.security.credentials import CredentialStore

from orchestrator.catalog import Catalog
from orchestrator.runs import RunFlow

_gateway_mod = load_module(ROOT / "mcp" / "tool-gateway" / "gateway.py", "tool_gateway")
_store_mod = load_module(ROOT / "orchestrator" / "state-manager" / "store.py", "run_store")
AGENT_DIR = ROOT / "agents"


class Platform(RunFlow, Catalog):
    def __init__(self) -> None:
        self.gateway = _gateway_mod.ToolGateway()
        self.memory = MemoryService()
        self.traces = TraceLog()
        self.evaluation = EvaluationLog()
        self.credentials = CredentialStore()
        self.jobs = JobRunner()
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

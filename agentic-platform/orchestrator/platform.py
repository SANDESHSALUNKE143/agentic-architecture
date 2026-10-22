"""Wires the router, planner, engine, tools, memory, and learning into one object."""

from __future__ import annotations

from pathlib import Path

from agents.registry import load_agents
from shared.config import data_dir
from shared.learning import Learning
from shared.loader import load_module
from shared.memory import Memory
from shared.security.delegation import can_delegate

from orchestrator.planner import planner as planner_module
from orchestrator.router import router as router_module

_ROOT = Path(__file__).resolve().parents[1]


def _load_hyphen(folder: str, filename: str, module_name: str):
    return load_module(_ROOT / folder / filename, module_name)


class Platform:
    """One process. Pass a data_dir in tests so notes do not leak between cases."""

    def __init__(self, data_path: Path | None = None) -> None:
        path = Path(data_path) if data_path else data_dir()
        path.mkdir(parents=True, exist_ok=True)
        gateway_module = _load_hyphen("mcp/tool-gateway", "gateway.py", "platform_tool_gateway")
        state = _load_hyphen("orchestrator/state-manager", "store.py", "platform_run_store")
        engine_module = _load_hyphen(
            "orchestrator/workflow-engine", "engine.py", "platform_workflow_engine"
        )
        self.store = state.RunStore()
        self.memory = Memory(path)
        self.learning = Learning(path)
        self.gateway = gateway_module.Gateway()
        self.agents = load_agents()
        self.router = router_module
        self.planner = planner_module
        self.engine = engine_module

    def security_can_delegate(self, source: str, target: str):
        return can_delegate(source, target)

    async def run(self, request):
        return await self.engine.start_run(self, request)

    async def resume(self, approval_id: str, decision: str, actor: str):
        return await self.engine.resume(self, approval_id, decision, actor)

    def feedback(self, run_id: str, rating: str, note: str) -> dict:
        if self.store.get(run_id) is None:
            raise KeyError(run_id)
        return self.learning.add_feedback(run_id, rating, note)

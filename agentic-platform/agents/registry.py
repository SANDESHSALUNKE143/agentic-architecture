"""Load every agents/*-agent package."""

from __future__ import annotations

from pathlib import Path

from shared.loader import load_module

_ROOT = Path(__file__).resolve().parent


def load_agents() -> dict:
    """Return agent id -> Agent. Folder names stay hyphenated."""
    found = {}
    for folder in sorted(
        path for path in _ROOT.iterdir() if path.is_dir() and path.name.endswith("-agent")
    ):
        module = load_module(folder / "agent.py", "platform_agent_" + folder.name.replace("-", "_"))
        agent = module.AGENT
        if agent.handler is None:
            raise RuntimeError(f"{agent.id} has no handler")
        found[agent.id] = agent
    return found

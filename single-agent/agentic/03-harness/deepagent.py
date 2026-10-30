"""Deep Agents harness.

Purpose: create_deep_agent in this process. Built-in filesystem, shell, and subagent tools stay off.
Used by: agentic/03-harness/runtime.py when the contract says deepagent.
"""

from __future__ import annotations

from harness.base import HarnessResult
from harness.langchain import _reply
from loops.llm import live_enabled, live_model

_EXCLUDED = [
    "ls",
    "read_file",
    "write_file",
    "edit_file",
    "glob",
    "grep",
    "execute",
    "task",
]


def run(tools, instructions: list[str], messages: list[dict]) -> HarnessResult:
    if not live_enabled():
        return HarnessResult(error="harness_unavailable")
    try:
        from deepagents import create_deep_agent
    except ImportError:
        return HarnessResult(error="harness_unavailable")
    prompt = "\n".join(instructions)
    model = live_model()
    agent = _build(create_deep_agent, model, tools, prompt)
    if agent is None:
        return HarnessResult(error="harness_unavailable")
    outcome = agent.invoke({"messages": messages})
    return HarnessResult(reply=_reply(outcome))


def _build(create_deep_agent, model, tools, prompt):
    kwargs = {"model": model, "tools": tools, "system_prompt": prompt}
    try:
        from deepagents import HarnessProfile

        kwargs["profile"] = HarnessProfile(excluded_tools=list(_EXCLUDED))
    except (ImportError, TypeError):
        pass
    try:
        return create_deep_agent(**kwargs)
    except TypeError:
        kwargs.pop("profile", None)
        try:
            return create_deep_agent(**kwargs)
        except Exception:
            return None
    except Exception:
        return None

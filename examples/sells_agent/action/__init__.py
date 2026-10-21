"""
Action for the sells agent.

Runs one question through the harness, records the outcome, and speaks the result.

Usage:
    status, payload = execute(runner, context, observer, question)
"""

import asyncio

from agentic_sdk.contracts.orchestration.types import ExecutionError

from sells_agent.communication import failure, success
from sells_agent.learning import note

# ── One question ──────────────────────────────────────────────────────


def execute(runner, context, observer, question):
    """Run one question and return an HTTP status plus a spoken body."""
    try:
        result = asyncio.run(runner.run(context, question))
    except (ExecutionError, ValueError, PermissionError) as exc:
        note("rejected", [], "error", 0)
        return 422, failure(str(exc))
    except Exception:
        note("rejected", [], "error", 0)
        return 500, failure("the agent could not finish the run")
    duration = 0
    if observer.events:
        duration = observer.events[-1].get("duration_ms", 0)
    note(result.run_id, list(result.tools_used), "ok", duration)
    return 200, success(result)

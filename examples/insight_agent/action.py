"""
Action for the insight agent.

The hands in motion. Runs one perceived question through the harness, asks
learning to record the outcome, and asks communication to speak the result.
The product page and the operator API both call execute.

Usage:
    status, payload = execute(runner, context, observer, question)
"""

import asyncio

from agentic_sdk.contracts.orchestration.types import ExecutionError

from insight_agent.communication import failure, success
from insight_agent.learning import note

# ── One question ──────────────────────────────────────────────────────


def execute(runner, context, observer, question):
    """Run one question and return an HTTP status plus a spoken body."""
    try:
        result = asyncio.run(runner.run(context, question))
    except (ExecutionError, ValueError, PermissionError) as exc:
        note("rejected", [], "error", 0)
        limited = str(exc) in {
            "request rate exceeded",
            "daily token quota exceeded",
            "monthly token quota exceeded",
        }
        return (429 if limited else 422), failure(str(exc))
    except Exception:
        note("rejected", [], "error", 0)
        return 500, failure("the agent could not finish the run")
    duration = 0
    if observer.events:
        duration = observer.events[-1].get("duration_ms", 0)
    note(result.run_id, list(result.tools_used), "ok", duration)
    return 200, success(result)

"""
Communication for the sells agent.

The voice. Shapes the payload a caller receives.

Usage:
    body = success(result)
"""

# ── Voice ─────────────────────────────────────────────────────────────


def success(result) -> dict:
    """Return the answer, the tools that produced it, and the run id."""
    return {
        "answer": result.answer,
        "tools_used": list(result.tools_used),
        "run_id": result.run_id,
    }


def failure(detail: str) -> dict:
    """Return a refusal a caller can show without the question text."""
    return {"detail": detail}

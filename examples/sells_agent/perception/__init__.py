"""
Perception for the sells agent.

The senses. Turns one HTTP body into the question the foundation model will see.

Usage:
    question = perceive(raw_body)
"""

import json

# ── Question ──────────────────────────────────────────────────────────


def perceive(raw: bytes) -> str:
    """Return the question text. Reject a body that is not a text question."""
    try:
        body = json.loads(raw.decode())
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError("question must be text") from exc
    question = body.get("question") if isinstance(body, dict) else None
    if not isinstance(question, str) or not question.strip():
        raise ValueError("question must be text")
    return question.strip()

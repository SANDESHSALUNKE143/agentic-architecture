"""
Run one sells question in this process.

Usage:
    python -m sells_agent
"""

from sells_agent.action import execute
from sells_agent.runtime import build

# ── One question ──────────────────────────────────────────────────────

QUESTION = "What is the status of order 1001, and can I add express shipping?"


def main() -> None:
    """Build the agent and print the spoken answer."""
    runner, context, trace = build()
    _status, payload = execute(runner, context, trace, QUESTION)
    print(payload["answer"])


if __name__ == "__main__":
    main()

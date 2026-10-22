"""Support can read an order and request a refund. The refund is not executed."""

from __future__ import annotations


def request_approval(action: str, summary: str, approved: bool = False) -> dict:
    return {
        "action": action,
        "summary": summary[:240],
        "approved": approved,
        "submitted": False,
        "simulated": True,
        "explanation": "The request is recorded for approval and no refund was sent.",
    }

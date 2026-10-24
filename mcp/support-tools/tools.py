"""Refund request.

Purpose: record a refund request. The refund is not sent. The gateway still waits for approval.
Used by: mcp/tool-gateway/registry.py under request_approval. The support contract names that tool.
"""

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

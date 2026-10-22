"""Support lookups. request_approval never approves the action."""

from __future__ import annotations


async def request_approval(ctx, arguments):
    return {
        "approval_requested": True,
        "auto_approved": False,
        "action": arguments["action"],
        "summary": arguments["summary"],
        "simulated": True,
    }

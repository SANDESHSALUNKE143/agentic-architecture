"""Enterprise drafts. Writes stay simulated even after approval."""

from __future__ import annotations

SNIPPET = "def add(a, b):\n    return a - b\n"


async def prepare_provisioning(ctx, arguments):
    return {
        "account": {"user": arguments["user_name"], "status": "draft"},
        "email": "not-sent",
        "meeting": "not-scheduled",
        "simulated": True,
    }


async def draft_campaign(ctx, arguments):
    segment = arguments.get("segment", "trail-club")
    return {
        "segment": segment,
        "copy": f"Draft for {segment}: the blue trail jacket is back in stock.",
        "sent": False,
        "spend": 0,
        "simulated": True,
    }


async def propose_patch(ctx, arguments):
    return {
        "path": "fixtures/add.py",
        "original": SNIPPET,
        "diff": "--- a/fixtures/add.py\n+++ b/fixtures/add.py\n@@\n-    return a - b\n+    return a + b\n",
        "written": False,
        "simulated": True,
    }


async def apply_patch(ctx, arguments):
    return {"path": "fixtures/add.py", "written": False, "simulated": True, "dry_run": True}

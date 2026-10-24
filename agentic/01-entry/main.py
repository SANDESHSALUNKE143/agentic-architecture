"""Process entry for the API.

Purpose: bind the HTTP app. The laptop uses 127.0.0.1. The server image sets PLATFORM_BIND_HOST=0.0.0.0.
Used by: ./start-local.sh and deploy/Dockerfile.api.
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

import uvicorn  # noqa: E402

from agentic.platform.config import setting  # noqa: E402
from agentic.platform.loader import load_module  # noqa: E402

app_module = load_module(ROOT / "agentic" / "01-entry" / "app.py", "agent_api_app")

if __name__ == "__main__":
    host = setting("PLATFORM_BIND_HOST", "127.0.0.1")
    port = int(setting("PLATFORM_BIND_PORT", "8090") or "8090")
    uvicorn.run(app_module.app, host=host, port=port)

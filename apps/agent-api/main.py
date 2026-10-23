"""Start the API. The laptop binds to 127.0.0.1. The server image binds to 0.0.0.0."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

import uvicorn  # noqa: E402
from shared.config import setting  # noqa: E402
from shared.loader import load_module  # noqa: E402

app_module = load_module(ROOT / "apps" / "agent-api" / "app.py", "agent_api_app")

if __name__ == "__main__":
    host = setting("PLATFORM_BIND_HOST", "127.0.0.1")
    port = int(setting("PLATFORM_BIND_PORT", "8090") or "8090")
    uvicorn.run(app_module.app, host=host, port=port)

"""Process entry for the single-agent API.

Purpose: bind the HTTP app on 127.0.0.1:8092 unless the environment sets the port.
Used by: start-local.sh.
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

import uvicorn  # noqa: E402

from agentic.platform.config import setting  # noqa: E402
from agentic.platform.loader import load_module  # noqa: E402

app_module = load_module(ROOT / "agentic" / "01-entry" / "app.py", "single_agent_app")

if __name__ == "__main__":
    host = setting("PLATFORM_BIND_HOST", "127.0.0.1")
    port = int(setting("PLATFORM_BIND_PORT", "8092") or "8092")
    uvicorn.run(app_module.app, host=host, port=port)

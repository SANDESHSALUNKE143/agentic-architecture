"""Start the local API on 127.0.0.1:8090."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

import uvicorn  # noqa: E402
from shared.loader import load_module  # noqa: E402

app_module = load_module(ROOT / "apps" / "agent-api" / "app.py", "agent_api_app")

if __name__ == "__main__":
    uvicorn.run(app_module.app, host="127.0.0.1", port=8090)

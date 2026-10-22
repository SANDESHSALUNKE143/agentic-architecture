"""Start the API on port 8090.

python agentic-platform/apps/agent-api/main.py
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT.parent / "src"))

import uvicorn  # noqa: E402
from shared.loader import load_module  # noqa: E402


def main() -> None:
    module = load_module(ROOT / "apps" / "agent-api" / "app.py", "platform_agent_api")
    uvicorn.run(module.create_app(), host="127.0.0.1", port=8090)


if __name__ == "__main__":
    main()

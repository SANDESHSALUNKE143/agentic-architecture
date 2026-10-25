"""Start the mock merchant once for tests.

Purpose: catalog, order, billing, and support calls need a server. The test process sets MERCHANT_MCP_URL.
Used by: the unit, API, security, and evaluation tests.
"""

from __future__ import annotations

import os
import sys
import threading
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from agentic.platform.loader import load_module  # noqa: E402

_started = False


def ensure_merchant_server() -> None:
    global _started
    if os.environ.get("MERCHANT_MCP_URL", "").strip() or _started:
        return
    server = load_module(ROOT / "mocks" / "merchant" / "server.py", "merchant_mcp_server")
    httpd = server.make_server("127.0.0.1", 0)
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    host, port = httpd.server_address
    os.environ["MERCHANT_MCP_URL"] = f"http://{host}:{port}/mcp"
    _started = True

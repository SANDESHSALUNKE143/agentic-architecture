"""Tool registry.

Purpose: collect plugins from mcp/<domain>-tools/tools.py.
Used by: agentic/05-tools/mcp/tool-gateway/gateway.py. A new plugin is a TOOLS entry beside its function.
"""

from __future__ import annotations

from typing import Any

from agentic.platform.config import ROOT
from agentic.platform.loader import load_module

Tool = dict[str, Any]


def _collect() -> dict[str, Tool]:
    found: dict[str, Tool] = {}
    mcp = ROOT / "agentic" / "05-tools" / "mcp"
    for path in sorted(mcp.glob("*/tools.py")):
        module = load_module(path, "tools_" + path.parent.name.replace("-", "_"))
        found.update(getattr(module, "TOOLS", {}))
    return found


REGISTRY: dict[str, Tool] = _collect()

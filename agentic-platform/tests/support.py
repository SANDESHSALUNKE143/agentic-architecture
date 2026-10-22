"""Put the platform and the SDK on the path for unittest."""

from __future__ import annotations

import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT.parent
for path in (str(ROOT), str(REPO / "src")):
    if path not in sys.path:
        sys.path.insert(0, path)


def make_platform():
    from orchestrator.platform import Platform

    directory = tempfile.mkdtemp(prefix="agentic-platform-")
    return Platform(Path(directory))

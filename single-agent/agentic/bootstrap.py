"""Register the numbered stage folders as importable packages.

Purpose: a folder that starts with digits cannot be a Python package. This binds each stage to a normal name.
Used by: agentic/__init__.py before the API or the tests import a stage.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
_BOUND = False
_PACKAGES = {
    "entry": "01-entry",
    "guardrails": "02-guardrails",
    "harness": "03-harness",
    "loops": "04-loops",
    "tools": "05-tools",
    "jobs": "06-jobs",
    "observability": "07-observability",
    "response": "08-response",
}


def install() -> None:
    global _BOUND
    if _BOUND:
        return
    root = str(_ROOT)
    if root not in sys.path:
        sys.path.insert(0, root)
    base = _ROOT / "agentic"
    for name, folder in _PACKAGES.items():
        _bind(name, base / folder)
    _BOUND = True


def _bind(name: str, directory: Path) -> None:
    if name in sys.modules:
        return
    init = directory / "__init__.py"
    spec = importlib.util.spec_from_file_location(
        name,
        init,
        submodule_search_locations=[str(directory)],
    )
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot bind {name} from {directory}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)

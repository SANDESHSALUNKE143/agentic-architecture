"""Import a Python file whose folder name contains a hyphen.

Purpose: load gateway, workflow, and engine modules that are not regular packages.
Used by: the API entrypoint, the router, and agentic/platform/composition.py.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path


def load_module(path: Path, module_name: str):
    path = Path(path)
    spec = importlib.util.spec_from_file_location(module_name, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module

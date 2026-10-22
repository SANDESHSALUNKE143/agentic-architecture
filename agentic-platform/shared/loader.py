"""Load a Python file from a hyphenated folder under a stable module name."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path


def load_module(path: Path, module_name: str):
    """Execute path as module_name. The name must be unique in this process."""
    path = Path(path)
    spec = importlib.util.spec_from_file_location(module_name, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module

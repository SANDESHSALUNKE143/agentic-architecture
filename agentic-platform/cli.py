"""Run a task from the shell.

python agentic-platform/cli.py list
python agentic-platform/cli.py run "Find a jacket and check whether it is available"
python agentic-platform/cli.py example product-discovery
"""

from __future__ import annotations

import asyncio
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT.parent / "src"))

from examples.scenarios.catalog import list_examples  # noqa: E402
from examples.scenarios.run_scenario import run_example  # noqa: E402
from orchestrator.platform import Platform  # noqa: E402
from shared.contracts import RunRequest  # noqa: E402


def main() -> None:
    command = sys.argv[1] if len(sys.argv) > 1 else "list"
    platform = Platform()
    if command == "list":
        print(json.dumps(list_examples(), indent=2))
        return
    if command == "example":
        result = asyncio.run(run_example(platform, sys.argv[2]))
    elif command == "run":
        task = sys.argv[2]
        result = asyncio.run(platform.run(RunRequest(task=task)))
    else:
        raise SystemExit("Use list, run, or example.")
    print(json.dumps(result, indent=2, default=str))


if __name__ == "__main__":
    main()

"""Direct Python runner. Usage: python examples/python/run.py product-discovery"""

from __future__ import annotations

import asyncio
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT.parent / "src"))

from examples.scenarios.catalog import EXAMPLES  # noqa: E402
from examples.scenarios.run_scenario import run_example  # noqa: E402
from orchestrator.platform import Platform  # noqa: E402


def main() -> None:
    example_id = sys.argv[1] if len(sys.argv) > 1 else "product-discovery"
    if example_id not in EXAMPLES:
        raise SystemExit(f"Unknown example {example_id}.")
    result = asyncio.run(run_example(Platform(), example_id))
    print(
        json.dumps(
            {
                "example": example_id,
                "status": result.get("status"),
                "summary": (result.get("result") or {}).get("summary")
                or result.get("run", {}).get("result", {}).get("summary"),
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()

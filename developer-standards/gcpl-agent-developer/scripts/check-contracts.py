"""Run the platform behavior suite from an explicit trusted checkout."""

import subprocess
import sys
from pathlib import Path

if __name__ == "__main__":
    root = Path(sys.argv[1]).resolve()
    if not (root / "src/agentic_sdk/execution.py").is_file():
        raise SystemExit("Expected a platform checkout")
    subprocess.run(
        [sys.executable, "-m", "unittest", "discover", "-s", "tests", "-v"],
        cwd=root,
        check=True,
    )

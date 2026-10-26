#!/usr/bin/env bash
# Create one agent from a problem statement. Restart the API after it writes the files.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")" && pwd)"
PYTHON="$ROOT/.venv/bin/python"

if [[ $# -lt 2 ]]; then
  echo "Usage: ./new-agent.sh <name> \"<the problem this agent solves>\"" >&2
  echo "Example: ./new-agent.sh claims \"Look up whether a claim is open and explain the next step\"" >&2
  exit 1
fi

if [[ ! -x "$PYTHON" ]]; then
  echo "Missing $PYTHON. Create the virtualenv and install the project first." >&2
  exit 1
fi

NAME="$1"
shift
export AGENT_ROOT="$ROOT"
export AGENT_NAME="$NAME"
export AGENT_PROBLEM="$*"

"$PYTHON" - <<'PY'
import os
import sys

sys.path.insert(0, os.environ["AGENT_ROOT"])
from agentic.platform.scaffold import create

made = create(os.environ["AGENT_NAME"], os.environ["AGENT_PROBLEM"])
print("Agent:", made["agent"])
print("Tool:", made["tool"])
print("Workflow:", made["workflow"])
print("Send this task:", made["phrase"])
print("Replace the tool function with the system that solves the problem, then restart the API.")
PY

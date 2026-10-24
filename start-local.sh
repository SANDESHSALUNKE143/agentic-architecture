#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")" && pwd)"
PYTHON="$ROOT/.venv/bin/python"
API_PID=""
UI_PID=""
MERCHANT_PID=""

cleanup() {
  if [[ -n "$API_PID" ]]; then kill "$API_PID" 2>/dev/null || true; fi
  if [[ -n "$UI_PID" ]]; then kill "$UI_PID" 2>/dev/null || true; fi
  if [[ -n "$MERCHANT_PID" ]]; then kill "$MERCHANT_PID" 2>/dev/null || true; fi
}
trap cleanup EXIT INT TERM

if [[ ! -x "$PYTHON" ]]; then
  echo "Missing $PYTHON. Create the virtualenv and install the project first." >&2
  exit 1
fi

port_open() {
  (echo >/dev/tcp/127.0.0.1/"$1") >/dev/null 2>&1
}

if port_open 8090 || port_open 5173 || port_open 8091; then
  echo "Port 8090, 8091, or 5173 is already in use. Stop that process and run this script again." >&2
  exit 1
fi

if [[ ! -d "$ROOT/apps/admin-dashboard/node_modules" ]]; then
  npm install --prefix "$ROOT/apps/admin-dashboard"
fi

"$PYTHON" "$ROOT/examples/merchant-mcp/server.py" &
MERCHANT_PID=$!
export MERCHANT_MCP_URL="${MERCHANT_MCP_URL:-http://127.0.0.1:8091/mcp}"
"$PYTHON" "$ROOT/apps/agent-api/main.py" &
API_PID=$!
npm run dev --prefix "$ROOT/apps/admin-dashboard" &
UI_PID=$!

for _ in $(seq 1 50); do
  if curl -fsS -H "Authorization: Bearer local-dev-token-not-for-production" http://127.0.0.1:8090/health >/dev/null 2>&1; then
    echo "API http://127.0.0.1:8090"
    echo "Merchant MCP http://127.0.0.1:8091/mcp"
    echo "Dashboard http://127.0.0.1:5173"
    wait
    exit 0
  fi
  sleep 0.2
done

echo "The API did not become healthy." >&2
exit 1

#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")" && pwd)"
if [[ -x "$ROOT/.venv/bin/python" ]]; then
  PYTHON="$ROOT/.venv/bin/python"
elif [[ -x "$ROOT/../.venv/bin/python" ]]; then
  PYTHON="$ROOT/../.venv/bin/python"
else
  PYTHON="$ROOT/.venv/bin/python"
fi
if [[ -f "$ROOT/.env" ]]; then
  set -a
  # shellcheck disable=SC1091
  source "$ROOT/.env"
  set +a
fi
TOKEN="${PLATFORM_DEV_TOKEN:-local-dev-token-not-for-production}"
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

if port_open 8092 || port_open 5174 || port_open 8093; then
  echo "Port 8092, 8093, or 5174 is already in use. Stop that process and run this script again." >&2
  exit 1
fi

if [[ ! -d "$ROOT/ui/admin-dashboard/node_modules" ]]; then
  npm install --prefix "$ROOT/ui/admin-dashboard"
fi

MERCHANT_MCP_HOST=127.0.0.1 MERCHANT_MCP_PORT=8093 "$PYTHON" "$ROOT/mocks/merchant/server.py" &
MERCHANT_PID=$!
export MERCHANT_MCP_URL="${MERCHANT_MCP_URL:-http://127.0.0.1:8093/mcp}"
export PLATFORM_BIND_PORT="${PLATFORM_BIND_PORT:-8092}"
"$PYTHON" "$ROOT/agentic/01-entry/main.py" &
API_PID=$!
npm run dev --prefix "$ROOT/ui/admin-dashboard" &
UI_PID=$!

for _ in $(seq 1 50); do
  if curl -fsS -H "Authorization: Bearer $TOKEN" http://127.0.0.1:8092/health >/dev/null 2>&1; then
    echo "API http://127.0.0.1:8092"
    echo "Merchant MCP http://127.0.0.1:8093/mcp"
    echo "Dashboard http://127.0.0.1:5174"
    wait
    exit 0
  fi
  sleep 0.2
done

echo "The API did not answer on port 8092." >&2
exit 1

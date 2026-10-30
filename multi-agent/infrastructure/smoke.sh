#!/usr/bin/env bash
# Prove the server path: health, the seven-step map, and one catalog run.
set -euo pipefail

BASE="${1:-http://127.0.0.1:5173}"
TOKEN="${PLATFORM_DEV_TOKEN:-local-dev-token-not-for-production}"
AUTH="Authorization: Bearer ${TOKEN}"

health=""
for _ in $(seq 1 30); do
  if health="$(curl -fsS -H "$AUTH" "$BASE/health")"; then
    break
  fi
  health=""
  sleep 1
done
if [[ -z "$health" ]]; then
  echo "The console did not answer $BASE/health" >&2
  curl -sS -D - -H "$AUTH" "$BASE/health" >&2 || true
  exit 1
fi
printf '%s' "$health" | grep -q '"status": *"ok"'
printf '%s' "$health" | grep -q '"agents": *8'

platform="$(curl -fsS -H "$AUTH" "$BASE/platform")"
for step in perception planning foundation_model memory action learning communication; do
  printf '%s' "$platform" | grep -q "\"id\": *\"$step\""
done
printf '%s' "$platform" | grep -q '"security"'
printf '%s' "$platform" | grep -q '"observability"'
printf '%s' "$platform" | grep -q 'agentic/04-loops/specialists/<name>/agent.yaml'
printf '%s' "$platform" | grep -q 'agentic/03-workflows/sequences/<name>/workflow.yaml'

run="$(curl -fsS -H "$AUTH" -H "Content-Type: application/json" \
  -d '{"task":"Find a blue trail jacket under $150","agents":["catalog-agent"]}' \
  "$BASE/agent-runs")" || {
  echo "The catalog run did not complete" >&2
  exit 1
}
if ! printf '%s' "$run" | grep -q 'search_products' || ! printf '%s' "$run" | grep -q '"status": *"completed"'; then
  echo "$run" >&2
  exit 1
fi

echo "Server smoke passed at $BASE"

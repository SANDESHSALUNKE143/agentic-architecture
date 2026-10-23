#!/usr/bin/env bash
# Prove the server path: health, the seven-step map, and one catalog run.
set -euo pipefail

BASE="${1:-http://127.0.0.1:5173}"
TOKEN="${PLATFORM_DEV_TOKEN:-local-dev-token-not-for-production}"
AUTH="Authorization: Bearer ${TOKEN}"

health="$(curl -fsS -H "$AUTH" "$BASE/health")"
printf '%s' "$health" | grep -q '"status": *"ok"'
printf '%s' "$health" | grep -q '"agents": *8'

platform="$(curl -fsS -H "$AUTH" "$BASE/platform")"
for step in perception planning foundation_model memory action learning communication; do
  printf '%s' "$platform" | grep -q "\"id\": *\"$step\""
done
printf '%s' "$platform" | grep -q '"security"'
printf '%s' "$platform" | grep -q '"observability"'
printf '%s' "$platform" | grep -q 'agents/<name>/agent.yaml'
printf '%s' "$platform" | grep -q 'workflows/<name>/workflow.py'

run="$(curl -fsS -H "$AUTH" -H "Content-Type: application/json" \
  -d '{"task":"Find a blue trail jacket under $150","agents":["catalog-agent"]}' \
  "$BASE/agent-runs")"
printf '%s' "$run" | grep -q 'search_products'
printf '%s' "$run" | grep -q '"status": *"completed"'

echo "Server smoke passed at $BASE"

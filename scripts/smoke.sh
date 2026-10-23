#!/usr/bin/env bash
# Smoke test against the deployed app. Usage: FRONTEND_URL=https://... [BACKEND_URL=https://...] bash scripts/smoke.sh
set -euo pipefail
: "${FRONTEND_URL:?set FRONTEND_URL}"

check() { # url, expected text
  body=$(curl -fsSL --max-time 30 "$1") || { echo "FAIL $1 (HTTP error)"; exit 1; }
  grep -q "$2" <<<"$body" || { echo "FAIL $1 (missing: $2)"; exit 1; }
  echo "ok   $1"
}

check "$FRONTEND_URL/" "RivalLens"
check "$FRONTEND_URL/app" "Your businesses"
check "$FRONTEND_URL/app/stacknest-demo/dashboard" "Sample data"
check "$FRONTEND_URL/app/demo-lab" "Demo Lab"

if [[ -n "${BACKEND_URL:-}" ]]; then
  check "$BACKEND_URL/healthz" '"ok"'
fi
echo "smoke passed"

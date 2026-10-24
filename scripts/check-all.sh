#!/usr/bin/env bash
# Before and after each deploy: unit tests (recorded LLM answers), live smoke, account isolation, and the live founder checks.
# Usage: PW=<playwright-core dir> CHROME=<chrome.exe> bash scripts/check-all.sh [--full]
#   --full also walks a brand-new founder end to end (about 12 minutes; creates a test account).
# Needs api/.env (SUPABASE_URL, SUPABASE_ANON_KEY) and the isolation user A: ISO_EMAIL / ISO_PASSWORD.
set -euo pipefail
cd "$(dirname "$0")/.."
FRONTEND_URL=${FRONTEND_URL:-https://rivallens-eight.vercel.app}
BACKEND_URL=${BACKEND_URL:-https://rivallens-api.onrender.com}
OUT=${OUT:-$(mktemp -d)}
set -a; . api/.env; set +a

echo "== unit tests"
(cd api && LLM_MODE=replay .venv/Scripts/python -m pytest -q | tail -1)
echo "== web typecheck"
(cd web && npx tsc --noEmit -p .)
echo "== smoke"
FRONTEND_URL=$FRONTEND_URL BACKEND_URL=$BACKEND_URL bash scripts/smoke.sh | tail -1
echo "== account isolation"
(cd api && LLM_MODE=replay .venv/Scripts/python -m scripts.isolation_check "${ISO_EMAIL:?set ISO_EMAIL}" "${ISO_PASSWORD:?set ISO_PASSWORD}" 2>&1 | grep -v "INFO httpx" | tail -2)
echo "== overview (desktop and phone)"
node scripts/e2e/overview.cjs "${PW:?set PW}" "$OUT" "${CHROME:?set CHROME}" | grep -E "RETURN VISIT"
echo "== simulator (changes and resets an assumption on the Stride demo)"
node scripts/e2e/simulator.cjs "$PW" "$OUT" "$CHROME" | grep -E "BEFORE|AFTER|LATEST|RESET|FAILED"
if [[ "${1:-}" == "--full" ]]; then
  echo "== new founder, end to end"
  node scripts/e2e/first-insight.cjs "$PW" "$OUT" "$CHROME" | grep -E "^[1-5] |FAILED"
fi
echo "all checks done; screenshots in $OUT"

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
check "$FRONTEND_URL/login" "Kesar Bakehouse"   # the four demo sign-ins
check "$FRONTEND_URL/app" "RivalLens"
check "$FRONTEND_URL/mock/seed-nimbusdeploy/nimbusdeploy" "Demo data: fictional company"
check "$FRONTEND_URL/robots.txt" "/mock/"

if [[ -n "${BACKEND_URL:-}" ]]; then
  check "$BACKEND_URL/healthz" '"ok"'
  code=$(curl -s -o /dev/null -w "%{http_code}" --max-time 30 "$BACKEND_URL/api/v1/profiles")
  [[ "$code" == 401 ]] && echo "ok   $BACKEND_URL/api/v1/profiles (401 without token)" || { echo "FAIL profiles without token returned $code"; exit 1; }
  for path in api/v1/demo/mocks api/v1/products/00000000-0000-0000-0000-000000000000/simulation               api/v1/products/00000000-0000-0000-0000-000000000000/segment api/v1/profiles/00000000-0000-0000-0000-000000000000/money api/v1/profiles/00000000-0000-0000-0000-000000000000/setup; do
    code=$(curl -s -o /dev/null -w "%{http_code}" --max-time 30 "$BACKEND_URL/$path")
    [[ "$code" == 401 ]] && echo "ok   $BACKEND_URL/$path (401 without token)" || { echo "FAIL $path without token returned $code"; exit 1; }
  done
  if [[ -n "${SUPABASE_URL:-}" && -n "${SUPABASE_ANON_KEY:-}" ]]; then  # each demo business signs in and has products
    for email in stride bakery stacknest quickkart; do
      token=$(curl -fsS --max-time 30 "$SUPABASE_URL/auth/v1/token?grant_type=password" -H "apikey: $SUPABASE_ANON_KEY" -H "Content-Type: application/json" \
        -d "{\"email\":\"$email@rivallens.demo\",\"password\":\"RivalLens-demo-2026\"}" | sed -E 's/.*"access_token":"([^"]+)".*/\1/')
      pid=$(curl -fsS --max-time 60 "$BACKEND_URL/api/v1/profiles" -H "Authorization: Bearer $token" | sed -E 's/^\[\{"id":"([^"]+)".*/\1/')
      n=$(curl -fsS --max-time 60 "$BACKEND_URL/api/v1/profiles/$pid/products" -H "Authorization: Bearer $token" | grep -o '"taxonomy_id"' | wc -l)
      [[ "$n" -ge 1 ]] && echo "ok   demo $email: $n products" || { echo "FAIL demo $email has no products"; exit 1; }
    done
  fi
fi
echo "smoke passed"

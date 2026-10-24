"""Account isolation sweep against the live API (Workstream 5).

Every route in the app is called (1) without a token: anything but 401 is listed; (2) as user B with user A's real ids:
any 2xx is a leak. A is an existing test founder with a business, products, competitors, runs and jobs; B is created fresh.
Destructive calls are sent too: if one succeeded, that is exactly the bug this finds.

Usage (from api/, SUPABASE_URL and SUPABASE_ANON_KEY in the environment):
  .venv/Scripts/python -m scripts.isolation_check <user A email> <user A password>
"""
import os
import re
import sys
import time

import httpx

from app.main import app

API = os.getenv("API_URL", "https://rivallens-api.onrender.com")
SUPABASE_URL, ANON = os.environ["SUPABASE_URL"], os.environ["SUPABASE_ANON_KEY"]
PUBLIC = {("POST", "/api/v1/accounts"), ("GET", "/api/v1/taxonomy"), ("GET", "/healthz"), ("GET", "/api/v1/mock/{instance}/{slug}"),
          ("POST", "/api/v1/cron/checks")}  # only starts checks already due


def token(email: str, password: str) -> str:
    r = httpx.post(f"{SUPABASE_URL}/auth/v1/token?grant_type=password", headers={"apikey": ANON},
                   json={"email": email, "password": password}, timeout=30)
    r.raise_for_status()
    return r.json()["access_token"]


def main(a_email: str, a_password: str) -> int:
    a = httpx.Client(base_url=API, headers={"Authorization": f"Bearer {token(a_email, a_password)}"}, timeout=120)
    pid = a.get("/api/v1/profiles").json()[0]["id"]
    ids = {"profile_id": pid}
    if prods := a.get(f"/api/v1/profiles/{pid}/products").json():
        ids["product_id"] = prods[0]["id"]
    if comps := a.get(f"/api/v1/profiles/{pid}/competitors").json():
        ids["competitor_id"] = comps[0]["id"]
        if comps[0]["sources"]:
            ids["source"] = comps[0]["sources"][0]["id"]
    from sqlalchemy import text
    from app.db import engine
    with engine.connect() as conn:  # the rest of A's ids straight from the database
        for key, sql in (("run_id", "select id from runs where profile_id = :p limit 1"),
                         ("job_id", "select id from jobs where profile_id = :p limit 1"),
                         ("snapshot_id", "select sn.id from snapshots sn join sources s on s.id = sn.source_id join competitors c on c.id = s.competitor_id where c.profile_id = :p limit 1"),
                         ("receipt_id", "select e.id from change_events e join competitors c on c.id = e.competitor_id where c.profile_id = :p limit 1"),
                         ("report_id", "select id from reports where profile_id = :p limit 1"),
                         ("alert_id", "select id from alerts where profile_id = :p limit 1")):
            try:
                if v := conn.execute(text(sql), {"p": pid}).scalar():
                    ids[key] = str(v)
            except Exception:
                conn.rollback()
    print("A's ids:", {k: v[:8] for k, v in ids.items()})

    b_email, b_password = f"isolation-{int(time.time())}@rivallens.test", "Isolation-test-2026"
    httpx.post(f"{API}/api/v1/accounts", json={"email": b_email, "password": b_password}, timeout=60).raise_for_status()
    b = httpx.Client(base_url=API, headers={"Authorization": f"Bearer {token(b_email, b_password)}"}, timeout=120)
    anon = httpx.Client(base_url=API, timeout=60)

    leaks, open_routes, skipped, checked = [], [], [], 0
    for path, ops in app.openapi()["paths"].items():  # every route, including routers FastAPI includes lazily
        if not path.startswith("/api/"):
            continue
        for method in sorted(m.upper() for m in ops):
            if (method, path) in PUBLIC:
                continue
            params = re.findall(r"{(\w+)(?::\w+)?}", path)
            r = anon.request(method, re.sub(r"{(\w+)(?::\w+)?}", "00000000-0000-0000-0000-000000000000", path), json={})
            if r.status_code != 401:
                open_routes.append(f"{method} {path} → {r.status_code} without a token")
            if not params:
                continue  # B's own list endpoints: nothing of A's to reach
            if any(p not in ids for p in params):
                skipped.append(f"{method} {path}")
                continue
            url = re.sub(r"{(\w+)(?::\w+)?}", lambda m: ids[m.group(1)], path)
            r = b.request(method, url, json={})
            checked += 1
            if 200 <= r.status_code < 300:
                leaks.append(f"{method} {path} → {r.status_code}: B reached A's data")
    print(f"checked {checked} routes as user B with A's ids; skipped (no id of that kind): {len(skipped)}")
    for line in skipped:
        print("  skipped", line)
    for line in open_routes:
        print("OPEN", line)
    for line in leaks:
        print("LEAK", line)
    print("isolation passed" if not leaks and not open_routes else "isolation FAILED")
    return 1 if leaks or open_routes else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1], sys.argv[2]))

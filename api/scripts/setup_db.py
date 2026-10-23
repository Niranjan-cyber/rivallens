"""Apply migrations and (re)load demo seed data. Re-runnable.

Usage (from api/): .venv/Scripts/python -m scripts.setup_db [--migrate] [--seed]
"""
import json
import secrets
import sys
from pathlib import Path

import httpx
from sqlalchemy import text

from app import jobs
from app.config import MOCK_BASE_URL, SEED_USER_EMAIL, SUPABASE_SECRET_KEY, SUPABASE_URL
from app.db import engine
from app.modules.changes.runs import monitor, start_run

MIGRATIONS = Path(__file__).resolve().parents[2] / "supabase" / "migrations"

MOCKS = [("NimbusDeploy (demo)", "nimbusdeploy"), ("KiteHost (demo)", "kitehost"), ("Orbitly Cloud (demo)", "orbitly")]

PROFILES = [
    {"name": "StackNest", "kind": "business", "offering_type": "service",
     "card": {"note": "Cloud deployment, Pune", "category": "Managed app deployment", "india_markets": ["Pune", "Bengaluru"],
              "price": {"amount": 999, "currency": "INR", "period": "month"}},
     "competitors": [*[(n, f"{s}.demo", "comparable", True) for n, s in MOCKS],
                     ("Render", "render.com", "comparable", False), ("Railway", "railway.com", "comparable", False),
                     ("E2E Networks", "e2enetworks.com", "comparable", False)]},
    {"name": "QuickKart", "kind": "business", "offering_type": "service", "card": {"note": "Quick commerce, Bengaluru"}, "competitors": []},
    {"name": "Stride & Co.", "kind": "business", "offering_type": "product", "card": {"note": "Running shoes, D2C"}, "competitors": []},
    {"name": "Qubit Labs", "kind": "idea", "offering_type": "service", "card": {"note": "Quantum computing access"}, "competitors": []},
]


def migrate() -> None:
    with engine.begin() as conn:
        for f in sorted(MIGRATIONS.glob("*.sql")):
            conn.exec_driver_sql(f.read_text(encoding="utf-8"))
            print("applied", f.name)


def ensure_seed_user() -> str:
    headers = {"apikey": SUPABASE_SECRET_KEY, "Authorization": f"Bearer {SUPABASE_SECRET_KEY}"}
    with engine.begin() as conn:
        uid = conn.execute(text("select id from auth.users where email = :e"), {"e": SEED_USER_EMAIL}).scalar()
    if uid:
        return str(uid)
    r = httpx.post(f"{SUPABASE_URL}/auth/v1/admin/users", headers=headers, timeout=20,
                   json={"email": SEED_USER_EMAIL, "password": secrets.token_urlsafe(24), "email_confirm": True})
    r.raise_for_status()
    return r.json()["id"]


def ensure_bucket() -> None:
    headers = {"apikey": SUPABASE_SECRET_KEY, "Authorization": f"Bearer {SUPABASE_SECRET_KEY}"}
    r = httpx.post(f"{SUPABASE_URL}/storage/v1/bucket", headers=headers, timeout=20, json={"id": "snapshots", "name": "snapshots", "public": False})
    if r.status_code not in (200, 409) and "already exists" not in r.text:
        r.raise_for_status()


def seed() -> None:
    uid = ensure_seed_user()
    ensure_bucket()
    with engine.begin() as conn:
        conn.execute(text("delete from profiles where user_id = :u"), {"u": uid})
        conn.execute(text("delete from mock_instances where user_id = :u"), {"u": uid})
        for _, slug in MOCKS:
            conn.execute(text("insert into mock_instances (user_id, instance_key, slug) values (:u, :k, :s)"), {"u": uid, "k": f"seed-{slug}", "s": slug})
        for p in PROFILES:
            pid = conn.execute(text("""
                insert into profiles (user_id, name, kind, offering_type, card, is_demo_data)
                values (:u, :name, :kind, :ot, cast(:card as jsonb), true) returning id
            """), {"u": uid, "name": p["name"], "kind": p["kind"], "ot": p["offering_type"], "card": json.dumps(p["card"])}).scalar()
            for name, domain, relation, is_mock in p["competitors"]:
                cid = conn.execute(text("""
                    insert into competitors (profile_id, name, domain, relation, origin, is_demo_data)
                    values (:p, :n, :d, :r, 'seed', true) returning id
                """), {"p": pid, "n": name, "d": domain, "r": relation}).scalar()
                url = f"{MOCK_BASE_URL}/seed-{domain.removesuffix('.demo')}/{domain.removesuffix('.demo')}" if is_mock else f"https://{'www.' if domain == 'e2enetworks.com' else ''}{domain}/pricing"
                conn.execute(text("insert into sources (competitor_id, url, page_type, is_mock) values (:c, :url, 'pricing', :m)"),
                             {"c": cid, "url": url, "m": is_mock})
            if p["name"] == "StackNest":
                stacknest = pid
    print("seeded", len(PROFILES), "profiles for", SEED_USER_EMAIL)

    # Baseline run over the mock pages: guest clones copy these snapshots as their starting point.
    job_id = jobs.create(uid, stacknest, "baseline")
    run_id = start_run(stacknest, job_id)
    jobs.run(job_id, lambda job: monitor(job, stacknest, run_id))
    with engine.begin() as conn:
        print("baseline", conn.execute(text("select status, counts from runs where id = :r"), {"r": run_id}).one())


if __name__ == "__main__":
    if "--migrate" in sys.argv:
        migrate()
    if "--seed" in sys.argv:
        seed()

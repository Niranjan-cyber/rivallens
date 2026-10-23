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
              "price": {"amount": 999, "currency": "INR", "period": "month"},
              "attributes": ["Autoscaling", "Preview environments", "Free SSL", "Email support", "Mumbai region"],
              # Labelled "your assumption" on S-14: a Pune deployment startup's own numbers, not defaults
              "sim_assumptions": {"segment_size": 20000, "upfront_cost": 300000, "monthly_cost": 100000}},
     "competitors": [*[(n, f"{s}.demo", "inspiration" if s == "orbitly" else "comparable", True) for n, s in MOCKS],
                     ("Render", "render.com", "inspiration", False), ("Railway", "railway.com", "inspiration", False),
                     ("E2E Networks", "e2enetworks.com", "comparable", False)]},
    {"name": "QuickKart", "kind": "business", "offering_type": "service", "card": {"note": "Quick commerce, Bengaluru"}, "competitors": []},
    {"name": "Stride & Co.", "kind": "business", "offering_type": "product", "card": {"note": "Running shoes, D2C"}, "competitors": []},
    {"name": "Qubit Labs", "kind": "idea", "offering_type": "service",
     "card": {"note": "Quantum computing access", "category": "Quantum computing access",
              "price": {"amount": 50000, "currency": "INR", "period": "month"},
              "planned_features": ["Hosted quantum processor time", "Simulator access", "Research support"],
              "sim_assumptions": {"segment_size": 60, "upfront_cost": 50000000, "monthly_cost": 2500000}},
     "competitors": []},
]


# What india_signals() finds on these pages (mock pages: ₹ prices, "Servers in India", GST; E2E fixture: see test_discovery).
_MOCK_SIGNALS = {"score": 4, "hits": ["₹ / INR / Rs.", "India or an Indian city", "GST / GSTIN"]}
INDIA_SIGNALS = {"nimbusdeploy": _MOCK_SIGNALS, "kitehost": _MOCK_SIGNALS, "orbitly": _MOCK_SIGNALS,
                 "e2enetworks.com": {"score": 4, "hits": ["India or an Indian city", "+91 phone number", "GST / GSTIN", "India region"]}}


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


FIXTURES = Path(__file__).resolve().parents[2] / "fixtures" / "pricing-pages"
FIXTURE_FETCHED_AT = "2026-10-23T10:50:00Z"  # fixtures/README.md: fetched 23 Oct 2026 ~16:20 IST


def _plan(name, amount, currency, period, raw, features=()):
    return {"name": name, "price": {"amount": amount, "currency": currency, "period": period, "raw": raw}, "features": list(features), "method": "manual_seed"}


# Values read by hand from the frozen fixture pages (only what the page states). Render's fixture has no readable prices.
REAL_OBSERVATIONS = {
    "railway.com": ("railway", {"plans": [_plan("Hobby", 5, "USD", "month", "$5 minimum usage", ["Includes $5 of monthly usage credits"]),
                                          _plan("Pro", 20, "USD", "month", "$20 minimum usage", ["Includes $20 of monthly usage credits"])],
                                "headline": {"text": "Pay only for what your app uses, by the second", "method": "manual_seed"}, "extraction_status": "ok"}),
    "e2enetworks.com": ("e2enetworks", {"plans": [_plan("B200 GPU", 7.99, "USD", "hour", "$7.99 /hr")],
                                        "headline": {"text": "Simple GPU pricing that scales with your AI ambitions", "method": "manual_seed"},
                                        "extraction_status": "partial"}),
}


def seed_real_observations(profile_id) -> None:
    """Seeded real competitors aren't fetched in demo runs (D-61); give them a dated observation from the frozen fixtures."""
    from app.modules.collector.service import sha, split_sections
    with engine.begin() as conn:
        for domain, (fixture, fields) in REAL_OBSERVATIONS.items():
            src = conn.execute(text("select s.id from sources s join competitors c on c.id = s.competitor_id where c.profile_id = :p and c.domain = :d"),
                               {"p": profile_id, "d": domain}).scalar()
            html = (FIXTURES / f"{fixture}-pricing.html").read_text(encoding="utf-8", errors="replace")
            body, sections = split_sections(html)
            snap = conn.execute(text("""insert into snapshots (source_id, observed_at, status, http_status, sha256, text, sections, bytes)
                values (:s, :t, 'ok', 200, :h, :x, cast(:sec as jsonb), :b) returning id"""),
                {"s": src, "t": FIXTURE_FETCHED_AT, "h": sha(html), "x": body, "sec": json.dumps(sections), "b": len(html)}).scalar()
            conn.execute(text("insert into observations (snapshot_id, source_id, observed_at, fields, origin) values (:i, :s, :t, cast(:f as jsonb), 'seed')"),
                         {"i": snap, "s": src, "t": FIXTURE_FETCHED_AT, "f": json.dumps(fields)})


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
                signals = INDIA_SIGNALS.get(domain.removesuffix(".demo") if is_mock else domain, {})
                cid = conn.execute(text("""
                    insert into competitors (profile_id, name, domain, relation, origin, is_demo_data, india_signals)
                    values (:p, :n, :d, :r, 'seed', true, cast(:i as jsonb)) returning id
                """), {"p": pid, "n": name, "d": domain, "r": relation, "i": json.dumps(signals)}).scalar()
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
    seed_real_observations(stacknest)  # after the baseline, so that run is still recorded as kind=baseline


if __name__ == "__main__":
    if "--migrate" in sys.argv:
        migrate()
    if "--seed" in sys.argv:
        seed()

"""B14j: build the demo businesses by calling the live API exactly as a user's browser does (D-75, D-76).

Inputs are licensed datasets (fixtures/demo/, see each README) and public pages; every result on the dashboards is computed
by the same pipeline a real user gets. Only two things are written straight to the database: the demo label, and the
fictional competitor pages (mock_instances) used by "Simulate a competitor move".

    cd api && .venv/Scripts/python -m scripts.build_demo stride stacknest bakery quickkart
"""
import json
import secrets
import sys
import time
from pathlib import Path

import httpx
from sqlalchemy import text

from app.config import SUPABASE_SECRET_KEY, SUPABASE_URL
from app.db import engine

API = "https://rivallens-api.onrender.com"
MOCK_BASE = "https://rivallens-eight.vercel.app/mock"
PASSWORD = "RivalLens-demo-2026"
FIX = Path(__file__).resolve().parents[2] / "fixtures" / "demo"
ANON_KEY = __import__("os").environ["SUPABASE_ANON_KEY"]

BUSINESSES = {
    "stride": {
        "email": "stride@rivallens.demo",
        "about": {"name": "Stride & Co.", "business_type": "D2C brand", "city": "Pune",
                  "description": "Running shoes for Indian roads, sold online",
                  "products": "Stride Runner, Stride Trail, Running socks", "funding_stage": "Angel",
                  "target_customer": "Recreational runners aged 22-40 in Indian metros"},
        "basis": "Campus Activewear's FY26 margins and the UCI Online Retail II order pattern",
        "prices": {"Stride Runner": 1999, "Stride Trail": 2499, "Running socks": 299},
        "money_files": ["stride/orders-oct2025-sep2026.xlsx", "stride/bank-statement-oct2025-sep2026.csv"],
        "cash": 2716169,  # closing balance of the bank statement
        "rivals": ["Campus Activewear", "Nivia", "Neemans"],
        "competitors": ["https://www.niviasports.com/", "https://neemans.com/", "https://www.campusshoes.com/"],
        "mocks": ["zephyrpace", "monsoonmiles"],
        "comparables": ["Stride Runner", "Stride Trail"],
    },
    "stacknest": {
        "email": "stacknest@rivallens.demo",
        "about": {"name": "StackNest", "business_type": "SaaS", "city": "Pune",
                  "description": "Managed app deployment for Indian startups: deploy from Git, autoscaling, servers in India",
                  "products": "StackNest Pro", "funding_stage": "Bootstrapped",
                  "target_customer": "Early-stage Indian startups and agencies shipping web apps"},
        "basis": "real Indian and global cloud hosts' public pricing pages",
        "prices": {"StackNest Pro": 999},
        "units": {"StackNest Pro": "month"},
        "rivals": ["E2E Networks"],
        "competitors": ["https://www.e2enetworks.com/pricing", "https://render.com/pricing", "https://railway.com/pricing"],
        "mocks": ["nimbusdeploy", "kitehost", "orbitly"],
        "comparables": [],
    },
    "quickkart": {
        "email": "quickkart@rivallens.demo",
        "about": {"name": "QuickKart", "business_type": "Startup", "city": "Bengaluru",
                  "description": "Quick commerce: groceries delivered in 10 minutes, with a monthly free-delivery membership",
                  "products": "QuickKart Pass", "funding_stage": "Seed",
                  "target_customer": "Working professionals in Bengaluru apartments"},
        "basis": "Eternal (Blinkit) and Swiggy (Instamart) public filings",
        "prices": {"QuickKart Pass": 129},
        "units": {"QuickKart Pass": "month"},
        "rivals": ["Eternal", "Swiggy"],
        "competitors": [],
        "mocks": [],
        "comparables": [],
    },
}


def log(*a):
    print(time.strftime("%H:%M:%S"), *a, flush=True)


def admin() -> dict:
    return {"apikey": SUPABASE_SECRET_KEY, "Authorization": f"Bearer {SUPABASE_SECRET_KEY}"}


def reset_user(email: str) -> None:
    with engine.connect() as conn:
        uid = conn.execute(text("select id from auth.users where email = :e"), {"e": email}).scalar()
    if uid:  # profiles, products, transactions, mentions and mock instances go with it (on delete cascade)
        httpx.delete(f"{SUPABASE_URL}/auth/v1/admin/users/{uid}", headers=admin(), timeout=30).raise_for_status()
        log("deleted", email)
    r = httpx.post(f"{API}/api/v1/accounts", json={"email": email, "password": PASSWORD}, timeout=60)
    r.raise_for_status()


def client(email: str) -> httpx.Client:
    r = httpx.post(f"{SUPABASE_URL}/auth/v1/token?grant_type=password", headers={"apikey": ANON_KEY},
                   json={"email": email, "password": PASSWORD}, timeout=30)
    r.raise_for_status()
    return httpx.Client(base_url=API, headers={"Authorization": f"Bearer {r.json()['access_token']}"}, timeout=120)


def wait(c: httpx.Client, job_id: str, what: str, limit: int = 600) -> dict:
    for _ in range(limit // 3):
        job = c.get(f"/api/v1/jobs/{job_id}").raise_for_status().json()
        if job["status"] in ("done", "failed", "stale"):
            log(f"  {what}: {job['status']}", json.dumps(job.get("result") or job.get("error"), ensure_ascii=False)[:300])
            return job
        time.sleep(3)
    log(f"  {what}: still running after {limit}s")
    return {}


def onboard(c: httpx.Client, b: dict) -> str:
    """The onboarding page: draft the card from the answers, then the answers win over the draft (web/app/app/new/page.tsx)."""
    a = b["about"]
    desc = f"{a['name']}, {a['business_type']} in {a['city']}. {a['description']} Products: {a['products']}. Customers: {a['target_customer']}."
    job = wait(c, c.post("/api/v1/profiles/draft", json={"kind": "business", "description": desc[:500]}).raise_for_status().json()["job_id"], "draft card")
    card = {k: {"value": v, "origin": "ai_drafted"} for k, v in (job.get("result") or {}).items() if v not in (None, "", [])}
    mine = {"name": a["name"], "business_type": a["business_type"], "india_markets": [a["city"]], "description": a["description"],
            "main_products": [p.strip() for p in a["products"].split(",")], "funding_stage": a["funding_stage"], "target_customer": a["target_customer"]}
    card |= {k: {"value": v, "origin": "user"} for k, v in mine.items()}
    card["demo_basis"] = {"value": b["basis"], "origin": "public_source"}
    offering = "product" if (card.get("offering_type") or {}).get("value") == "product" else "service"
    pid = c.post("/api/v1/profiles", json={"kind": "business", "offering_type": offering, "name": a["name"], "card": card}).raise_for_status().json()["id"]
    with engine.begin() as conn:  # the label, before any upload, so every row inherits it
        conn.execute(text("update profiles set is_demo_data = true where id = :p"), {"p": pid})
    log("  profile", pid)
    return pid


def products(c: httpx.Client, pid: str, b: dict) -> dict:
    want = len(b["prices"])
    for _ in range(60):  # products are classified on a thread after the profile is saved
        items = c.get(f"/api/v1/profiles/{pid}/products").raise_for_status().json()
        if len(items) >= want:
            break
        time.sleep(3)
    out = {}
    for p in items:
        if p["name"] in b["prices"]:
            body = {"price": b["prices"][p["name"]], "unit": b.get("units", {}).get(p["name"], "one_time")}
            c.patch(f"/api/v1/products/{p['id']}", json=body).raise_for_status()
        out[p["name"]] = p["id"]
        log(f"  product {p['name']}: {p['category_path']} / {p['niche']}")
    return out


def upload(c: httpx.Client, pid: str, area: str, path: Path) -> dict:
    files = lambda: {"file": (path.name, path.read_bytes())}
    prev = c.post(f"/api/v1/profiles/{pid}/{area}/preview", files=files()).raise_for_status().json()
    data = {"mapping": json.dumps(prev["mapping"])} | ({"kind": prev["kind"]} if area == "customers" else {})
    out = c.post(f"/api/v1/profiles/{pid}/{area}/import", files=files(), data=data).raise_for_status().json()
    log(f"  {area} upload {path.name}:", out)
    return out


def competitors(c: httpx.Client, pid: str, user_id: str, b: dict) -> None:
    urls = list(b["competitors"])
    with engine.begin() as conn:
        for slug in b["mocks"]:
            key = secrets.token_urlsafe(8)
            conn.execute(text("insert into mock_instances (user_id, instance_key, slug) values (:u, :k, :s)"), {"u": user_id, "k": key, "s": slug})
            urls.append(f"{MOCK_BASE}/{key}/{slug}")
    for url in urls:
        r = c.post(f"/api/v1/profiles/{pid}/competitors", json={"url": url})
        log(f"  competitor {url[:60]}: {r.status_code}", "" if r.is_success else r.text[:160])
    if urls:
        wait(c, c.post(f"/api/v1/profiles/{pid}/monitoring/start").raise_for_status().json()["job_id"], "baseline check")


def build(key: str) -> None:
    b = BUSINESSES[key]
    log("building", key)
    reset_user(b["email"])
    c = client(b["email"])
    pid = onboard(c, b)
    with engine.connect() as conn:
        user_id = conn.execute(text("select user_id from profiles where id = :p"), {"p": pid}).scalar()
    ids = products(c, pid, b)
    for f in b.get("money_files", []):
        upload(c, pid, "money", FIX / f)
    if b.get("cash"):
        c.put(f"/api/v1/profiles/{pid}/money/settings", json={"cash": b["cash"]}).raise_for_status()
    for f in b.get("review_files", []):
        out = upload(c, pid, "customers", FIX / f)
        if out.get("job_id"):
            wait(c, out["job_id"], "customer themes")
    competitors(c, pid, user_id, b)
    for name in b["comparables"]:
        wait(c, c.post(f"/api/v1/products/{ids[name]}/comparables/find").raise_for_status().json()["job_id"], f"comparables for {name}")
    if b["rivals"]:
        wait(c, c.post(f"/api/v1/profiles/{pid}/money/rivals/find", json={"companies": b["rivals"]}).raise_for_status().json()["job_id"], "competitor money")
    if b.get("collect", True):
        wait(c, c.post(f"/api/v1/profiles/{pid}/customers/collect").raise_for_status().json()["job_id"], "customer mentions")
    r = c.post(f"/api/v1/profiles/{pid}/market/news")
    log("  market news:", r.json() if r.is_success else r.text[:160])
    log("done", key, b["email"])


if __name__ == "__main__":
    for k in sys.argv[1:] or list(BUSINESSES):
        build(k)

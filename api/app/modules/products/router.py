"""B14c products: existing and new products of a business, each in an exact category (UC-16, S-22)."""
import json
import logging
import threading
import time
from datetime import UTC, datetime
from typing import Literal
from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import Connection, text

from app import jobs
from app.auth import UserDep
from app.modules.discovery.pipeline import card_value
from app.db import ConnDep
from app.modules.collector.service import fetch
from app.modules.products.classify import classify, classify_many
from app.modules.discovery.service import registrable_domain
from app.modules.products.market import find_comparables, hint, in_category, niche_overlap, price_position, screen_prices
from app.modules.products.news import fetch_news, queries_for
from app.modules.products.pages import product_from_html
from app.modules.products.taxonomy import candidates, path_of

router = APIRouter(prefix="/api/v1", tags=["products"])
log = logging.getLogger(__name__)
COLS = ("id, profile_id, name, stage, description, url, taxonomy_id, category_path, niche, category_source, price, currency, unit, "
        "unit_cost, features, add_ons, source, is_demo_data, created_at")
Unit = Literal["one_time", "month", "year", "hour", "user"]


class Product(BaseModel):
    id: UUID
    profile_id: UUID
    name: str
    stage: Literal["existing", "new"]
    description: str | None
    url: str | None
    taxonomy_id: int | None
    category_path: str | None
    niche: str | None
    category_source: str
    price: float | None
    currency: str
    unit: str
    unit_cost: float | None
    features: list
    add_ons: list
    source: dict | None
    is_demo_data: bool
    created_at: datetime


class ProductIn(BaseModel):
    name: str | None = Field(None, max_length=160)
    stage: Literal["existing", "new"] = "existing"
    description: str | None = Field(None, max_length=600)
    url: str | None = Field(None, max_length=500)
    price: float | None = Field(None, ge=0)
    unit: Unit = "one_time"
    features: list[str] = Field(default_factory=list, max_length=30)
    add_ons: list[str] = Field(default_factory=list, max_length=30)


class ProductPatch(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=160)
    stage: Literal["existing", "new"] | None = None
    description: str | None = Field(None, max_length=600)
    price: float | None = Field(None, ge=0)
    unit: Unit | None = None
    unit_cost: float | None = Field(None, ge=0)
    features: list[str] | None = Field(None, max_length=30)
    add_ons: list[str] | None = Field(None, max_length=30)
    taxonomy_id: int | None = None
    niche: str | None = Field(None, max_length=60)


def _own(conn: Connection, profile_id: UUID, user_id: UUID) -> dict:
    row = conn.execute(text("select name, card from profiles where id = :p and user_id = :u"), {"p": profile_id, "u": user_id}).mappings().first()
    if not row:
        raise HTTPException(404, {"code": "not_found", "message": "Business not found."})
    return dict(row)


def _business(profile: dict) -> str:
    card = profile["card"] or {}
    v = lambda k: card_value(card, k) or ""
    return " ".join(str(x) for x in (v("business_type"), v("industry"), v("category"), v("description")) if x)


def insert_product(conn: Connection, profile_id, profile: dict, body: ProductIn, is_demo: bool = False, cat: dict | None = None) -> dict:
    """Shared by the endpoint, onboarding and the demo builder: read the page if given, classify, insert."""
    name, description, price, source = body.name, body.description, body.price, None
    if body.url:
        page = fetch(body.url)
        if page["status"] == "blocked_robots":
            raise HTTPException(422, {"code": "blocked_robots", "message": "That site's robots.txt doesn't allow reading this page. Enter the product by hand."})
        found = product_from_html(page["html"]) if page["status"] == "ok" else None
        if found:
            name = name or found["name"]
            description = description or found["description"]
            price = price if price is not None else (found["price"] if found["currency"] in (None, "INR") else None)
            source = {"url": body.url, "observed_at": datetime.now(UTC).isoformat(), "brand": found["brand"],
                      "rating": found["rating"], "review_count": found["review_count"], "currency": found["currency"]}
    if not name:
        raise HTTPException(422, {"code": "no_name", "message": "We couldn't find a product on that page. Add the name by hand."})
    cat = cat or classify(name, description or "", _business(profile))
    return dict(conn.execute(text(f"""
        insert into products (profile_id, name, stage, description, url, taxonomy_id, category_path, niche, category_source,
                              price, unit, features, add_ons, source, is_demo_data)
        values (:p, :n, :s, :d, :url, :t, :path, :niche, :cs, :price, :unit, cast(:f as jsonb), cast(:a as jsonb), cast(:src as jsonb), :demo)
        returning {COLS}
    """), {"p": profile_id, "n": name[:160], "s": body.stage, "d": description, "url": body.url, "t": cat["taxonomy_id"],
           "path": cat["path"], "niche": cat["niche"], "cs": cat["source"], "price": price, "unit": body.unit,
           "f": json.dumps(body.features), "a": json.dumps(body.add_ons), "src": json.dumps(source) if source else None,
           "demo": is_demo}).mappings().one())


@router.get("/profiles/{profile_id}/products")
def list_products(profile_id: UUID, user: UserDep, conn: ConnDep) -> list[Product]:
    _own(conn, profile_id, user.id)
    rows = conn.execute(text(f"select {COLS} from products where profile_id = :p order by stage, created_at"), {"p": profile_id}).mappings()
    return [Product(**r) for r in rows]


@router.post("/profiles/{profile_id}/products", status_code=201)
def create_product(profile_id: UUID, body: ProductIn, user: UserDep, conn: ConnDep) -> Product:
    profile = _own(conn, profile_id, user.id)
    if not (body.name or body.url):
        raise HTTPException(422, {"code": "no_name", "message": "Give the product a name or paste its page link."})
    return Product(**insert_product(conn, profile_id, profile, body))


def _owned_product(conn: Connection, product_id: UUID, user_id: UUID) -> dict:
    row = conn.execute(text(f"""
        select {', '.join('pr.' + c.strip() for c in COLS.split(','))} from products pr join profiles p on p.id = pr.profile_id
        where pr.id = :id and p.user_id = :u
    """), {"id": product_id, "u": user_id}).mappings().first()
    if not row:
        raise HTTPException(404, {"code": "not_found", "message": "Product not found."})
    return dict(row)


@router.get("/products/{product_id}")
def get_product(product_id: UUID, user: UserDep, conn: ConnDep) -> Product:
    return Product(**_owned_product(conn, product_id, user.id))


@router.patch("/products/{product_id}")
def update_product(product_id: UUID, body: ProductPatch, user: UserDep, conn: ConnDep) -> Product:
    _owned_product(conn, product_id, user.id)
    changes = body.model_dump(exclude_unset=True)
    if "taxonomy_id" in changes:
        path = path_of(changes["taxonomy_id"]) if changes["taxonomy_id"] is not None else None
        if changes["taxonomy_id"] is not None and not path:
            raise HTTPException(422, {"code": "bad_category", "message": "Unknown category."})
        changes |= {"category_path": path, "category_source": "user"}
        if path is None:
            changes.setdefault("niche", None)  # the niche named a type inside the old category
    for k in ("features", "add_ons"):
        if k in changes:
            changes[k] = json.dumps(changes[k])
    if changes:
        sets = ", ".join(f"{k} = cast(:{k} as jsonb)" if k in ("features", "add_ons") else f"{k} = :{k}" for k in changes)
        conn.execute(text(f"update products set {sets} where id = :id"), changes | {"id": product_id})
    return Product(**_owned_product(conn, product_id, user.id))


@router.delete("/products/{product_id}", status_code=204)
def delete_product(product_id: UUID, user: UserDep, conn: ConnDep) -> None:
    _owned_product(conn, product_id, user.id)
    conn.execute(text("delete from products where id = :id"), {"id": product_id})


@router.get("/taxonomy")
def search_taxonomy(q: str) -> list[dict]:
    return candidates(q, 15)


def add_from_onboarding(profile_id) -> None:
    """After onboarding: one product row per 'main product' the user listed, each classified.

    Runs on its own thread: FastAPI background tasks run before the request's transaction commits,
    and an exception there would roll the new business back.
    """
    threading.Thread(target=_add_from_onboarding, args=(profile_id,), daemon=True).start()


def _add_from_onboarding(profile_id) -> None:
    from app.db import engine
    for _ in range(40):  # wait for the request's transaction to commit
        with engine.connect() as conn:
            if conn.execute(text("select 1 from profiles where id = :p"), {"p": profile_id}).first():
                break
        time.sleep(0.5)
    with engine.connect() as conn:
        profile = dict(conn.execute(text("select name, kind, card from profiles where id = :p"), {"p": profile_id}).mappings().one())
    names = [str(n)[:160] for n in (card_value(profile["card"], "main_products") or [])][:10]
    stage = "new" if profile["kind"] == "idea" else "existing"
    for name, cat in zip(names, classify_many(names, _business(profile))):
        try:
            with engine.begin() as conn:  # one commit per product, so the page fills in as they land
                insert_product(conn, profile_id, profile, ProductIn(name=name, stage=stage), cat=cat)
        except Exception:
            log.exception("onboarding product %r failed", name)


# ---- B14d: like-for-like comparison inside the product's exact category (S-23) ----

@router.post("/products/{product_id}/comparables/find", status_code=202)
def find_comparable_products(product_id: UUID, user: UserDep, conn: ConnDep, background: BackgroundTasks) -> dict:
    p = _owned_product(conn, product_id, user.id)
    if not p["taxonomy_id"]:
        raise HTTPException(409, {"code": "no_category", "message": "Set the product's category first."})
    job_id = jobs.create(user.id, p["profile_id"], "comparables", {"product_id": str(product_id)})
    background.add_task(jobs.run, job_id, lambda job: find_comparables(job, product_id))  # own connections; never touches this request's rows
    return {"job_id": job_id, "status": "queued"}


class ComparableIn(BaseModel):
    url: str = Field(max_length=500)


@router.post("/products/{product_id}/comparables", status_code=201)
def add_comparable(product_id: UUID, body: ComparableIn, user: UserDep, conn: ConnDep) -> dict:
    """A founder pastes a rival's product page: read its JSON-LD; it joins the comparison only if it's in the same category."""
    p = _owned_product(conn, product_id, user.id)
    page = fetch(body.url)
    if page["status"] == "blocked_robots":
        raise HTTPException(422, {"code": "blocked_robots", "message": "That site's robots.txt doesn't allow reading this page."})
    found = product_from_html(page["html"]) if page["status"] == "ok" else None
    if not found or not found["name"]:
        raise HTTPException(422, {"code": "no_product", "message": "We couldn't find product details on that page (it may need JavaScript)."})
    cat = classify(found["name"], (found["description"] or "")[:150], hint(p))
    conn.execute(text("""
        insert into market_products (url, domain, taxonomy_id, category_path, niche, name, brand, description, price, currency, rating, review_count, observed_at)
        values (:url, :d, :t, :path, :niche, :name, :brand, :desc, :price, :cur, :rating, :rc, now())
        on conflict (url) do update set taxonomy_id = excluded.taxonomy_id, category_path = excluded.category_path, niche = excluded.niche,
          name = excluded.name, price = excluded.price, rating = excluded.rating, review_count = excluded.review_count, observed_at = now()
    """), {"url": body.url, "d": registrable_domain(body.url), "t": cat["taxonomy_id"], "path": cat["path"], "niche": cat["niche"],
           "name": found["name"][:200], "brand": found["brand"], "desc": (found["description"] or "")[:600],
           "price": found["price"] if found["currency"] in (None, "INR") else None, "cur": found["currency"],
           "rating": found["rating"], "rc": found["review_count"]})
    same = in_category(cat["path"], p["category_path"])
    return {"name": found["name"], "category_path": cat["path"], "same_category": same,
            "message": "Added to the comparison." if same else f"Not compared: it's in {cat['path']}, not {p['category_path']}."}


@router.get("/products/{product_id}/comparison")
def product_comparison(product_id: UUID, user: UserDep, conn: ConnDep) -> dict:
    return comparison_data(conn, _owned_product(conn, product_id, user.id))


def comparison_data(conn: Connection, p: dict) -> dict:
    """Shared with the product simulator (B14i)."""
    rows = [dict(r) for r in conn.execute(text("""
        select distinct on (domain, lower(name)) url, domain, name, brand, niche, price, currency, rating, review_count, features, observed_at
        from market_products where (taxonomy_id = :t or category_path like :sub) and url is distinct from :own
        order by domain, lower(name), observed_at desc
    """), {"t": p["taxonomy_id"], "sub": f"{p['category_path']} > %", "own": p["url"]}).mappings()]
    leaf = (p["category_path"] or "").split(" > ")[-1]
    for r in rows:
        r["price"] = float(r["price"]) if r["price"] is not None else None  # numeric, not Decimal strings, in JSON
        r["rating"] = float(r["rating"]) if r["rating"] is not None else None
        r["same_niche"] = niche_overlap(p["niche"], f"{r['niche']} {r['name']}", leaf)
    screen_prices([r for r in rows if r["same_niche"]])  # invalid prices and outliers stay listed, with the reason, but don't count
    niche_rows = [r for r in rows if r["same_niche"] and not r.get("excluded")]
    basis = niche_rows if sum(r["price"] is not None for r in niche_rows) >= 3 else rows
    # Only like-for-like prices make a median: a French press is in "Coffee" but says nothing about the price of coffee powder (L-23)
    prices = [float(r["price"]) for r in basis if r["price"] is not None] if basis is niche_rows else []
    pos = price_position(float(p["price"]) if p["price"] is not None else None, prices)
    premium = sorted((r for r in basis if r["price"] is not None and pos["q75"] and r["price"] >= pos["q75"]), key=lambda r: -r["price"])[:5]
    brands: dict[str, dict] = {}
    for r in rows:  # each brand's range in this category: its "additional products"
        b = brands.setdefault(r["brand"] or r["domain"], {"brand": r["brand"] or r["domain"], "products": 0, "min": None, "max": None})
        b["products"] += 1
        if r["price"] is not None:
            b["min"] = min(x for x in (b["min"], float(r["price"])) if x is not None)
            b["max"] = max(x for x in (b["max"], float(r["price"])) if x is not None)
    from app.modules.money.router import facts_for  # B14f: each brand's reported revenue, cited
    revenue = {}
    for f in facts_for(conn, [b["brand"] for b in brands.values()]):
        if f["kind"] == "revenue":
            revenue.setdefault(f["company"].lower(), f)
    for b in brands.values():
        b["revenue"] = revenue.get(b["brand"].lower())
    rows.sort(key=lambda r: (not r["same_niche"], r["price"] is None, r["price"] or 0))
    return {"product": Product(**p).model_dump(mode="json"), "basis": "niche" if basis is niche_rows else "category",
            "position": pos, "rows": rows, "premium": premium, "brands": sorted(brands.values(), key=lambda b: -b["products"])}


# ---- B14h: market news and funding, and category prices now ----

@router.get("/profiles/{profile_id}/market")
def market_overview(profile_id: UUID, user: UserDep, conn: ConnDep) -> dict:
    _own(conn, profile_id, user.id)
    news = conn.execute(text("select items, queries, fetched_at from market_news where profile_id = :p"), {"p": profile_id}).mappings().first()
    cats = []  # like-for-like prices only, the same basis as the product page (L-23)
    for p in conn.execute(text(f"select {COLS} from products where profile_id = :p order by created_at"), {"p": profile_id}).mappings():
        c = comparison_data(conn, dict(p)) if p["taxonomy_id"] else {"position": {"n": 0, "median": None, "min": None, "max": None}, "rows": []}
        pos, seen = c["position"], max((r["observed_at"] for r in c["rows"] if r["same_niche"]), default=None)
        cats.append({"category_path": p["category_path"], "niche": p["niche"], "product": p["name"], "product_id": p["id"], "n": pos["n"],
                     "median": pos["median"], "min": pos["min"], "max": pos["max"], "seen": seen.isoformat() if seen and pos["n"] else None})
    return {"news": news["items"] if news else [], "queries": news["queries"] if news else [],
            "news_fetched_at": news["fetched_at"].isoformat() if news else None, "categories": cats}


@router.post("/profiles/{profile_id}/market/news")
def refresh_news(profile_id: UUID, user: UserDep, conn: ConnDep) -> dict:
    profile = _own(conn, profile_id, user.id)
    queries = queries_for(conn, profile_id, profile["card"] or {})
    if not queries:
        raise HTTPException(409, {"code": "no_market", "message": "Add a product first, so we know which market to follow."})
    items = fetch_news(queries)
    conn.execute(text("""insert into market_news (profile_id, queries, items) values (:p, cast(:q as jsonb), cast(:i as jsonb))
        on conflict (profile_id) do update set queries = excluded.queries, items = excluded.items, fetched_at = now()"""),
                 {"p": profile_id, "q": json.dumps(queries), "i": json.dumps(items)})
    return {"items": len(items)}

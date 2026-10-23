"""B14c products: existing and new products of a business, each in an exact category (UC-16, S-22)."""
import json
from datetime import UTC, datetime
from typing import Literal
from uuid import UUID

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import Connection, text

from app.auth import UserDep
from app.db import ConnDep
from app.modules.collector.service import fetch
from app.modules.products.classify import classify
from app.modules.products.pages import product_from_html
from app.modules.products.taxonomy import candidates, path_of

router = APIRouter(prefix="/api/v1", tags=["products"])
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
    v = lambda k: (card.get(k) or {}).get("value") or ""
    return " ".join(str(x) for x in (v("business_type"), v("industry"), v("category"), v("description")) if x)


def insert_product(conn: Connection, profile_id, profile: dict, body: ProductIn, is_demo: bool = False) -> dict:
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
    cat = classify(name, description or "", _business(profile))
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
    """Background task after onboarding: one product row per 'main product' the user listed, each classified."""
    import time
    from app.db import engine
    for _ in range(10):  # the request's transaction may still be committing
        with engine.connect() as conn:
            if conn.execute(text("select 1 from profiles where id = :p"), {"p": profile_id}).first():
                break
        time.sleep(0.5)
    with engine.begin() as conn:
        profile = dict(conn.execute(text("select name, kind, card from profiles where id = :p"), {"p": profile_id}).mappings().one())
        names = (profile["card"].get("main_products") or {}).get("value") or []
        stage = "new" if profile["kind"] == "idea" else "existing"
        for name in names[:10]:
            insert_product(conn, profile_id, profile, ProductIn(name=str(name)[:160], stage=stage))

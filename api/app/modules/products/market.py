"""B14d: real comparable products for one product, from Indian brand stores' public product pages (schema.org JSON-LD).

Find: Tavily (niche) + the business's competitors → brand domains → product links on each homepage → JSON-LD per page
→ batch-classify → keep only the product's exact taxonomy category. Stored in market_products (shared public data).
"""
import json
import re
import statistics
from datetime import UTC, datetime
from urllib.parse import urljoin, urlsplit

from pydantic import BaseModel, Field
from sqlalchemy import text

from app.db import engine
from app.jobs import Job
from app.llm.gateway import LLMUnavailable, complete_json
from app.modules.collector.service import fetch, fetch_json
from app.modules.discovery.pipeline import _tavily
from app.modules.discovery.service import blocked, registrable_domain
from app.modules.products.classify import classify_many
from app.modules.products.pages import product_from_html
from app.modules.products.taxonomy import tokens

MARKETPLACES = re.compile(r"(^|\.)(myntra|ajio|tatacliq|nykaa|meesho|snapdeal|jiomart|shopclues|paytmmall|pinterest|bewakoof)\.(com|in)$")
# Product page URL shapes: Shopify /products/x, /product/x, Puma /pd/x, Nike /p/x, Magento x-1234.html
LINK = re.compile(r'href="([^"?#]*?(?:/products?/|/pd/|/p/)[^"?#]+|[^"?#]*?/[a-z0-9-]*\d[a-z0-9-]*\.html)')
MAX_DOMAINS, LINKS_PER_DOMAIN, MAX_PAGES = 6, 5, 24


def price_position(yours: float | None, prices: list[float]) -> dict:
    """Your price against the category: median, range, upper quartile, % vs median and your rank (1 = cheapest)."""
    if not prices:
        return {"n": 0, "median": None, "min": None, "max": None, "q75": None, "pct_vs_median": None, "rank": None}
    s = sorted(prices)
    median = statistics.median(s)
    q75 = statistics.quantiles(s, n=4, method="inclusive")[2] if len(s) > 1 else s[0]
    return {"n": len(s), "median": median, "min": s[0], "max": s[-1], "q75": q75,
            "pct_vs_median": round((yours - median) / median * 100) if yours and median else None,
            "rank": sum(p < yours for p in s) + 1 if yours else None}


def in_category(path: str | None, parent: str | None) -> bool:
    """Same category, or a sub-category of it: 'Bakery > Pastries & Scones' counts as 'Bakery'."""
    return bool(path and parent and (path == parent or path.startswith(parent + " > ")))


def hint(p: dict) -> str:
    """Context for classifying a rival's page: what it's being compared with."""
    return f"Compared with {p['niche'] or p['name']} ({p['category_path']})"


def niche_overlap(a: str | None, b: str | None, leaf: str = "") -> bool:
    """Like-for-like: every word that sets our product type apart (beyond the category's own word) appears in theirs.
    One shared word is not enough: 'protein coffee powder' is not 'filter coffee powder' (L-25)."""
    generic = tokens(leaf)
    ours = tokens(a or "") - generic
    return bool(ours) and ours <= tokens(b or "") - generic


def product_links(base: str, html: str, niche_words: set[str], n: int) -> list[str]:
    site = registrable_domain(base)
    seen, hits, rest = set(), [], []
    for href in LINK.findall(html):
        url = urljoin(base, href.replace(" ", "-"))
        if registrable_domain(url) != site or url in seen:
            continue
        seen.add(url)
        (hits if tokens(url.rsplit("/", 1)[-1].replace("-", " ")) & niche_words else rest).append(url)
    return (hits + rest)[:n]


def catalogue_links(url: str, catalogue: dict, niche_words: set[str], n: int) -> list[str]:
    """Shopify's public /products.json: keep products whose title, type or tags name the niche, best match first (L-24).
    Roasters name blends ("Vienna Roast"), so URL words alone miss them and pick journals and French presses instead."""
    root = "{0.scheme}://{0.netloc}".format(urlsplit(url))
    scored = []
    for p in catalogue.get("products") or []:
        if not isinstance(p, dict) or not p.get("handle"):
            continue
        tags = p.get("tags") or []
        rest = tokens(" ".join([p.get("product_type") or "", *(tags if isinstance(tags, list) else [str(tags)])]))
        if score := 3 * len(tokens(p.get("title") or "") & niche_words) + len(rest & niche_words):  # the title says what it is
            scored.append((-score, len(scored), f"{root}/products/{p['handle']}"))
    return [u for *_, u in sorted(scored)][:n]


class Features(BaseModel):
    items: list[list[str]] = Field(description="For each numbered product, up to 5 short features stated in its description")


def _features(rows: list[dict]) -> list[list[str]]:
    try:
        out = complete_json("product_features", Features, {
            "instructions": "List up to 5 short features each product's description states (materials, comfort tech, warranty, size, use). "
                            "Only what the text says. One list per product, in order.",
            "products": "\n\n".join(f"{i}. {r['name']}: {(r['description'] or '')[:400]}" for i, r in enumerate(rows)),
        }, "product_features.v1")
        return (out.items + [[]] * len(rows))[: len(rows)]
    except LLMUnavailable:
        return [[] for _ in rows]


def find_comparables(job: Job, product_id) -> dict:
    with engine.connect() as conn:
        p = dict(conn.execute(text("""
            select pr.name, pr.niche, pr.taxonomy_id, pr.category_path, pr.url, pr.profile_id, p.card
            from products pr join profiles p on p.id = pr.profile_id where pr.id = :id"""), {"id": product_id}).mappings().one())
        rivals = [r[0] for r in conn.execute(text("select domain from competitors where profile_id = :p and selected"), {"p": p["profile_id"]})]
    niche = p["niche"] or p["name"]
    words = tokens(niche) - tokens((p["category_path"] or "").split(" > ")[-1]) or tokens(niche)

    job.step("search", "running", None, f"Searching for {niche.lower()} sold in India…")
    own = registrable_domain(p["url"]) if p["url"] else None
    pages, listings = [], []  # listings: (store, [listing urls to try in order])
    for d in rivals:  # the business's competitors: their niche listing (Shopify-style), else their homepage
        listings.append((d, [f"https://www.{d}/collections/{'-'.join(niche.lower().split())}", f"https://www.{d}/"]))
    for q in (f"{niche} buy online India price", f"best {niche} brands India"):
        for r in _tavily(q):
            url = r.get("url", "")
            d = registrable_domain(url)
            if blocked(url) or MARKETPLACES.search(d) or d == own:
                continue
            bare = url.split("?")[0].split("#")[0]
            if (m := LINK.match(f'href="{bare}')) and m.group(1) == bare:
                pages.append(url)
            elif urlsplit(url).path.strip("/"):  # a brand's listing page for the niche
                listings.append((d, [url]))
            else:
                listings.append((d, [f"https://www.{d}/collections/{'-'.join(niche.lower().split())}", url]))
    stores = list(dict.fromkeys(d for d, _ in listings))[:MAX_DOMAINS]

    job.step("stores", "running", len(stores), "Reading brand stores (robots.txt respected)…")
    for d in stores:
        cat_url = f"https://www.{d}/products.json?limit=250"
        if links := catalogue_links(cat_url, fetch_json(cat_url) or {}, words, LINKS_PER_DOMAIN):
            pages += links
            continue
        for url in next(urls for dd, urls in listings if dd == d):
            listing = fetch(url)
            links = product_links(url, listing["html"], words, LINKS_PER_DOMAIN) if listing["status"] == "ok" else []
            if links:
                pages += links
                break

    found = []
    for url in list(dict.fromkeys(pages))[:MAX_PAGES]:
        page = fetch(url)
        item = product_from_html(page["html"]) if page["status"] == "ok" else None
        if item and item["name"]:
            found.append(item | {"url": url})
    job.step("classify", "running", len(found), "Checking which are in the same category…")
    cats = classify_many([f"{f['name']}. {(f['description'] or '')[:150]}" for f in found], hint(p)) if found else []
    same = [f | {"cat": c} for f, c in zip(found, cats) if in_category(c["path"], p["category_path"])]
    for f, feats in zip(same, _features(same) if same else []):
        f["features"] = feats

    now = datetime.now(UTC)
    with engine.begin() as conn:
        for f in same:
            inr = f["price"] if f["currency"] in (None, "INR") else None
            conn.execute(text("""
                insert into market_products (url, domain, taxonomy_id, category_path, niche, name, brand, description, price, currency,
                                             rating, review_count, features, observed_at)
                values (:url, :d, :t, :path, :niche, :name, :brand, :desc, :price, :cur, :rating, :rc, cast(:feat as jsonb), :at)
                on conflict (url) do update set taxonomy_id = excluded.taxonomy_id, category_path = excluded.category_path,
                  niche = excluded.niche, name = excluded.name, price = excluded.price, currency = excluded.currency,
                  rating = excluded.rating, review_count = excluded.review_count, features = excluded.features, observed_at = excluded.observed_at
            """), {"url": f["url"], "d": registrable_domain(f["url"]), "t": f["cat"]["taxonomy_id"], "path": f["cat"]["path"],
                   "niche": f["cat"]["niche"], "name": f["name"][:200], "brand": f["brand"], "desc": (f["description"] or "")[:600],
                   "price": inr, "cur": f["currency"], "rating": f["rating"], "rc": f["review_count"],
                   "feat": json.dumps(f.get("features") or []), "at": now})
    return {"product_id": str(product_id), "stores": stores, "pages_read": len(found), "same_category": len(same),
            "unclassified": sum(c["source"] != "ai" for c in cats)}  # the AI couldn't place these: shown, never counted

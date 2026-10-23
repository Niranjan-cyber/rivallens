"""Read a product from its public page: schema.org Product JSON-LD (what shops publish for search engines)."""
import html as html_lib
import json

from selectolax.lexbor import LexborHTMLParser


def _num(v) -> float | None:
    try:
        return float(str(v).replace(",", ""))
    except (TypeError, ValueError):
        return None


def _products(node):
    if isinstance(node, list):
        for x in node:
            yield from _products(x)
    elif isinstance(node, dict):
        t = node.get("@type")
        if t == "Product" or (isinstance(t, list) and "Product" in t):
            yield node
        for key in ("@graph", "itemListElement", "item", "mainEntity"):
            if key in node:
                yield from _products(node[key])


def product_from_html(html: str) -> dict | None:
    for script in LexborHTMLParser(html).css('script[type="application/ld+json"]'):
        try:
            data = json.loads(script.text(strip=True) or "null")
        except json.JSONDecodeError:
            continue
        for p in _products(data):
            offers = p.get("offers") or {}
            if isinstance(offers, list):
                offers = offers[0] if offers else {}
            brand = p.get("brand")
            rating = p.get("aggregateRating") or {}
            count = rating.get("reviewCount") or rating.get("ratingCount")
            return {
                "name": html_lib.unescape(p["name"]) if p.get("name") else None,
                "brand": brand.get("name") if isinstance(brand, dict) else brand,
                "description": html_lib.unescape(p["description"])[:600] if p.get("description") else None,
                "price": _num(offers.get("price") or offers.get("lowPrice")),
                "currency": offers.get("priceCurrency"),
                "rating": _num(rating.get("ratingValue")),
                "review_count": int(_num(count)) if _num(count) is not None else None,
            }
    return None

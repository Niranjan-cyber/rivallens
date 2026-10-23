"""B14g Customers (UC-18): what customers say, from the business's own exports and pages, plus public web mentions.

Every theme the LLM proposes must cite mention ids that exist; a theme's size is the number of mentions it cites.
"""
import json
import re
from datetime import UTC, date, datetime

from pydantic import BaseModel, Field
from selectolax.lexbor import LexborHTMLParser

from app.llm.gateway import LLMUnavailable, complete_json
from app.modules.money.service import parse_amount, parse_date

HINTS = {
    "text": ("text", "review", "comment", "message", "feedback", "body", "content"),
    "rating": ("rating", "score", "stars", "star"),
    "date": ("date", "time", "postedon", "createdat", "posted", "timestamp"),
    "author": ("author", "username", "user", "profilename", "name", "customer"),
    "title": ("summary", "title", "headline", "subject"),
    "url": ("url", "link", "permalink"),
    "product": ("product", "productid", "sku", "item"),
}


def suggest_review_mapping(headers: list[str]) -> dict:
    norm = {h: re.sub(r"[^a-z]", "", h.lower()) for h in headers}
    out: dict[str, str] = {}
    for field, words in HINTS.items():
        for w in words:
            exact = next((h for h in headers if norm[h] == w and h not in out.values()), None)
            col = exact or next((h for h in headers if w in norm[h] and h not in out.values() and not norm[h].endswith("id") or
                                 (field == "product" and w in norm[h] and h not in out.values())), None)
            if col:
                out[field] = col
                break
    return out


def _date(v) -> date | None:
    s = str(v or "").strip()
    if s.isdigit() and len(s) >= 9:  # unix seconds (Amazon review exports)
        return datetime.fromtimestamp(int(s), UTC).date()
    try:
        return parse_date(v)
    except ValueError:
        return None


def mentions_from_rows(rows: list[dict], mapping: dict, source: str) -> list[dict]:
    g = lambda r, f: r.get(mapping[f]) if f in mapping else None
    out = []
    for r in rows:
        body = str(g(r, "text") or "").strip()
        if not body:
            continue
        title = str(g(r, "title") or "").strip()
        rating = parse_amount(g(r, "rating"))
        out.append({"text": (f"{title}. {body}" if title and title.lower() not in body.lower() else body)[:2000],
                    "rating": rating if rating is not None and 0 <= rating <= 5 else None, "date": _date(g(r, "date")),
                    "author": str(g(r, "author") or "").strip()[:80] or None, "url": str(g(r, "url") or "").strip() or None,
                    "product": str(g(r, "product") or "").strip()[:160] or None, "source": source, "source_type": "upload"})
    return out


def _reviews(node):
    if isinstance(node, list):
        for x in node:
            yield from _reviews(x)
    elif isinstance(node, dict):
        if node.get("@type") == "Review":
            yield node
        for k in ("review", "reviews", "@graph"):
            if k in node:
                yield from _reviews(node[k])


def reviews_from_html(html: str) -> list[dict]:
    out = []
    for script in LexborHTMLParser(html).css('script[type="application/ld+json"]'):
        try:
            data = json.loads(script.text(strip=True) or "null")
        except json.JSONDecodeError:
            continue
        for r in _reviews(data):
            body = (r.get("reviewBody") or r.get("description") or "").strip()
            if not body:
                continue
            author = r.get("author")
            rating = (r.get("reviewRating") or {}).get("ratingValue")
            out.append({"text": body[:2000], "rating": parse_amount(rating), "author": author.get("name") if isinstance(author, dict) else author,
                        "date": _date(r.get("datePublished"))})
    return out


class Theme(BaseModel):
    label: str = Field(description="Short theme in the customers' terms, e.g. 'Wider sizes', 'Sole wears out fast'")
    kind: str = Field(description="request (something customers ask for) | complaint | praise")
    mention_ids: list[int] = Field(description="Ids of the mentions that say this")


class Analysis(BaseModel):
    sentiment: list[str] = Field(description="One of positive | neutral | negative per mention, in id order")
    themes: list[Theme]


def checked_themes(themes: list[dict], n_mentions: int) -> list[dict]:
    out = []
    for t in themes:
        ids = sorted({i for i in t["mention_ids"] if 0 <= i < n_mentions})
        if ids and t["kind"] in ("request", "complaint", "praise"):
            out.append({"label": t["label"][:80], "kind": t["kind"], "mention_ids": ids, "count": len(ids)})
    return sorted(out, key=lambda t: -t["count"])


def analyse(mentions: list[dict], business: str) -> dict:
    """mentions: [{id, text, rating}] (≤ 80). Returns {sentiment: {id: label}, themes: [...]}; rating-only fallback without the LLM."""
    rated = {m["id"]: ("positive" if m["rating"] >= 4 else "negative" if m["rating"] <= 2 else "neutral") for m in mentions if m.get("rating") is not None}
    try:
        out = complete_json("customer_themes", Analysis, {
            "instructions": "For each numbered customer mention give its sentiment. Then list up to 8 themes: what customers ask for "
                            "(request), complain about (complaint) or praise (praise), each citing the ids of the mentions that say it. "
                            "Only themes stated by at least one mention.",
            "business": business,
            "mentions": "\n".join(f"[{i}] {(m['text'] or '')[:300]}" for i, m in enumerate(mentions)),
        }, "customer_themes.v1", max_input_chars=30000)
    except LLMUnavailable:
        return {"sentiment": rated, "themes": [], "ai": False}
    sentiment = {m["id"]: s for m, s in zip(mentions, out.sentiment) if s in ("positive", "neutral", "negative")}
    themes = checked_themes([t.model_dump() for t in out.themes], len(mentions))
    for t in themes:
        t["mention_ids"] = [mentions[i]["id"] for i in t["mention_ids"]]
    return {"sentiment": rated | sentiment, "themes": themes, "ai": True}

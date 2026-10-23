"""B14h: what's moving in the business's market: recent category news and funding, each with its link and date (Tavily news)."""
import re
from email.utils import parsedate_to_datetime
from urllib.parse import urlsplit

import httpx
from sqlalchemy import Connection, text

from app.modules.discovery.pipeline import TAVILY_KEY, card_value
from app.modules.products.taxonomy import tokens

GENERIC = {"india", "market", "startup", "funding", "indian", "brand", "raise", "raises"}

# Indian business and retail news, so founders see their own market rather than US shopping deals.
INDIA_NEWS = ["economictimes.indiatimes.com", "inc42.com", "entrackr.com", "yourstory.com", "livemint.com", "business-standard.com",
              "moneycontrol.com", "thehindubusinessline.com", "financialexpress.com", "vccircle.com", "fortuneindia.com",
              "indianretailer.com", "afaqs.com", "medianama.com", "techcrunch.com", "thehindu.com", "businesstoday.in"]
FUNDING = re.compile(r"\b(raises?|raised|funding|series [a-e]|seed round|pre-series|investment|valuation|ipo|acquires?|acquired)\b", re.I)


def _news(query: str) -> list[dict]:
    if not TAVILY_KEY:
        return []
    try:
        r = httpx.post("https://api.tavily.com/search", headers={"Authorization": f"Bearer {TAVILY_KEY}"}, timeout=20,
                       json={"query": query, "topic": "news", "days": 90, "search_depth": "basic", "max_results": 6, "include_domains": INDIA_NEWS})
        return r.json().get("results", []) if r.status_code == 200 else []
    except httpx.HTTPError:
        return []


def _iso(v: str | None) -> str:
    try:
        return parsedate_to_datetime(v).date().isoformat() if v else ""
    except (TypeError, ValueError):
        return (v or "")[:10]


def queries_for(conn: Connection, profile_id, card: dict) -> list[str]:
    niches = [r[0] for r in conn.execute(text("""select niche from products where profile_id = :p and niche is not null
        group by niche order by count(*) desc limit 2"""), {"p": profile_id})]
    industry = card_value(card, "industry") or card_value(card, "category") or card_value(card, "business_type") or ""
    focus = niches[0] if niches else industry
    return [f"{n} India market" for n in niches] + ([f"{focus} brand raises funding India"] if focus else [])


def fetch_news(queries: list[str]) -> list[dict]:
    items, seen = [], set()
    for q in queries[:4]:
        for r in _news(q):
            url = r.get("url", "")
            if not url or url in seen:
                continue
            seen.add(url)
            body = f"{r.get('title', '')} {r.get('content', '')}"
            if not (tokens(q) - GENERIC) & tokens(body):  # must be about this market, not startup news in general
                continue
            items.append({"title": r.get("title") or url, "url": url, "source": urlsplit(url).hostname.removeprefix("www.") if urlsplit(url).hostname else url,
                          "published": _iso(r.get("published_date")), "snippet": (r.get("content") or "")[:280],
                          "funding": bool(FUNDING.search(body)), "query": q})
    return sorted(items, key=lambda i: i["published"], reverse=True)[:15]

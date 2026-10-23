"""C-07 extractor, rules only (the LLM merge arrives in B07). Output is ObservationFields (specs §3)."""
import re

from app.modules.collector.service import is_pricing, lines, section_nodes

PRICE = re.compile(r"(₹|Rs\.?|INR|\$|USD)\s?(\d[\d,]*(?:\.\d+)?)\s*(?:/|per)?\s*(mo|month|yr|year|hr|hour|user|seat)?\b", re.I)
# Specs list credits/revenue/customers; "spend" and "million" come from the Railway and DigitalOcean fixtures.
NOT_A_PLAN_PRICE = re.compile(r"credit|revenue|customer|spend|million", re.I)
CURRENCY = {"₹": "INR", "rs": "INR", "rs.": "INR", "inr": "INR", "$": "USD", "usd": "USD"}
PERIOD = {"mo": "month", "month": "month", "yr": "year", "year": "year", "hr": "hour", "hour": "hour", "user": "user", "seat": "seat"}


def parse_price(line: str) -> dict | None:
    if NOT_A_PLAN_PRICE.search(line):
        return None
    m = PRICE.search(line)
    if not m:
        return None
    amount = float(m.group(2).replace(",", ""))
    if not 0 <= amount <= 1_000_000:
        return None
    return {"amount": amount, "currency": CURRENCY[m.group(1).lower()], "period": PERIOD.get((m.group(3) or "").lower()),
            "raw": m.group(0).strip()}


def _plans(node) -> list[dict]:
    # A plan card is a heading's parent that holds exactly one heading; its first price binds to that heading.
    plans = []
    for h in node.css("h2, h3, h4"):
        card = h.parent
        if card is None or len(card.css("h1, h2, h3, h4")) != 1:
            continue
        price = next((p for p in map(parse_price, lines(card)) if p), None)
        features = [li.text(strip=True) for li in card.css("li") if li.text(strip=True)]
        if price is None and not features:
            continue
        name = h.text(strip=True)
        plans.append({"name": name, "price": price or {"amount": None, "currency": None, "period": None, "raw": None},
                      "features": features, "method": "rules"})
    return plans


def extract(html: str, prev: dict | None = None, reuse_pricing: bool = False) -> dict:
    """reuse_pricing: every pricing section hash is unchanged since `prev`, so keep its plans (method=reused)."""
    parts = section_nodes(html)
    if reuse_pricing and prev:
        plans = [{**p, "method": "reused"} for p in prev["plans"]]
    else:
        plans = [p for _, _, node in parts if is_pricing(node) for p in _plans(node)]
    h1 = next((n.css_first("h1") for _, landmark, n in parts if landmark == "main" and n.css_first("h1")), None)
    headline = {"text": h1.text(strip=True), "method": "rules"} if h1 else None
    priced = [p for p in plans if p["price"]["amount"] is not None]
    status = "ok" if priced else ("partial" if plans or headline else "failed")
    return {"plans": plans, "headline": headline, "extraction_status": status}

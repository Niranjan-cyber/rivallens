"""B14f: competitors' reported revenue and funding (UC-17), each a quote from a linked source.

Tavily finds coverage (filings, results, funding news) → the LLM extracts facts with a verbatim quote → a rule keeps a fact
only if the quote is in that source's text and the amount in the quote matches. Anything else stays Unknown.
"""
import re
from datetime import UTC, datetime

from pydantic import BaseModel, Field
from sqlalchemy import text

from app.db import engine
from app.jobs import Job
from app.llm.gateway import LLMUnavailable, complete_json
from app.modules.discovery.pipeline import _tavily

USD_INR = 84
SOCIAL = re.compile(r"//(www\.)?(youtube|youtu\.be|instagram|facebook|x|twitter|reddit|quora|linkedin)\.", re.I)  # not citable sources
UNITS = {"crore": 1e7, "crores": 1e7, "cr": 1e7, "lakh": 1e5, "lac": 1e5, "lakhs": 1e5, "million": 1e6, "mn": 1e6, "m": 1e6, "billion": 1e9, "bn": 1e9, "b": 1e9}
AMOUNT = re.compile(r"(₹|rs\.?|inr|\$|usd)\s*([\d,]+(?:\.\d+)?)\s*(crores?|lakhs?|lac|million|mn|billion|bn|cr|m|b)(?=in\b|[^a-z]|$)", re.I)


def amount_inr(s: str) -> int | None:
    m = AMOUNT.search(s or "")
    if not m:
        return None
    cur, num, unit = m.group(1).lower(), float(m.group(2).replace(",", "")), UNITS[m.group(3).lower()]
    return round(num * unit * (USD_INR if cur in ("$", "usd") else 1))


def _norm(s: str) -> str:
    return re.sub(r"\s+", " ", s.replace("’", "'")).strip().lower()


def verified(fact: dict, source_text: str) -> bool:
    quote = fact.get("quote") or ""
    parsed = amount_inr(quote)
    return bool(quote) and _norm(quote) in _norm(source_text) and parsed is not None and abs(parsed - fact["amount_inr"]) <= 0.02 * parsed


class Fact(BaseModel):
    source: int = Field(description="Number of the source the quote comes from")
    kind: str = Field(description="revenue | profit | funding")
    amount_inr: int = Field(description="The amount in rupees (crore = 10,000,000; lakh = 100,000; USD × 84)")
    period: str | None = Field(None, description="The period exactly as the source states it: 'FY26' for a full year, 'Q3 FY26' for a quarter")
    round: str | None = Field(None, description="Funding round name, e.g. Series B")
    event_date: str | None = Field(None, description="YYYY-MM or YYYY-MM-DD if the source states it")
    quote: str = Field(description="Exact words from the source containing the amount, copied verbatim")


class Facts(BaseModel):
    facts: list[Fact]


def find_facts(company: str) -> list[dict]:
    sources = []
    for q in (f"{company} revenue from operations FY26 crore", f"{company} funding raised"):
        sources += [r for r in _tavily(q) if r.get("content") and not SOCIAL.search(r.get("url", ""))]
    sources = list({s["url"]: s for s in sources}.values())[:8]
    if not sources:
        return []
    try:
        out = complete_json("money_facts", Facts, {
            "instructions": f"Extract reported revenue, profit and funding rounds of {company} only (not of other companies). "
                            "Copy the quote word for word from the source. Skip anything not stated as a number.",
            "company": company,
            "sources": "\n\n".join(f"Source {i}: {s.get('title', '')}\n{s['content'][:1500]}" for i, s in enumerate(sources)),
        }, "money_facts.v1", max_input_chars=14000)
    except LLMUnavailable:
        return []
    keep = []
    for f in out.facts:
        if 0 <= f.source < len(sources) and f.kind in ("revenue", "profit", "funding") and verified(f.model_dump(), sources[f.source]["content"]):
            s = sources[f.source]
            keep.append(f.model_dump() | {"source_url": s["url"], "source_title": s.get("title")})
    return keep


def find_job(job: Job, profile_id, companies: list[str]) -> dict:
    found = 0
    for name in companies:
        job.step("search", "running", None, f"Looking for {name}'s reported revenue and funding…")
        facts = find_facts(name)
        now = datetime.now(UTC)
        with engine.begin() as conn:
            for f in facts:
                conn.execute(text("""
                    insert into money_facts (company, kind, amount_inr, period, round, event_date, quote, source_url, source_title, observed_at)
                    values (:company, :kind, :amount_inr, :period, :round, :event_date, :quote, :source_url, :source_title, :at)
                    on conflict (company, kind, source_url, amount_inr) do update set observed_at = excluded.observed_at
                """), f | {"company": name, "at": now})
        found += len(facts)
    return {"companies": len(companies), "facts": found}

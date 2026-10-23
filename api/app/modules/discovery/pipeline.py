"""C-05 discovery pipeline: LLM candidates + Tavily → verify (robots, 200, India) → rank → pricing page → classify → persist."""
import json
import logging
import os
from concurrent.futures import ThreadPoolExecutor
from typing import Literal
from uuid import UUID

import httpx
from pydantic import BaseModel, Field
from selectolax.lexbor import LexborHTMLParser
from sqlalchemy import text

from app.db import engine
from app.jobs import Job
from app.llm.gateway import LLMUnavailable, complete_json
from app.modules.collector.service import fetch, split_sections
from app.modules.discovery.service import blocked, india_signals, registrable_domain, similarity

log = logging.getLogger("discovery")
TAVILY_KEY = os.getenv("TAVILY_API_KEY", "").strip()
MIN_SIMILARITY = 0.05  # spec says 0.08; E2E Networks (a real Indian host) scores 0.059 on the fixtures (D-59)


class Candidate(BaseModel):
    name: str
    domain: str
    why: str | None = None


class Candidates(BaseModel):
    queries: list[str] = Field(default_factory=list, description="Up to 4 web search queries to find competitors serving India")
    candidates: list[Candidate] = Field(default_factory=list, description="Up to 10 real competitor companies with their website domain")


class Label(BaseModel):
    domain: str
    relation: Literal["comparable", "inspiration"]
    reason: str


class Labels(BaseModel):
    labels: list[Label] = Field(default_factory=list)


def card_value(card: dict, key: str):
    v = card.get(key)
    return v.get("value") if isinstance(v, dict) and "value" in v else v


def card_text(card: dict) -> str:
    parts = [card_value(card, k) for k in ("name", "category", "industry", "attributes", "problem", "target_customer", "planned_features", "note")]
    return " ".join(" ".join(p) if isinstance(p, list) else str(p) for p in parts if p)


def _tavily(query: str) -> list[dict]:
    if not TAVILY_KEY:
        return []
    try:
        r = httpx.post("https://api.tavily.com/search", headers={"Authorization": f"Bearer {TAVILY_KEY}"}, timeout=15,
                       json={"query": query, "search_depth": "basic", "max_results": 5})
        return r.json().get("results", []) if r.status_code == 200 else []
    except httpx.HTTPError:
        return []


def find_pricing_page(domain: str, homepage_html: str) -> tuple[str, str, str]:
    """(url, page_type, html): /pricing, /plans, then a pricing-looking link; the homepage if none."""
    for path in ("/pricing", "/plans"):
        if (page := fetch(f"https://{domain}{path}"))["status"] == "ok":
            return f"https://{domain}{path}", "pricing", page["html"]
    for a in LexborHTMLParser(homepage_html).css("a[href]")[:300]:
        href, label = a.attributes.get("href") or "", a.text(strip=True).lower()
        if any(w in href.lower() or w in label for w in ("pricing", "plans", "price")):
            url = href if href.startswith("http") else f"https://{domain}/{href.lstrip('/')}"
            if registrable_domain(url) == domain and (page := fetch(url))["status"] == "ok":
                return url, "pricing", page["html"]
    return f"https://{domain}/", "home", homepage_html


def verify(c: dict, ctext: str) -> dict:
    page = fetch(f"https://{c['domain']}/")
    out = {**c, "reasons": [], "signals": {"score": 0, "hits": []}, "similarity": 0.0, "page": None}
    if page["status"] == "blocked_robots":
        return {**out, "status": "rejected", "reasons": ["robots.txt disallows the homepage"]}
    if page["status"] != "ok":
        return {**out, "status": "rejected", "reasons": [f"homepage unreachable ({page['status'].replace('_', ' ')})"]}
    url, page_type, pricing_html = find_pricing_page(c["domain"], page["html"])
    body = split_sections(page["html"])[0] + ("\n" + split_sections(pricing_html)[0] if page_type == "pricing" else "")
    signals, sim = india_signals(body, url), similarity(ctext, body)
    reasons = [f"India signals: {', '.join(signals['hits'])}" if signals["score"] else "no India signals on the homepage",
               f"similarity {sim:.2f}" + ("" if sim >= MIN_SIMILARITY else " (too different from your card)")]
    ok = signals["score"] >= 1 and sim >= MIN_SIMILARITY
    return {**out, "status": "verified" if ok else "rejected", "reasons": reasons, "signals": signals, "similarity": sim, "page": (url, page_type)}


def discover(job: Job, profile_id: UUID) -> dict:
    with engine.begin() as conn:
        card = conn.execute(text("select card from profiles where id = :p"), {"p": profile_id}).scalar() or {}
        existing = {d for (d,) in conn.execute(text("select domain from competitors where profile_id = :p"), {"p": profile_id})}
    ctext = card_text(card)
    markets = card_value(card, "india_markets") or []
    own = registrable_domain(card_value(card, "website") or "") if card_value(card, "website") else None

    job.step("generate_candidates", "running", None, "Asking the AI for likely competitors")
    try:
        gen = complete_json("discovery_candidates", Candidates, {"card": ctext, "india_markets": ", ".join(markets) or "India",
                            "instruction": "Competitors that sell to customers in India. At least 6 of the 10 must be companies headquartered in "
                                           "India that price in rupees (₹), the rest global companies with Indian regions or INR pricing. "
                                           "Use each company's exact website domain. Queries should find Indian providers."},
                            "discovery_candidates.v3")
    except LLMUnavailable:
        gen = Candidates(queries=[f"{ctext[:80]} India"], candidates=[])
    job.step("generate_candidates", "done", len(gen.candidates), f"{len(gen.candidates)} suggested")

    pool = {registrable_domain(c.domain): {"name": c.name, "domain": registrable_domain(c.domain), "origin": "ai_suggested"}
            for c in gen.candidates[:10] if c.domain}
    category = card_value(card, "category") or ctext[:60]
    queries = [f"{category} India pricing ₹ per month", *gen.queries][:3]
    if TAVILY_KEY:
        found = 0
        for q in queries:
            for r in _tavily(q):
                d = registrable_domain(r.get("url", ""))
                if d and not blocked(r["url"]) and d not in pool:
                    pool[d] = {"name": d.split(".")[0].replace("-", " ").title(), "domain": d, "origin": "ai_suggested"}
                    found += 1
        job.step("search", "done", found, f"{found} more from {len(queries)} web searches")
    else:
        job.step("search", "skipped", 0, "Web search unavailable; using AI suggestions only")

    cands = [c for d, c in pool.items() if d != own and d not in existing and not blocked(f"https://{d}")][:12]
    job.step("verify", "running", len(cands), "Checking robots.txt, reachability and India signals")
    with ThreadPoolExecutor(8) as ex:
        checked = list(ex.map(lambda c: verify(c, ctext), cands))
    ok = sorted([c for c in checked if c["status"] == "verified"], key=lambda c: -c["similarity"])
    job.step("verify", "done", len(ok), f"{len(ok)} of {len(checked)} passed")
    job.step("rank", "done", len(ok), "Ranked by similarity to your card")

    pages = [c["page"] for c in ok]
    job.step("find_pages", "done", sum(p[1] == "pricing" for p in pages), "Pricing pages found")

    relation = {}
    if ok:
        try:
            labels = complete_json("classify_competitors", Labels, {"card": ctext, "competitors": json.dumps(
                [{"name": c["name"], "domain": c["domain"]} for c in ok]),
                "instruction": "comparable = sells a similar offering to similar customers; inspiration = adjacent or much larger."},
                "classify_competitors.v1")
            relation = {registrable_domain(lab.domain): (lab.relation, lab.reason) for lab in labels.labels}
        except LLMUnavailable:
            pass
    job.step("classify", "done", len(ok), "Comparable vs inspiration")

    with engine.begin() as conn:
        for c in checked:
            conn.execute(text("""
                insert into discovery_candidates (profile_id, job_id, name, domain, origin, status, reasons, india_signals, similarity)
                values (:p, :j, :n, :d, :o, :s, :r, cast(:i as jsonb), :sim)
            """), {"p": profile_id, "j": job.id, "n": c["name"], "d": c["domain"], "o": c["origin"], "s": c["status"],
                   "r": c["reasons"] + ([relation[c["domain"]][1]] if c["domain"] in relation else []),
                   "i": json.dumps(c["signals"]), "sim": c["similarity"]})
        for c, (url, page_type) in zip(ok, pages):
            cid = conn.execute(text("""
                insert into competitors (profile_id, name, domain, relation, origin, selected, india_signals, similarity)
                values (:p, :n, :d, :r, 'ai_suggested', true, cast(:i as jsonb), :sim) on conflict (profile_id, domain) do nothing returning id
            """), {"p": profile_id, "n": c["name"], "d": c["domain"], "r": relation.get(c["domain"], ("comparable", ""))[0],
                   "i": json.dumps(c["signals"]), "sim": c["similarity"]}).scalar()
            if cid:
                conn.execute(text("insert into sources (competitor_id, url, page_type) values (:c, :u, :t) on conflict do nothing"),
                             {"c": cid, "u": url, "t": page_type})
    return {"verified": len(ok), "rejected": len(checked) - len(ok)}

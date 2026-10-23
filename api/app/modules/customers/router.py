"""B14g Customers dashboard (UC-18, S-26): uploads, own product pages, web mentions → sentiment and themes, each cited."""
import json
import re
from typing import Annotated, Literal
from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, File, Form, HTTPException, UploadFile
from sqlalchemy import Connection, text

from app import jobs
from app.auth import UserDep
from app.modules.discovery.pipeline import card_value
from app.db import ConnDep, engine
from app.jobs import Job
from app.modules.collector.service import fetch
from app.modules.customers.service import analyse, mentions_from_rows, reviews_from_html, suggest_review_mapping
from app.modules.discovery.pipeline import _tavily
from app.modules.money.router import _read
from app.modules.money.service import parse_amount, parse_date

router = APIRouter(prefix="/api/v1", tags=["customers"])
SOCIAL = re.compile(r"//(www\.)?(youtube|youtu\.be|instagram|facebook|x|twitter|linkedin)\.", re.I)
ANALYSE_LIMIT = 80


def _own(conn: Connection, profile_id: UUID, user_id: UUID) -> dict:
    row = conn.execute(text("select name, card, is_demo_data from profiles where id = :p and user_id = :u"), {"p": profile_id, "u": user_id}).mappings().first()
    if not row:
        raise HTTPException(404, {"code": "not_found", "message": "Business not found."})
    return dict(row)


def _business(p: dict) -> str:
    v = lambda k: str(card_value(p["card"] or {}, k) or "")
    return f"{p['name']}: {v('business_type')} {v('description')}".strip()


def _metric_columns(headers: list[str], rows: list[dict]) -> list[str]:
    """Insight exports: numeric columns (reach, followers, likes…) next to a date column."""
    return [h for h in headers if rows and sum(parse_amount(r.get(h)) is not None for r in rows[:20]) >= min(len(rows), 20) * 0.8
            and not re.search(r"date|time|id$", h, re.I)]


@router.post("/profiles/{profile_id}/customers/preview")
async def preview(profile_id: UUID, user: UserDep, conn: ConnDep, file: Annotated[UploadFile, File()]) -> dict:
    _own(conn, profile_id, user.id)
    headers, rows = await _read(file)
    mapping = suggest_review_mapping(headers)
    kind = "reviews" if "text" in mapping else "metrics"
    return {"filename": file.filename, "headers": headers, "rows": len(rows), "kind": kind, "mapping": mapping,
            "metrics": _metric_columns(headers, rows) if kind == "metrics" else [],
            "sample": mentions_from_rows(rows[:20], mapping, file.filename or "")[:4] if kind == "reviews" else []}


def _analyse_job(job: Job, profile_id: UUID, business: str) -> dict:
    job.step("analyse", "running", None, "Reading what customers say…")
    with engine.connect() as conn:
        rows = [dict(r) for r in conn.execute(text("""select id::text as id, text, rating::float as rating from customer_mentions
            where profile_id = :p order by date desc nulls last, created_at desc limit :n"""), {"p": profile_id, "n": ANALYSE_LIMIT}).mappings()]
    result = analyse(rows, business) if rows else {"sentiment": {}, "themes": [], "ai": False}
    with engine.begin() as conn:
        for mid, s in result["sentiment"].items():
            conn.execute(text("update customer_mentions set sentiment = :s where id = cast(:id as uuid)"), {"s": s, "id": mid})
        conn.execute(text("""insert into customer_insights (profile_id, themes, mention_count, ai) values (:p, cast(:t as jsonb), :n, :ai)
            on conflict (profile_id) do update set themes = excluded.themes, mention_count = excluded.mention_count, ai = excluded.ai, analysed_at = now()"""),
                     {"p": profile_id, "t": json.dumps(result["themes"]), "n": len(rows), "ai": result["ai"]})
    return {"mentions": len(rows), "themes": len(result["themes"])}


def _start_analysis(user_id, profile_id, business: str, background: BackgroundTasks) -> str:
    job_id = jobs.create(user_id, profile_id, "customer_themes")
    background.add_task(jobs.run, job_id, lambda job: _analyse_job(job, profile_id, business))
    return str(job_id)


@router.post("/profiles/{profile_id}/customers/import", status_code=201)
async def import_file(profile_id: UUID, user: UserDep, conn: ConnDep, background: BackgroundTasks, file: Annotated[UploadFile, File()],
                      mapping: Annotated[str, Form()], kind: Annotated[Literal["reviews", "metrics"], Form()]) -> dict:
    p = _own(conn, profile_id, user.id)
    headers, rows = await _read(file)
    name = file.filename or "upload"
    m = {k: v for k, v in json.loads(mapping).items() if v in headers}
    if kind == "reviews" and "text" not in m:
        raise HTTPException(422, {"code": "mapping", "message": "Pick the column with the review or comment text."})
    date_col = m.get("date") or next((h for h in headers if re.search(r"date|day", h, re.I)), None)
    if kind == "metrics" and not date_col:
        raise HTTPException(422, {"code": "mapping", "message": "Insight exports need a date column."})
    with engine.begin() as tx:  # its own transaction: committed before the analysis job reads the rows
        tx.execute(text("delete from customer_mentions where profile_id = :p and source = :s"), {"p": profile_id, "s": name})
        tx.execute(text("delete from social_metrics where profile_id = :p and source = :s"), {"p": profile_id, "s": name})
        if kind == "reviews":
            found = mentions_from_rows(rows, m, name)
            if found:
                tx.execute(text("""insert into customer_mentions (profile_id, source_type, source, url, author, text, rating, date, product, is_demo_data)
                    values (:p, 'upload', :source, :url, :author, :text, :rating, :date, :product, :demo)"""),
                           [x | {"p": profile_id, "demo": p["is_demo_data"]} for x in found])
        else:
            found = [{"p": profile_id, "s": name, "d": d, "m": h, "v": v} for r in rows if (d := parse_date(r.get(date_col)))
                     for h in _metric_columns(headers, rows) if (v := parse_amount(r.get(h))) is not None]
            if found:
                tx.execute(text("insert into social_metrics (profile_id, source, date, metric, value) values (:p, :s, :d, :m, :v)"), found)
    job = _start_analysis(user.id, profile_id, _business(p), background) if kind == "reviews" else None
    return {"imported": len(found), "job_id": job}


def _collect_job(job: Job, profile_id: UUID, p: dict) -> dict:
    found = []
    with engine.connect() as conn:
        pages = [r[0] for r in conn.execute(text("select url from products where profile_id = :p and url is not null"), {"p": profile_id})]
    website = str(card_value(p["card"] or {}, "website") or "")
    job.step("own_site", "running", len(pages), "Reading reviews on your product pages (robots.txt respected)…")
    for url in pages[:10]:
        page = fetch(url)
        for r in reviews_from_html(page["html"]) if page["status"] == "ok" else []:
            found.append(r | {"source_type": "own_site", "source": url, "url": url, "product": None})
    job.step("web", "running", None, "Searching the web for mentions…")
    for q in (f'"{p["name"]}" reviews', f'"{p["name"]}" customers'):
        for r in _tavily(q):
            u = r.get("url", "")
            if SOCIAL.search(u) or (website and website.split("//")[-1].split("/")[0] in u) or p["name"].lower() not in (r.get("content") or "").lower():
                continue
            found.append({"text": f"{r.get('title', '')}. {r.get('content', '')}"[:1200], "rating": None, "author": None, "date": None,
                          "source_type": "web", "source": u, "url": u, "product": None})
    with engine.begin() as conn:
        conn.execute(text("delete from customer_mentions where profile_id = :p and source_type in ('own_site', 'web')"), {"p": profile_id})
        if found:
            conn.execute(text("""insert into customer_mentions (profile_id, source_type, source, url, author, text, rating, date, product, is_demo_data)
                values (:p, :source_type, :source, :url, :author, :text, :rating, :date, :product, :demo)"""),
                         [x | {"p": profile_id, "demo": p["is_demo_data"]} for x in found])
    out = _analyse_job(job, profile_id, _business(p))
    return {"own_site": sum(f["source_type"] == "own_site" for f in found), "web": sum(f["source_type"] == "web" for f in found)} | out


@router.post("/profiles/{profile_id}/customers/collect", status_code=202)
def collect(profile_id: UUID, user: UserDep, conn: ConnDep, background: BackgroundTasks) -> dict:
    p = _own(conn, profile_id, user.id)
    job_id = jobs.create(user.id, profile_id, "customers_collect")
    background.add_task(jobs.run, job_id, lambda job: _collect_job(job, profile_id, p))
    return {"job_id": job_id, "status": "queued"}


@router.delete("/profiles/{profile_id}/customers/sources/{source:path}", status_code=204)
def delete_source(profile_id: UUID, source: str, user: UserDep, conn: ConnDep) -> None:
    _own(conn, profile_id, user.id)
    conn.execute(text("delete from customer_mentions where profile_id = :p and source = :s"), {"p": profile_id, "s": source})
    conn.execute(text("delete from social_metrics where profile_id = :p and source = :s"), {"p": profile_id, "s": source})


def customer_summary(conn: Connection, profile_id: UUID) -> dict:
    """Shared with the overview and the simulator (B14i)."""
    split = {r[0] or "unrated": r[1] for r in conn.execute(text(
        "select sentiment, count(*) from customer_mentions where profile_id = :p group by sentiment"), {"p": profile_id})}
    ins = conn.execute(text("select themes, mention_count, ai, analysed_at from customer_insights where profile_id = :p"), {"p": profile_id}).mappings().first()
    rating = conn.execute(text("select avg(rating)::float, count(rating) from customer_mentions where profile_id = :p"), {"p": profile_id}).one()
    return {"total": sum(split.values()), "sentiment": split, "avg_rating": round(rating[0], 2) if rating[0] else None, "rated": rating[1],
            "themes": ins["themes"] if ins else [], "analysed": ins["mention_count"] if ins else 0, "ai": ins["ai"] if ins else None,
            "analysed_at": ins["analysed_at"].isoformat() if ins else None}


@router.get("/profiles/{profile_id}/customers")
def get_customers(profile_id: UUID, user: UserDep, conn: ConnDep) -> dict:
    _own(conn, profile_id, user.id)
    out = customer_summary(conn, profile_id)
    ids = list({i for t in out["themes"] for i in t["mention_ids"][:3]})
    quotes = {r["id"]: dict(r) | {"date": r["date"].isoformat() if r["date"] else None} for r in conn.execute(text("""
        select id::text as id, text, rating::float as rating, date, author, url, source, source_type, sentiment from customer_mentions
        where id = any(cast(:ids as uuid[]))"""), {"ids": ids}).mappings()} if ids else {}
    for t in out["themes"]:
        t["quotes"] = [quotes[i] for i in t["mention_ids"][:3] if i in quotes]
    out["sources"] = [dict(r) for r in conn.execute(text("""select source, source_type, count(*) as rows from customer_mentions
        where profile_id = :p group by source, source_type order by count(*) desc"""), {"p": profile_id}).mappings()]
    out["recent"] = [dict(r) | {"date": r["date"].isoformat() if r["date"] else None} for r in conn.execute(text("""
        select text, rating::float as rating, date, author, url, source, source_type, sentiment from customer_mentions
        where profile_id = :p order by date desc nulls last, created_at desc limit 20"""), {"p": profile_id}).mappings()]
    out["metrics"] = [dict(r) | {"first_date": r["first_date"].isoformat(), "last_date": r["last_date"].isoformat()} for r in conn.execute(text("""
        select metric, source, (array_agg(value::float order by date))[1] as first, (array_agg(value::float order by date desc))[1] as last,
               min(date) as first_date, max(date) as last_date, count(*) as points
        from social_metrics where profile_id = :p group by metric, source order by source, metric"""), {"p": profile_id}).mappings()]
    return out

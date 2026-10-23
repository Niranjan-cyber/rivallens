import json
from typing import Literal
from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, HTTPException
from pydantic import BaseModel
from sqlalchemy import Connection, text

from app import jobs
from app.auth import UserDep
from app.config import MOCK_BASE_URL
from app.db import ConnDep, engine
from app.modules.changes.router import JobAccepted, create_run
from app.modules.collector.service import fetch, split_sections
from app.modules.discovery.pipeline import card_text, discover
from app.modules.discovery.service import india_signals, registrable_domain, similarity

router = APIRouter(prefix="/api/v1", tags=["discovery"])
GUEST_PER_DAY, GLOBAL_PER_DAY = 2, 20
MOCK_NAMES = {"nimbusdeploy": "NimbusDeploy (demo)", "kitehost": "KiteHost (demo)", "orbitly": "Orbitly Cloud (demo)"}


class CandidateOut(BaseModel):
    id: UUID
    name: str
    domain: str
    origin: str
    status: str
    reasons: list[str]
    india_signals: dict
    similarity: float | None


class Source(BaseModel):
    id: UUID
    url: str
    page_type: str


class Competitor(BaseModel):
    id: UUID
    name: str
    domain: str
    relation: str
    origin: str
    selected: bool
    monitorable: bool
    india_signals: dict
    similarity: float | None
    is_demo_data: bool
    sources: list[Source]


class AddCompetitor(BaseModel):
    url: str


class CompetitorPatch(BaseModel):
    selected: bool | None = None
    relation: Literal["comparable", "inspiration"] | None = None


def _own(conn: Connection, profile_id: UUID, user_id: UUID) -> dict:
    row = conn.execute(text("select id, card from profiles where id = :p and user_id = :u"), {"p": profile_id, "u": user_id}).mappings().first()
    if row is None:
        raise HTTPException(404, {"code": "not_found", "message": "Profile not found."})
    return dict(row)


def _bump(conn: Connection, scope: str) -> int:
    return conn.execute(text("""insert into usage_counters (scope, kind, count) values (:s, 'discovery', 1)
        on conflict (scope, day, kind) do update set count = usage_counters.count + 1 returning count"""), {"s": scope}).scalar()


@router.post("/profiles/{profile_id}/discovery", status_code=202)
def start_discovery(profile_id: UUID, user: UserDep, background: BackgroundTasks) -> JobAccepted:
    with engine.begin() as conn:
        _own(conn, profile_id, user.id)
        if user.is_anonymous and _bump(conn, f"user:{user.id}") > GUEST_PER_DAY:
            raise HTTPException(429, {"code": "discovery_limit", "message": f"Demo accounts can run discovery {GUEST_PER_DAY} times a day. "
                                      "The StackNest demo already has its competitors; log in with email for more."})
        if _bump(conn, "global") > GLOBAL_PER_DAY:
            raise HTTPException(429, {"code": "discovery_limit", "message": "Today's discovery budget is used up. Add competitors by URL instead."})
    job_id = jobs.create(user.id, profile_id, "discovery")
    background.add_task(jobs.run, job_id, lambda job: discover(job, profile_id))
    return JobAccepted(job_id=job_id, status="queued")


@router.get("/profiles/{profile_id}/discovery-candidates")
def list_candidates(profile_id: UUID, user: UserDep, conn: ConnDep) -> list[CandidateOut]:
    _own(conn, profile_id, user.id)
    rows = conn.execute(text("""
        select id, name, domain, origin, status, reasons, india_signals, similarity from discovery_candidates
        where job_id = (select job_id from discovery_candidates where profile_id = :p order by created_at desc limit 1)
        order by status desc, similarity desc nulls last
    """), {"p": profile_id}).mappings()
    return [CandidateOut(**r) for r in rows]


def _competitors(conn: Connection, profile_id: UUID, competitor_id: UUID | None = None) -> list[Competitor]:
    rows = conn.execute(text("""
        select c.id, c.name, c.domain, c.relation, c.origin, c.selected, c.monitorable, c.india_signals, c.similarity, c.is_demo_data,
               coalesce(json_agg(json_build_object('id', s.id, 'url', s.url, 'page_type', s.page_type)) filter (where s.id is not null), '[]') as sources
        from competitors c left join sources s on s.competitor_id = c.id
        where c.profile_id = :p and (cast(:c as uuid) is null or c.id = :c)
        group by c.id order by c.selected desc, c.similarity desc nulls last, c.created_at
    """), {"p": profile_id, "c": competitor_id}).mappings()
    return [Competitor(**r) for r in rows]


@router.get("/profiles/{profile_id}/competitors")
def list_competitors(profile_id: UUID, user: UserDep, conn: ConnDep) -> list[Competitor]:
    _own(conn, profile_id, user.id)
    return _competitors(conn, profile_id)


@router.post("/profiles/{profile_id}/competitors", status_code=201)
def add_competitor(profile_id: UUID, body: AddCompetitor, user: UserDep, conn: ConnDep) -> Competitor:
    profile = _own(conn, profile_id, user.id)
    url = body.url.strip()
    if not url.startswith(("http://", "https://")):
        raise HTTPException(422, {"code": "invalid_url", "message": "Paste a full web address starting with https://"})
    is_mock = url.startswith(f"{MOCK_BASE_URL}/")
    slug = url.rstrip("/").rsplit("/", 1)[-1]
    domain = f"{slug}.demo" if is_mock else registrable_domain(url)
    if conn.execute(text("select 1 from competitors where profile_id = :p and domain = :d"), {"p": profile_id, "d": domain}).first():
        raise HTTPException(409, {"code": "duplicate", "message": "That competitor is already on your list."})
    page = fetch(url)
    if page["status"] == "blocked_robots":
        raise HTTPException(422, {"code": "blocked_robots", "message": "That site's robots.txt doesn't allow monitoring this page."})
    if page["status"] != "ok":
        raise HTTPException(422, {"code": "unreachable", "message": "We couldn't open that page. Check the address and try again."})
    body_text = split_sections(page["html"])[0]
    name = MOCK_NAMES.get(slug, slug) if is_mock else domain.split(".")[0].title()
    cid = conn.execute(text("""
        insert into competitors (profile_id, name, domain, relation, origin, selected, india_signals, similarity, is_demo_data)
        values (:p, :n, :d, 'comparable', 'added_by_user', true, cast(:i as jsonb), :s, :demo) returning id
    """), {"p": profile_id, "n": name, "d": domain, "i": json.dumps(india_signals(body_text, url)),
           "s": similarity(card_text(profile["card"] or {}), body_text), "demo": is_mock}).scalar()
    conn.execute(text("insert into sources (competitor_id, url, page_type, is_mock) values (:c, :u, 'pricing', :m)"), {"c": cid, "u": url, "m": is_mock})
    return _competitors(conn, profile_id, cid)[0]


@router.patch("/competitors/{competitor_id}")
def patch_competitor(competitor_id: UUID, body: CompetitorPatch, user: UserDep, conn: ConnDep) -> Competitor:
    profile_id = conn.execute(text("select c.profile_id from competitors c join profiles p on p.id = c.profile_id where c.id = :c and p.user_id = :u"),
                              {"c": competitor_id, "u": user.id}).scalar()
    if profile_id is None:
        raise HTTPException(404, {"code": "not_found", "message": "Competitor not found."})
    conn.execute(text("update competitors set selected = coalesce(:s, selected), relation = coalesce(:r, relation) where id = :c"),
                 {"s": body.selected, "r": body.relation, "c": competitor_id})
    return _competitors(conn, profile_id, competitor_id)[0]


@router.post("/profiles/{profile_id}/monitoring/start", status_code=202)
def start_monitoring(profile_id: UUID, user: UserDep, background: BackgroundTasks) -> JobAccepted:
    return create_run(profile_id, user, background)  # first run over the selected sources is the baseline

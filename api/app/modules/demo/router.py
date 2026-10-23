import secrets

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from sqlalchemy import Connection, text

from app.auth import UserDep
from app.config import MOCK_BASE_URL, SEED_USER_EMAIL
from app.db import ConnDep
from app.modules.demo.history import DEMO_HISTORY, seed_history
from app.modules.discovery.router import MOCK_NAMES
from app.modules.profiles.router import ProfileSummary, list_profiles

router = APIRouter(tags=["demo"])

MOCK_SLUGS = ("nimbusdeploy", "kitehost", "orbitly")


def _seed_user_id(conn: Connection):
    uid = conn.execute(text("select id from auth.users where email = :e"), {"e": SEED_USER_EMAIL}).scalar()
    if uid is None:
        raise HTTPException(500, {"code": "seed_missing", "message": "Demo data isn't loaded yet."})
    return uid


@router.post("/api/v1/demo/guest-clone", status_code=201)
def guest_clone(user: UserDep, conn: ConnDep) -> dict[str, list[ProfileSummary]]:
    if not user.is_anonymous:
        raise HTTPException(403, {"code": "not_anonymous", "message": "Only demo accounts can load the demo data."})
    if conn.execute(text("select 1 from profiles where user_id = :u limit 1"), {"u": user.id}).first():
        raise HTTPException(409, {"code": "already_cloned", "message": "Demo data is already loaded."})

    seed = _seed_user_id(conn)
    keys = {slug: secrets.token_urlsafe(8) for slug in MOCK_SLUGS}
    for slug, key in keys.items():
        conn.execute(text("insert into mock_instances (user_id, instance_key, slug) values (:u, :k, :s)"), {"u": user.id, "k": key, "s": slug})

    # Deep-copy profiles → competitors → sources with fresh ids; mock source URLs point at this guest's own instances.
    conn.execute(text("create temp table _p on commit drop as select id as old_id, gen_random_uuid() as new_id from profiles where user_id = :seed"), {"seed": seed})
    conn.execute(text("""
        insert into profiles (id, user_id, name, kind, offering_type, card, is_demo_data, created_at)
        select m.new_id, :u, p.name, p.kind, p.offering_type, p.card, p.is_demo_data, p.created_at from profiles p join _p m on m.old_id = p.id
    """), {"u": user.id})
    # Profiles with generated demo history get fresh history below instead of a copy (same story, guest-owned rows).
    conn.execute(text("""create temp table _c on commit drop as select c.id as old_id, gen_random_uuid() as new_id, m.new_id as profile_id
        from competitors c join _p m on m.old_id = c.profile_id join profiles p on p.id = c.profile_id where not (p.name = any(:generated))"""),
        {"generated": list(DEMO_HISTORY)})
    conn.execute(text("""
        insert into competitors (id, profile_id, name, domain, relation, origin, selected, monitorable, india_signals, similarity, is_demo_data)
        select m.new_id, m.profile_id, c.name, c.domain, c.relation, c.origin, c.selected, c.monitorable, c.india_signals, c.similarity, c.is_demo_data
        from competitors c join _c m on m.old_id = c.id
    """))
    sources = conn.execute(text("select s.id, s.url, s.page_type, s.is_mock, m.new_id as competitor_id from sources s join _c m on m.old_id = s.competitor_id")).mappings().all()
    for s in sources:
        url = s["url"]
        if s["is_mock"]:
            slug = url.rstrip("/").rsplit("/", 1)[-1]
            url = f"{MOCK_BASE_URL}/{keys[slug]}/{slug}"
        new_id = conn.execute(text("insert into sources (competitor_id, url, page_type, is_mock) values (:c, :url, :t, :m) returning id"),
                              {"c": s["competitor_id"], "url": url, "t": s["page_type"], "m": s["is_mock"]}).scalar()
        # The seed's latest snapshot becomes this guest's baseline (same immutable storage object, specs §1 C-13).
        conn.execute(text("""
            with old as (select * from snapshots where source_id = :old and status = 'ok' order by observed_at desc limit 1),
            snap as (
                insert into snapshots (source_id, observed_at, status, http_status, storage_path, sha256, text, sections, bytes)
                select :new, observed_at, status, http_status, storage_path, sha256, text, sections, bytes from old returning id, observed_at
            )
            insert into observations (snapshot_id, source_id, observed_at, fields, origin)
            select snap.id, :new, snap.observed_at, o.fields, 'seed' from snap, old join observations o on o.snapshot_id = old.id
        """), {"old": s["id"], "new": new_id})
    for pid, name in conn.execute(text("select p.id, p.name from profiles p join _p m on m.new_id = p.id")).all():
        seed_history(conn, pid, name)
    return {"profiles": list_profiles(user, conn)}


SCENARIOS = ("price_cut_40", "add_feature", "positioning", "cosmetic")


class Mock(BaseModel):
    slug: str
    name: str
    version: list[str]
    url: str


class Mocks(BaseModel):
    mocks: list[Mock]


class ScenarioIn(BaseModel):
    scenario: str


class ScenarioOut(BaseModel):
    slug: str
    version: list[str]


@router.get("/api/v1/demo/mocks")
def list_mocks(user: UserDep, conn: ConnDep) -> Mocks:
    rows = conn.execute(text("select slug, instance_key, version from mock_instances where user_id = :u order by slug"), {"u": user.id}).mappings()
    return Mocks(mocks=[Mock(slug=r["slug"], name=MOCK_NAMES.get(r["slug"], r["slug"]), version=r["version"],
                             url=f"{MOCK_BASE_URL}/{r['instance_key']}/{r['slug']}") for r in rows])


@router.post("/api/v1/demo/mocks/{slug}/scenario")
def apply_scenario(slug: str, body: ScenarioIn, user: UserDep, conn: ConnDep) -> ScenarioOut:
    if body.scenario not in SCENARIOS:
        raise HTTPException(422, {"code": "bad_scenario", "message": f"Scenario must be one of {', '.join(SCENARIOS)}."})
    version = conn.execute(text("""
        update mock_instances set version = case when :sc = any(version) then version else array_append(version, :sc) end
        where user_id = :u and slug = :s returning version
    """), {"sc": body.scenario, "u": user.id, "s": slug}).scalar()
    if version is None:
        raise HTTPException(404, {"code": "mock_not_found", "message": "Unknown demo page."})
    return ScenarioOut(slug=slug, version=version)


@router.post("/api/v1/demo/mocks/reset")
def reset_mocks(user: UserDep, conn: ConnDep) -> dict[str, int]:
    n = conn.execute(text("update mock_instances set version = '{v1}', overrides = '{}' where user_id = :u"), {"u": user.id}).rowcount
    return {"reset": n}

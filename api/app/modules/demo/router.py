from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from sqlalchemy import text

from app.auth import UserDep
from app.config import MOCK_BASE_URL
from app.db import ConnDep
from app.modules.discovery.router import MOCK_NAMES

router = APIRouter(tags=["demo"])

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

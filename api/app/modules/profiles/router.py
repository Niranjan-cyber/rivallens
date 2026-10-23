import json
from datetime import datetime
from typing import Literal
from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, HTTPException
from pydantic import BaseModel, Field, model_validator
from sqlalchemy import text

from app import jobs
from app.auth import UserDep
from app.db import ConnDep
from app.modules.discovery.pipeline import card_value
from app.modules.products.router import add_from_onboarding
from app.modules.profiles.drafting import draft_job

router = APIRouter(prefix="/api/v1/profiles", tags=["profiles"])


class ProfileSummary(BaseModel):
    id: UUID
    name: str
    kind: Literal["business", "idea"]
    offering_type: Literal["product", "service"]
    note: str
    competitors_monitored: int
    unread_alerts: int
    last_run_at: datetime | None
    is_demo_data: bool


@router.get("")
def list_profiles(user: UserDep, conn: ConnDep) -> list[ProfileSummary]:
    rows = conn.execute(
        text("""
            select p.id, p.name, p.kind, p.offering_type, coalesce(p.card->>'note', p.card->'category'->>'value', '') as note, p.is_demo_data,
                   (select count(*) from competitors c where c.profile_id = p.id and c.selected) as competitors_monitored,
                   (select max(r.started_at) from runs r where r.profile_id = p.id) as last_run_at
            from profiles p where p.user_id = :uid order by p.created_at
        """),
        {"uid": user.id},
    ).mappings()
    return [ProfileSummary(**r, unread_alerts=0) for r in rows]


@router.delete("/{profile_id}", status_code=204)
def delete_profile(profile_id: UUID, user: UserDep, conn: ConnDep) -> None:
    # Ownership in the WHERE clause: someone else's id looks exactly like a missing one (404, not 403).
    if not conn.execute(text("delete from profiles where id = :id and user_id = :uid"), {"id": profile_id, "uid": user.id}).rowcount:
        raise HTTPException(404, {"code": "not_found", "message": "Profile not found."})


class DraftIn(BaseModel):
    kind: Literal["business", "idea"]
    url: str | None = Field(None, max_length=300)
    description: str | None = Field(None, max_length=500)

    @model_validator(mode="after")
    def one_input(self):
        if not (self.url or self.description):
            raise ValueError("Give a website or a one-line description.")
        return self


class ProfileIn(BaseModel):
    kind: Literal["business", "idea"]
    offering_type: Literal["product", "service"]
    name: str = Field(min_length=1, max_length=120)
    card: dict  # each leaf {value, origin: user | ai_drafted | public_source}


class CardPatch(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=120)
    offering_type: Literal["product", "service"] | None = None
    card: dict | None = None


class Profile(BaseModel):
    id: UUID
    name: str
    kind: str
    offering_type: str
    card: dict
    is_demo_data: bool
    created_at: datetime


@router.post("/draft", status_code=202)
def draft_profile(body: DraftIn, user: UserDep, background: BackgroundTasks) -> dict:
    job_id = jobs.create(user.id, None, "draft")
    background.add_task(jobs.run, job_id, lambda job: draft_job(job, body.kind, body.description, body.url))
    return {"job_id": job_id, "status": "queued"}


@router.post("", status_code=201)
def create_profile(body: ProfileIn, user: UserDep, conn: ConnDep) -> Profile:
    row = conn.execute(text("""
        insert into profiles (user_id, name, kind, offering_type, card) values (:u, :n, :k, :o, cast(:c as jsonb))
        returning id, name, kind, offering_type, card, is_demo_data, created_at
    """), {"u": user.id, "n": body.name, "k": body.kind, "o": body.offering_type, "c": json.dumps(body.card)}).mappings().one()
    conn.execute(text("insert into alert_rules (profile_id) values (:p) on conflict do nothing"), {"p": row["id"]})
    if card_value(body.card, "main_products"):
        add_from_onboarding(row["id"])  # its own thread; waits for this transaction to commit
    return Profile(**row)


@router.get("/{profile_id}")
def get_profile(profile_id: UUID, user: UserDep, conn: ConnDep) -> Profile:
    row = conn.execute(text("select id, name, kind, offering_type, card, is_demo_data, created_at from profiles where id = :id and user_id = :u"),
                       {"id": profile_id, "u": user.id}).mappings().first()
    if row is None:
        raise HTTPException(404, {"code": "not_found", "message": "Profile not found."})
    return Profile(**row)


@router.patch("/{profile_id}")
def patch_profile(profile_id: UUID, body: CardPatch, user: UserDep, conn: ConnDep) -> Profile:
    get_profile(profile_id, user, conn)
    conn.execute(text("""
        update profiles set name = coalesce(:n, name), offering_type = coalesce(:o, offering_type),
               card = coalesce(cast(:c as jsonb), card) where id = :id
    """), {"n": body.name, "o": body.offering_type, "c": json.dumps(body.card) if body.card is not None else None, "id": profile_id})
    return get_profile(profile_id, user, conn)

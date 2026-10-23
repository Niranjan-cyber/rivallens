from datetime import datetime
from typing import Literal
from uuid import UUID

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from sqlalchemy import text

from app.auth import UserDep
from app.db import ConnDep

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
            select p.id, p.name, p.kind, p.offering_type, coalesce(p.card->>'note', '') as note, p.is_demo_data,
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

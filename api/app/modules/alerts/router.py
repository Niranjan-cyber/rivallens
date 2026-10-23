import json
from datetime import datetime
from html import escape
from typing import Literal
from uuid import UUID
from zoneinfo import ZoneInfo

import httpx
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import Connection, text

from app.auth import UserDep
from app.config import ALERT_EMAIL_OVERRIDE, ALERT_FROM, RESEND_API_KEY, WEB_ORIGIN
from app.db import ConnDep
from app.modules.alerts.service import GROUP, alert_text, bucket, score

router = APIRouter(prefix="/api/v1", tags=["alerts"])
IST = ZoneInfo("Asia/Kolkata")
DEFAULT_TYPES = {"price": True, "feature": True, "plan": True, "positioning": True, "announcement": False}


def rules_for(conn: Connection, profile_id: UUID) -> dict:
    conn.execute(text("insert into alert_rules (profile_id) values (:p) on conflict (profile_id) do nothing"), {"p": profile_id})
    return dict(conn.execute(text("select change_types, min_priority, email_enabled, muted from alert_rules where profile_id = :p"),
                             {"p": profile_id}).mappings().one())


def _send_email(subject: str, html: str) -> str:
    if not (RESEND_API_KEY and ALERT_EMAIL_OVERRIDE):  # P1: only to the owner's inbox, never to a user's (or guest's) address
        return "skipped"
    try:
        r = httpx.post("https://api.resend.com/emails", headers={"Authorization": f"Bearer {RESEND_API_KEY}"}, timeout=15,
                       json={"from": ALERT_FROM, "to": [ALERT_EMAIL_OVERRIDE], "subject": subject, "html": html})
        return "sent" if r.status_code in (200, 201) else "failed"
    except httpx.HTTPError:
        return "failed"


def raise_alert(conn: Connection, ctx: dict, src: dict, event_id: UUID, change: dict, fingerprint: str,
                prev: str | None, curr: str | None, observed_at: datetime) -> None:
    """Score the change (always stored on the event), then alert unless it's suspicious, muted, filtered or a repeat."""
    priority, breakdown = score(change, src["relation"], ctx["planned_price"])
    conn.execute(text("update change_events set priority = :p, priority_breakdown = cast(:b as jsonb) where id = :id"),
                 {"p": priority, "b": json.dumps(breakdown), "id": event_id})
    rules = ctx["rules"]
    muted = any(m.get("competitor_id") == str(src["competitor_id"]) and m.get("field_path") in (change["field_path"], "*") for m in rules["muted"])
    enabled = {**DEFAULT_TYPES, **(rules["change_types"] or {})}.get(GROUP.get(change["change_type"], "announcement"), False)
    if change["status"] != "confirmed" or muted or not enabled or priority < rules["min_priority"]:
        return
    repeat = conn.execute(text("""
        update alerts a set seen_again = seen_again + 1 from change_events e
        where a.change_event_id = e.id and a.profile_id = :p and e.fingerprint = :f and e.id <> :id
          and a.created_at > now() - interval '30 days' returning a.id
    """), {"p": ctx["profile_id"], "f": fingerprint, "id": event_id}).first()
    if repeat:
        return
    undercut = f"₹{ctx['planned_price']:,.0f}" if breakdown["undercut"] else None
    body = alert_text(src["name"], change, prev, curr, observed_at.astimezone(IST).strftime("%d %b %Y"), undercut)
    level = bucket(priority)
    email = "not_sent"
    if level == "high" and rules["email_enabled"]:
        link = f"{WEB_ORIGIN}/app/{ctx['profile_id']}/receipt?id={event_id}"
        demo = '<p style="color:#696969">Demo data: fictional company.</p>' if src["is_demo_data"] else ""
        email = _send_email(f"[RivalLens] {src['name']}: {prev} → {curr}",
                            f'<p>{escape(body)}</p><p>Priority {priority} (high).</p><p><a href="{link}">Open the change receipt</a></p>{demo}')
    conn.execute(text("""
        insert into alerts (user_id, profile_id, change_event_id, bucket, priority, text, email_status)
        values (:u, :p, :e, :b, :pr, :t, :em)
    """), {"u": ctx["user_id"], "p": ctx["profile_id"], "e": event_id, "b": level, "pr": priority, "t": body, "em": email})


class Alert(BaseModel):
    id: UUID
    profile_id: UUID
    change_event_id: UUID
    bucket: str
    priority: int
    text: str
    observed_at: datetime
    read: bool
    seen_again: int
    email_status: str


class UnreadCount(BaseModel):
    count: int
    top: list[Alert]


class AlertPatch(BaseModel):
    read: bool | None = None
    mute: Literal["competitor", "type"] | None = None


class Rules(BaseModel):
    change_types: dict[str, bool]
    min_priority: int = Field(ge=0, le=100)
    email_enabled: bool


ALERT_SQL = """
    select a.id, a.profile_id, a.change_event_id, a.bucket, a.priority, a.text, e.observed_at, a.read, a.seen_again, a.email_status
    from alerts a join change_events e on e.id = a.change_event_id where a.user_id = :u
"""


@router.get("/alerts")
def list_alerts(user: UserDep, conn: ConnDep, profile_id: UUID | None = None, bucket: str | None = None,
                type: str | None = None, unread: bool | None = None) -> list[Alert]:
    sql = ALERT_SQL + """ and (cast(:p as uuid) is null or a.profile_id = :p) and (cast(:b as text) is null or a.bucket = :b)
        and (cast(:t as text) is null or e.change_type like :t || '%') and (cast(:r as boolean) is null or a.read = not :r)
        order by a.created_at desc limit 200"""
    rows = conn.execute(text(sql), {"u": user.id, "p": profile_id, "b": bucket, "t": type, "r": unread}).mappings()
    return [Alert(**r) for r in rows]


@router.get("/alerts/unread-count")
def unread_count(user: UserDep, conn: ConnDep) -> UnreadCount:
    count = conn.execute(text("select count(*) from alerts where user_id = :u and not read"), {"u": user.id}).scalar()
    top = conn.execute(text(ALERT_SQL + " and not a.read order by a.priority desc, a.created_at desc limit 5"), {"u": user.id}).mappings()
    return UnreadCount(count=count, top=[Alert(**r) for r in top])


@router.patch("/alerts/{alert_id}")
def patch_alert(alert_id: UUID, body: AlertPatch, user: UserDep, conn: ConnDep) -> Alert:
    row = conn.execute(text(ALERT_SQL + " and a.id = :id"), {"u": user.id, "id": alert_id}).mappings().first()
    if row is None:
        raise HTTPException(404, {"code": "not_found", "message": "Alert not found."})
    if body.read is not None:
        conn.execute(text("update alerts set read = :r where id = :id"), {"r": body.read, "id": alert_id})
    if body.mute:
        event = conn.execute(text("select competitor_id, change_type from change_events where id = :e"), {"e": row["change_event_id"]}).one()
        rules_for(conn, row["profile_id"])
        if body.mute == "competitor":
            conn.execute(text("update alert_rules set muted = muted || cast(:m as jsonb) where profile_id = :p"),
                         {"p": row["profile_id"], "m": json.dumps([{"competitor_id": str(event.competitor_id), "field_path": "*"}])})
        else:
            conn.execute(text("update alert_rules set change_types = change_types || cast(:t as jsonb) where profile_id = :p"),
                         {"p": row["profile_id"], "t": json.dumps({GROUP.get(event.change_type, "announcement"): False})})
    return Alert(**conn.execute(text(ALERT_SQL + " and a.id = :id"), {"u": user.id, "id": alert_id}).mappings().one())


def _own(conn: Connection, profile_id: UUID, user_id: UUID) -> None:
    if not conn.execute(text("select 1 from profiles where id = :p and user_id = :u"), {"p": profile_id, "u": user_id}).first():
        raise HTTPException(404, {"code": "not_found", "message": "Profile not found."})


@router.get("/profiles/{profile_id}/alert-rules")
def get_rules(profile_id: UUID, user: UserDep, conn: ConnDep) -> Rules:
    _own(conn, profile_id, user.id)
    r = rules_for(conn, profile_id)
    return Rules(change_types={**DEFAULT_TYPES, **(r["change_types"] or {})}, min_priority=r["min_priority"], email_enabled=r["email_enabled"])


@router.put("/profiles/{profile_id}/alert-rules")
def put_rules(profile_id: UUID, body: Rules, user: UserDep, conn: ConnDep) -> Rules:
    _own(conn, profile_id, user.id)
    rules_for(conn, profile_id)
    conn.execute(text("update alert_rules set change_types = cast(:t as jsonb), min_priority = :m, email_enabled = :e where profile_id = :p"),
                 {"t": json.dumps({**DEFAULT_TYPES, **body.change_types}), "m": body.min_priority, "e": body.email_enabled, "p": profile_id})
    return get_rules(profile_id, user, conn)

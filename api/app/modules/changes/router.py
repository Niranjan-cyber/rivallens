import json
from datetime import datetime
from typing import Literal
from uuid import UUID, uuid4

import httpx
from fastapi import APIRouter, BackgroundTasks, HTTPException
from pydantic import BaseModel
from sqlalchemy import text

from app import jobs
from app.auth import UserDep
from app.db import ConnDep, engine
from app.modules.alerts.service import bucket
from app.modules.changes.runs import monitor, show, start_run
from app.modules.collector.service import sign_snapshot

router = APIRouter(prefix="/api/v1", tags=["monitoring"])

RUNS_PER_DAY_ANON = 20


class JobAccepted(BaseModel):
    job_id: UUID
    status: Literal["queued"]


class Change(BaseModel):
    change_event_id: UUID
    competitor: str
    change_type: str
    field: str
    prev: str | None
    curr: str | None
    delta_pct: float | None
    status: str
    priority: int | None
    bucket: str | None


class LedgerEntry(BaseModel):
    source_id: UUID
    competitor: str
    section_key: str
    reason: str
    summary: str


class Failure(BaseModel):
    source_id: UUID
    status: str
    url: str


class Run(BaseModel):
    id: UUID
    profile_id: UUID
    status: str
    kind: str
    started_at: datetime
    finished_at: datetime | None
    counts: dict
    changes: list[Change]
    ledger: list[LedgerEntry]
    failures: list[Failure]


class RunSummary(BaseModel):
    id: UUID
    status: str
    kind: str
    started_at: datetime
    finished_at: datetime | None
    counts: dict


class JobStatus(BaseModel):
    id: UUID
    kind: str
    status: str
    steps: list[dict]
    result: dict | None
    error: dict | None


def _own_profile(conn, profile_id: UUID, user_id: UUID) -> None:
    if not conn.execute(text("select 1 from profiles where id = :p and user_id = :u"), {"p": profile_id, "u": user_id}).first():
        raise HTTPException(404, {"code": "not_found", "message": "Profile not found."})


@router.post("/profiles/{profile_id}/runs", status_code=202)
def create_run(profile_id: UUID, user: UserDep, background: BackgroundTasks) -> JobAccepted:
    # Own transaction (not ConnDep) so the rows are committed before the background task reads them.
    with engine.begin() as conn:
        _own_profile(conn, profile_id, user.id)
        if conn.execute(text("select 1 from runs where profile_id = :p and status = 'running' and started_at > now() - interval '10 minutes'"),
                        {"p": profile_id}).first():
            raise HTTPException(409, {"code": "run_in_progress", "message": "A check is already running for this profile."})
        if user.is_anonymous:
            used = conn.execute(text("""
                insert into usage_counters (scope, kind, count) values (:s, 'run', 1)
                on conflict (scope, day, kind) do update set count = usage_counters.count + 1 returning count
            """), {"s": f"user:{user.id}"}).scalar()
            if used > RUNS_PER_DAY_ANON:
                raise HTTPException(429, {"code": "run_limit", "message": f"Demo accounts can run {RUNS_PER_DAY_ANON} checks a day."})
    job_id = jobs.create(user.id, profile_id, "run")
    run_id = start_run(profile_id, job_id)
    background.add_task(jobs.run, job_id, lambda job: monitor(job, profile_id, run_id))
    return JobAccepted(job_id=job_id, status="queued")


DUE_SQL = """
    select p.id, p.user_id from profiles p
    where not p.is_demo_data
      and exists (select 1 from competitors c where c.profile_id = p.id and c.selected)
      and exists (select 1 from runs r where r.profile_id = p.id and r.kind = 'baseline' and r.status = 'done')
      and not exists (select 1 from runs r where r.profile_id = p.id and r.status = 'running' and r.started_at > now() - interval '10 minutes')
      and (select max(started_at) from runs r where r.profile_id = p.id) < now() - case
            when exists (select 1 from snapshots sn join runs r on r.id = sn.run_id where r.profile_id = p.id and sn.status <> 'ok'
                         and r.started_at = (select max(started_at) from runs where profile_id = p.id))
            then interval '1 day' else interval '7 days' end  -- a check with failed pages is retried the next day
    order by (select max(started_at) from runs r where r.profile_id = p.id) limit :n"""


@router.post("/cron/checks", status_code=202)
def scheduled_checks(background: BackgroundTasks) -> dict:
    """Workstream 5: weekly competitor checks for real businesses, called daily by a scheduler (.github/workflows/scheduled-checks.yml).
    No secret: it can only start checks that are already due (a week since the last, a day if pages failed), at most 3 a call."""
    with engine.begin() as conn:
        due = conn.execute(text(DUE_SQL), {"n": 3}).all()
    for profile_id, user_id in due:
        job_id = jobs.create(user_id, profile_id, "run")
        run_id = start_run(profile_id, job_id)
        background.add_task(jobs.run, job_id, lambda job, p=profile_id, r=run_id: monitor(job, p, r))
    return {"started": len(due)}


@router.get("/profiles/{profile_id}/runs")
def list_runs(profile_id: UUID, user: UserDep, conn: ConnDep, limit: int = 20) -> list[RunSummary]:
    _own_profile(conn, profile_id, user.id)
    rows = conn.execute(text("select id, status, kind, started_at, finished_at, counts from runs where profile_id = :p order by started_at desc limit :l"),
                        {"p": profile_id, "l": min(limit, 100)}).mappings()
    return [RunSummary(**r) for r in rows]


@router.get("/runs/{run_id}")
def get_run(run_id: UUID, user: UserDep, conn: ConnDep) -> Run:
    run = conn.execute(text("""
        select r.id, r.profile_id, r.status, r.kind, r.started_at, r.finished_at, r.counts
        from runs r join profiles p on p.id = r.profile_id where r.id = :r and p.user_id = :u
    """), {"r": run_id, "u": user.id}).mappings().first()
    if run is None:
        raise HTTPException(404, {"code": "not_found", "message": "Run not found."})
    changes = conn.execute(text("""
        select e.id, c.name, e.change_type, e.field_path, e.prev_value, e.curr_value, e.delta_pct, e.status, e.priority
        from change_events e join competitors c on c.id = e.competitor_id where e.run_id = :r order by e.delta_pct nulls last, e.created_at
    """), {"r": run_id}).mappings()
    ledger = conn.execute(text("""
        select l.source_id, c.name, l.section_key, l.reason, l.summary from ledger_entries l
        join sources s on s.id = l.source_id join competitors c on c.id = s.competitor_id where l.run_id = :r order by c.name, l.created_at
    """), {"r": run_id}).mappings()
    failures = conn.execute(text("""
        select sn.source_id, sn.status, s.url from snapshots sn join sources s on s.id = sn.source_id where sn.run_id = :r and sn.status <> 'ok'
    """), {"r": run_id}).mappings()
    return Run(
        **run,
        changes=[Change(change_event_id=c["id"], competitor=c["name"], change_type=c["change_type"], field=c["field_path"],
                        prev=show(c["prev_value"]), curr=show(c["curr_value"]), delta_pct=c["delta_pct"], status=c["status"],
                        priority=c["priority"], bucket=bucket(c["priority"]) if c["priority"] is not None else None) for c in changes],
        ledger=[LedgerEntry(source_id=e["source_id"], competitor=e["name"], section_key=e["section_key"], reason=e["reason"], summary=e["summary"])
                for e in ledger],
        failures=[Failure(**f) for f in failures],
    )


@router.get("/jobs/{job_id}")
def get_job(job_id: UUID, user: UserDep, conn: ConnDep) -> JobStatus:
    row = conn.execute(text("select id, kind, status, steps, result, error from jobs where id = :j and user_id = :u"),
                       {"j": job_id, "u": user.id}).mappings().first()
    if row is None:
        raise HTTPException(404, {"code": "not_found", "message": "Job not found."})
    return JobStatus(**row)


# ---- Receipts (S-11) --------------------------------------------------------------------------------------------
WINDOW = 600


class Named(BaseModel):
    id: UUID
    name: str


class Receipt(BaseModel):
    id: UUID
    profile_id: UUID
    competitor: Named
    source_url: str
    change_type: str
    field: str
    prev_value: dict | str | None
    curr_value: dict | str | None
    prev_display: str | None
    curr_display: str | None
    delta_pct: float | None
    status: str
    observed_at: datetime
    prev_observed_at: datetime | None
    published_at: datetime | None
    wayback_url: str | None
    is_demo_data: bool
    muted: bool
    priority: int | None
    priority_breakdown: dict | None
    simulation_impact: dict | None


class EvidenceSide(BaseModel):
    snapshot_id: UUID
    observed_at: datetime
    text_window: str
    highlight: dict | None


class Evidence(BaseModel):
    before: EvidenceSide | None
    after: EvidenceSide | None
    sha256: dict
    evidence_missing: bool


class SignedSnapshot(BaseModel):
    signed_url: str
    expires_in: int


class FeedbackIn(BaseModel):
    relevant: bool


def _receipt_row(conn, receipt_id: UUID, user_id: UUID):
    row = conn.execute(text("""
        select e.*, c.name as competitor_name, c.profile_id, s.url as source_url from change_events e
        join competitors c on c.id = e.competitor_id join profiles p on p.id = c.profile_id join sources s on s.id = e.source_id
        where e.id = :id and p.user_id = :u
    """), {"id": receipt_id, "u": user_id}).mappings().first()
    if row is None:
        raise HTTPException(404, {"code": "not_found", "message": "Receipt not found."})
    return row


def _impact(conn, receipt_id: UUID) -> dict | None:
    row = conn.execute(text("""
        select s.version, s.recommended_price_inr as after, p.recommended_price_inr as before, s.replan_summary as summary
        from simulations s left join simulations p on p.profile_id = s.profile_id and p.version = s.replanned_from_version
        where s.trigger_change_event_id = :id order by s.version desc limit 1
    """), {"id": receipt_id}).mappings().first()
    return dict(row) if row else None


@router.get("/receipts/{receipt_id}")
def get_receipt(receipt_id: UUID, user: UserDep, conn: ConnDep) -> Receipt:
    e = _receipt_row(conn, receipt_id, user.id)
    muted = conn.execute(text("""
        select exists (select 1 from alert_rules r, jsonb_array_elements(r.muted) m
                       where r.profile_id = :p and m->>'competitor_id' = :c and m->>'field_path' = :f)
    """), {"p": e["profile_id"], "c": str(e["competitor_id"]), "f": e["field_path"]}).scalar()
    return Receipt(
        id=e["id"], profile_id=e["profile_id"], competitor=Named(id=e["competitor_id"], name=e["competitor_name"]),
        source_url=e["source_url"], change_type=e["change_type"], field=e["field_path"],
        prev_value=e["prev_value"], curr_value=e["curr_value"], prev_display=show(e["prev_value"]), curr_display=show(e["curr_value"]),
        delta_pct=e["delta_pct"], status=e["status"], observed_at=e["observed_at"], prev_observed_at=e["prev_observed_at"],
        published_at=e["published_at"], wayback_url=e["wayback_url"], is_demo_data=e["is_demo_data"], muted=muted,
        priority=e["priority"], priority_breakdown=e["priority_breakdown"], simulation_impact=_impact(conn, receipt_id),
    )


def _side(conn, snapshot_id: UUID | None, span: dict | None) -> tuple[EvidenceSide | None, str | None]:
    snap = conn.execute(text("select id, observed_at, text, sha256 from snapshots where id = :id"), {"id": snapshot_id}).mappings().first() if snapshot_id else None
    if snap is None or snap["text"] is None:
        return None, None
    body = snap["text"]
    if span is None:  # nothing to highlight: show the top of the page
        return EvidenceSide(snapshot_id=snap["id"], observed_at=snap["observed_at"], text_window=body[: 2 * WINDOW], highlight=None), snap["sha256"]
    lo = max(span["start"] - WINDOW, 0)
    return EvidenceSide(snapshot_id=snap["id"], observed_at=snap["observed_at"], text_window=body[lo: span["end"] + WINDOW],
                        highlight={"start": span["start"] - lo, "end": span["end"] - lo}), snap["sha256"]


@router.get("/receipts/{receipt_id}/evidence")
def get_evidence(receipt_id: UUID, user: UserDep, conn: ConnDep) -> Evidence:
    e = _receipt_row(conn, receipt_id, user.id)
    excerpt = e["excerpt"] or {}
    before, sha_before = _side(conn, e["before_snapshot_id"], excerpt.get("before"))
    after, sha_after = _side(conn, e["after_snapshot_id"], excerpt.get("after"))
    return Evidence(before=before, after=after, sha256={"before": sha_before, "after": sha_after},
                    evidence_missing=before is None or after is None)


@router.get("/snapshots/{snapshot_id}/html")
def snapshot_html(snapshot_id: UUID, user: UserDep, conn: ConnDep) -> SignedSnapshot:
    path = conn.execute(text("""
        select sn.storage_path from snapshots sn join sources s on s.id = sn.source_id join competitors c on c.id = s.competitor_id
        join profiles p on p.id = c.profile_id where sn.id = :id and p.user_id = :u
    """), {"id": snapshot_id, "u": user.id}).scalar()
    if path is None:
        raise HTTPException(404, {"code": "not_found", "message": "Saved page not found."})
    try:
        url = sign_snapshot(path, 300)
    except httpx.HTTPError:
        raise HTTPException(502, {"code": "storage_unavailable", "message": "The saved page can't be opened right now. The text evidence above is unaffected."})
    return SignedSnapshot(signed_url=url, expires_in=300)


@router.post("/receipts/{receipt_id}/feedback")
def receipt_feedback(receipt_id: UUID, body: FeedbackIn, user: UserDep, conn: ConnDep) -> dict[str, UUID | None]:
    e = _receipt_row(conn, receipt_id, user.id)
    conn.execute(text("insert into alert_rules (profile_id) values (:p) on conflict (profile_id) do nothing"), {"p": e["profile_id"]})
    match = {"competitor_id": str(e["competitor_id"]), "field_path": e["field_path"]}
    # Drop any existing mute for this competitor + field, then add one back if the user says it's not relevant.
    conn.execute(text("""
        update alert_rules set muted = coalesce((select jsonb_agg(m) from jsonb_array_elements(muted) m
            where not (m->>'competitor_id' = :c and m->>'field_path' = :f)), '[]'::jsonb) where profile_id = :p
    """), {"p": e["profile_id"], "c": match["competitor_id"], "f": match["field_path"]})
    if body.relevant:
        return {"muted_rule_id": None}
    rule_id = uuid4()
    conn.execute(text("update alert_rules set muted = muted || cast(:m as jsonb) where profile_id = :p"),
                 {"p": e["profile_id"], "m": json.dumps([{**match, "id": str(rule_id), "change_event_id": str(receipt_id)}])})
    return {"muted_rule_id": rule_id}

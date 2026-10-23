from datetime import datetime
from typing import Literal
from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, HTTPException
from pydantic import BaseModel
from sqlalchemy import text

from app import jobs
from app.auth import UserDep
from app.db import ConnDep, engine
from app.modules.changes.runs import monitor, show, start_run

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
                        priority=c["priority"], bucket=None) for c in changes],
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

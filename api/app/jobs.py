"""Jobs (specs §1 C-03): a jobs row plus a FastAPI BackgroundTask. Each step write commits on its own."""
import json
import logging
from collections.abc import Callable
from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import text

from app.db import engine

log = logging.getLogger("jobs")


class Job:
    def __init__(self, job_id: UUID):
        self.id = job_id

    def _update(self, sql: str, **params) -> None:
        with engine.begin() as conn:
            conn.execute(text(f"update jobs set {sql}, heartbeat_at = now() where id = :id"), {"id": self.id, **params})

    def step(self, name: str, status: str, count: int | None = None, detail: str | None = None) -> None:
        entry = {"name": name, "status": status, "count": count, "detail": detail, "at": datetime.now(UTC).isoformat()}
        self._update("status = 'running', steps = steps || cast(:s as jsonb)", s=json.dumps([entry]))

    def finish(self, result: dict) -> None:
        self._update("status = 'done', result = cast(:r as jsonb)", r=json.dumps(result))

    def fail(self, code: str, message: str) -> None:
        self._update("status = 'failed', error = cast(:e as jsonb)", e=json.dumps({"code": code, "message": message}))


def create(user_id: UUID, profile_id: UUID | None, kind: str) -> UUID:
    with engine.begin() as conn:
        return conn.execute(text("insert into jobs (user_id, profile_id, kind) values (:u, :p, :k) returning id"),
                            {"u": user_id, "p": profile_id, "k": kind}).scalar()


def run(job_id: UUID, fn: Callable[[Job], dict]) -> None:
    """The BackgroundTask body: fn does the work and returns the job result."""
    job = Job(job_id)
    try:
        job.finish(fn(job))
    except Exception as e:  # a job must never stay 'running' because of an exception
        log.exception("job %s failed", job_id)
        job.fail(getattr(e, "code", "job_failed"), str(e)[:300])


def mark_stale() -> None:
    """On startup: anything still running after 10 min died with a previous process."""
    with engine.begin() as conn:
        conn.execute(text("update jobs set status = 'stale' where status in ('queued', 'running') and coalesce(heartbeat_at, created_at) < now() - interval '10 minutes'"))
        conn.execute(text("update runs set status = 'stale' where status = 'running' and started_at < now() - interval '10 minutes'"))

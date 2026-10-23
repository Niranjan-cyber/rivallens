"""C-12 report builder: every claim carries evidence; unevidenced facts become limitations; the LLM only summarises claims."""
import json
from datetime import UTC, date, datetime, timedelta
from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import Connection, text

from app import jobs
from app.auth import User, UserDep
from app.db import ConnDep, engine
from app.jobs import Job
from app.llm.gateway import LLMUnavailable, complete_json
from app.modules.alerts.service import alert_text
from app.modules.changes.router import JobAccepted
from app.modules.changes.runs import show
from app.modules.comparison.router import comparison
from app.modules.simulator.router import _load, save_version
from app.modules.simulator.service import inr

router = APIRouter(prefix="/api/v1", tags=["reports"])


class ReportIn(BaseModel):
    from_: date | None = Field(None, alias="from")
    to: date | None = None


class Suggestion(BaseModel):
    text: str
    claim_ids: list[str] = Field(default_factory=list)


class Summary(BaseModel):
    summary: str | None = Field(None, description="At most 120 words, using only the claims")
    suggestions: list[Suggestion] = Field(default_factory=list, description="Up to 3 actions, each citing the claim ids it rests on")


def _claim(claims: list, section: list, text_: str, kind: str, eid, observed_at, source_url) -> None:
    cid = f"c{len(claims) + 1}"
    c = {"id": cid, "text": text_, "evidence": {"type": kind, "id": str(eid), "observed_at": observed_at, "source_url": source_url}}
    claims.append(c)
    section.append(c)


def build(conn: Connection, profile_id: UUID, user: User, start: date, end: date) -> dict:
    claims, limitations = [], []
    changes = []
    for e in conn.execute(text("""
        select e.id, e.change_type, e.field_path, e.prev_value, e.curr_value, e.delta_pct, e.observed_at, e.status, c.name, s.url
        from change_events e join competitors c on c.id = e.competitor_id join sources s on s.id = e.source_id
        where c.profile_id = :p and e.observed_at::date between :a and :b order by e.observed_at desc limit 20
    """), {"p": profile_id, "a": start, "b": end}).mappings():
        change = {"change_type": e["change_type"], "field_path": e["field_path"], "delta_pct": e["delta_pct"]}
        note = "" if e["status"] == "confirmed" else " (needs review)"
        _claim(claims, changes, alert_text(e["name"], change, show(e["prev_value"]), show(e["curr_value"]),
                                           e["observed_at"].strftime("%d %b %Y")).split(" · observed")[0] + note,
               "receipt", e["id"], e["observed_at"], e["url"])
    if not changes:
        limitations.append(f"No competitor changes were detected between {start:%d %b} and {end:%d %b %Y}.")

    comp = []
    cmp_ = comparison(profile_id, user, conn, "comparable")
    ranked = [r for r in cmp_["rows"] if r["ranked"] and r["subject"] == "competitor"]
    for i, r in enumerate(ranked[:3], 1):
        known = [(c["label"], r["cells"][c["key"]]) for c in cmp_["criteria"] if c["enabled"] and r["cells"][c["key"]]["known"]]
        price = r["cells"]["entry_price"]
        if price["known"]:
            _claim(claims, comp, f"{r['name']} ranks #{i} of {len(ranked)} on your criteria (score {round(r['score'] * 100)}); entry price {price['display']}.",
                   "observation", price["evidence_id"], price["observed_at"], price["source_url"])
        elif known:
            label, cell = known[0]
            _claim(claims, comp, f"{r['name']} ranks #{i} of {len(ranked)} on your criteria (score {round(r['score'] * 100)}); {label.lower()}: {cell['display']}.",
                   "observation", cell["evidence_id"], cell["observed_at"], cell["source_url"])
    for r in cmp_["rows"]:
        if not r["ranked"] and r["subject"] == "competitor":
            limitations.append(f"{r['name']} isn't ranked: only {r['known_weight_pct']}% of the criteria weight is known ({r['unknown_count']} unknown).")

    sim_section = []
    try:
        sim = _load(conn, profile_id) or save_version(conn, profile_id, {}, None)
        replan = sim.get("replanned")
        line = f"Recommended launch price {inr(sim['recommended_price_inr'])}/month (simulator version {sim['version']}, a scenario model, not a forecast)"
        if replan:
            ev = conn.execute(text("select e.observed_at, s.url from change_events e join sources s on s.id = e.source_id where e.id = :id"),
                              {"id": replan["trigger_change_event_id"]}).first()
            why = replan["summary"].split(" because ", 1)[-1]
            before = replan["summary"].removeprefix("Recommended ").split(" → ")[0]
            _claim(claims, sim_section, f"{line}, re-planned from {before} because {why}.", "receipt", replan["trigger_change_event_id"],
                   ev.observed_at if ev else None, ev.url if ev else None)
        else:
            ev = next((e for e in sim["market"]["evidence"] if e.get("evidence_id")), None)
            if ev:
                _claim(claims, sim_section, f"{line}, anchored on a market median of {inr(sim['market']['median_price_inr'])}/month.",
                       "receipt", ev["evidence_id"], ev["observed_at"], ev["source_url"])
            else:
                limitations.append(f"{line}; it rests on observed prices without a change receipt, so it is not cited as a claim.")
        limitations += [f"Simulator flag: {f['text']}" for f in sim["viability_flags"]]
    except HTTPException:
        limitations.append("No launch simulation: fewer than two comparable competitors have known prices.")

    summary, suggestions, unavailable = None, [], False
    if claims:
        try:
            out = complete_json("report_summary", Summary, {"claims": json.dumps([{"id": c["id"], "text": c["text"]} for c in claims], ensure_ascii=False),
                                "instruction": "Summarise for a founder in at most 120 words. Suggest up to 3 concrete actions; each must cite claim ids."},
                                "report_summary.v1", cache_if=lambda o: bool(o.summary))
            valid = {c["id"] for c in claims}
            summary = " ".join((out.summary or "").split()[:120]) or None
            suggestions = [{"text": s.text, "claim_ids": [i for i in s.claim_ids if i in valid], "label": "AI suggestion"}
                           for s in out.suggestions if set(s.claim_ids) & valid][:3]
        except LLMUnavailable:
            unavailable = True
    return {"generated_at": datetime.now(UTC).isoformat(), "range": {"from": str(start), "to": str(end)},
            "summary": summary, "summary_unavailable": unavailable or summary is None,
            "sections": [{"title": "What changed", "claims": changes}, {"title": "How they compare", "claims": comp},
                         {"title": "What it means for your launch", "claims": sim_section}],
            "suggestions": suggestions, "limitations": limitations}


def _job(job: Job, profile_id: UUID, user: User, start: date, end: date) -> dict:
    job.step("claims", "running", None, "Collecting evidence")
    with engine.begin() as conn:
        body = build(conn, profile_id, user, start, end)
        rid = conn.execute(text("insert into reports (profile_id, job_id, range, body) values (:p, :j, cast(:r as jsonb), cast(:b as jsonb)) returning id"),
                           {"p": profile_id, "j": job.id, "r": json.dumps(body["range"]), "b": json.dumps(body, default=str)}).scalar()
    job.step("claims", "done", sum(len(s["claims"]) for s in body["sections"]), "Report ready")
    return {"report_id": str(rid)}


@router.post("/profiles/{profile_id}/reports", status_code=202)
def create_report(profile_id: UUID, body: ReportIn, user: UserDep, conn: ConnDep, background: BackgroundTasks) -> JobAccepted:
    if not conn.execute(text("select 1 from profiles where id = :p and user_id = :u"), {"p": profile_id, "u": user.id}).first():
        raise HTTPException(404, {"code": "not_found", "message": "Profile not found."})
    end = body.to or date.today()
    start = body.from_ or end - timedelta(days=30)
    job_id = jobs.create(user.id, profile_id, "report")
    background.add_task(jobs.run, job_id, lambda job: _job(job, profile_id, user, start, end))
    return JobAccepted(job_id=job_id, status="queued")


@router.get("/reports/{report_id}")
def get_report(report_id: UUID, user: UserDep, conn: ConnDep) -> dict:
    row = conn.execute(text("select r.id, r.profile_id, r.body from reports r join profiles p on p.id = r.profile_id where r.id = :id and p.user_id = :u"),
                       {"id": report_id, "u": user.id}).mappings().first()
    if row is None:
        raise HTTPException(404, {"code": "not_found", "message": "Report not found."})
    return {"id": row["id"], "profile_id": row["profile_id"], **row["body"]}


@router.get("/profiles/{profile_id}/reports/latest")
def latest_report(profile_id: UUID, user: UserDep, conn: ConnDep) -> dict | None:
    rid = conn.execute(text("""select r.id from reports r join profiles p on p.id = r.profile_id
        where r.profile_id = :p and p.user_id = :u order by r.created_at desc limit 1"""), {"p": profile_id, "u": user.id}).scalar()
    return get_report(rid, user, conn) if rid else None

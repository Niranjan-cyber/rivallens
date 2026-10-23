"""A monitoring run over a profile's sources: fetch → sections → extract → compare → ledger and change events."""
import hashlib
import json
from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import text

from app.db import engine
from app.jobs import Job
from app.modules.alerts.router import raise_alert, rules_for
from app.modules.changes.service import compare
from app.modules.collector.service import fetch, split_sections, store_snapshot
from app.modules.extractor.service import extract

SYMBOL = {"INR": "₹", "USD": "$"}


def show(value) -> str | None:
    """Human form of a field value: '₹1,499/month' for prices, the text otherwise."""
    if isinstance(value, dict) and "amount" in value:
        if value["amount"] is None:
            return "no price shown"
        amount = f"{SYMBOL.get(value['currency'], value['currency'] or '')}{value['amount']:,.{0 if value['amount'] == int(value['amount']) else 2}f}"
        return f"{amount}/{value['period']}" if value.get("period") else amount
    return value


def _excerpt(snap_text: str, value) -> dict | None:
    needle = value.get("raw") if isinstance(value, dict) else value
    i = snap_text.find(needle) if needle else -1
    return {"start": i, "end": i + len(needle)} if i >= 0 else None


def _sources(conn, profile_id: UUID):
    # Mock pages only for now; real competitor pages join in B08.
    return conn.execute(text("""
        select s.id, s.url, c.id as competitor_id, c.name, c.relation, c.is_demo_data from sources s join competitors c on c.id = s.competitor_id
        where c.profile_id = :p and c.selected and s.is_mock order by c.created_at
    """), {"p": profile_id}).mappings().all()


def _previous(conn, source_id: UUID):
    return conn.execute(text("""
        select s.id, s.observed_at, s.text, s.sections, o.fields from snapshots s join observations o on o.snapshot_id = s.id
        where s.source_id = :s and s.status = 'ok' order by s.observed_at desc limit 1
    """), {"s": source_id}).mappings().first()


def start_run(profile_id: UUID, job_id: UUID) -> UUID:
    with engine.begin() as conn:
        first = not conn.execute(text("""
            select 1 from snapshots sn join sources s on s.id = sn.source_id join competitors c on c.id = s.competitor_id
            where c.profile_id = :p limit 1
        """), {"p": profile_id}).first()
        return conn.execute(text("insert into runs (profile_id, job_id, kind) values (:p, :j, :k) returning id"),
                            {"p": profile_id, "j": job_id, "k": "baseline" if first else "run"}).scalar()


def monitor(job: Job, profile_id: UUID, run_id: UUID) -> dict:
    counts = {"sources": 0, "diffs": 0, "ignored": 0, "meaningful": 0, "needs_review": 0, "failed": 0}
    with engine.begin() as conn:
        sources = _sources(conn, profile_id)
        profile = conn.execute(text("select user_id, card from profiles where id = :p"), {"p": profile_id}).one()
        planned = (profile.card or {}).get("price") or {}
        planned = planned.get("value", planned) if isinstance(planned, dict) else {}  # card leaves may be {value, origin}
        ctx = {"profile_id": profile_id, "user_id": profile.user_id, "rules": rules_for(conn, profile_id),
               "planned_price": planned.get("amount") if isinstance(planned, dict) else None}
    counts["sources"] = len(sources)
    job.step("fetch", "running", len(sources), "Fetching pricing pages")
    status = "failed"
    try:
        for src in sources:
            _check_source(src, run_id, counts, ctx)
            job.step("source", "done", counts["meaningful"], src["url"])
        status = "done"
    finally:
        with engine.begin() as conn:
            conn.execute(text("update runs set status = :st, finished_at = now(), counts = cast(:c as jsonb) where id = :r"),
                         {"st": status, "c": json.dumps(counts), "r": run_id})
    job.step("diff", "done", counts["meaningful"], f"{counts['ignored']} ignored, {counts['meaningful']} meaningful")
    return {"run_id": str(run_id)}


def _fingerprint(competitor_id, field_path: str, value) -> str:
    if isinstance(value, dict):  # normalized: amount, currency and period only
        value = [value.get("amount"), value.get("currency"), value.get("period")]
    return hashlib.sha256(f"{competitor_id}|{field_path}|{json.dumps(value)}".encode()).hexdigest()[:32]


def _check_source(src, run_id: UUID, counts: dict, ctx: dict) -> None:
    observed_at = datetime.now(UTC)
    page = fetch(src["url"])
    with engine.begin() as conn:
        if page["status"] != "ok":
            counts["failed"] += 1
            conn.execute(text("""insert into snapshots (source_id, run_id, observed_at, status, http_status, bytes)
                                 values (:s, :r, :t, :st, :h, :b)"""),
                         {"s": src["id"], "r": run_id, "t": observed_at, "st": page["status"], "h": page["http_status"], "b": page["bytes"]})
            return
        html = page["html"]
        snap_text, sections = split_sections(html)
        prev = _previous(conn, src["id"])
        prev_pricing = {s["hash"] for s in prev["sections"] if s["pricing"]} if prev else None
        reuse = prev_pricing is not None and prev_pricing == {s["hash"] for s in sections if s["pricing"]}
        fields = extract(html, prev["fields"] if prev else None, reuse)
        digest, path = store_snapshot(str(src["id"]), observed_at.isoformat(), html)
        snap_id = conn.execute(text("""
            insert into snapshots (source_id, run_id, observed_at, status, http_status, storage_path, sha256, text, sections, bytes)
            values (:s, :r, :t, 'ok', :h, :p, :d, :x, cast(:sec as jsonb), :b) returning id
        """), {"s": src["id"], "r": run_id, "t": observed_at, "h": page["http_status"], "p": path, "d": digest,
               "x": snap_text, "sec": json.dumps(sections), "b": page["bytes"]}).scalar()
        conn.execute(text("insert into observations (snapshot_id, source_id, observed_at, fields) values (:i, :s, :t, cast(:f as jsonb))"),
                     {"i": snap_id, "s": src["id"], "t": observed_at, "f": json.dumps(fields)})
        if prev is None:
            return

        ledger, changes = compare(dict(prev), {"text": snap_text, "sections": sections, "fields": fields})
        for e in ledger:
            conn.execute(text("insert into ledger_entries (run_id, source_id, section_key, reason, summary) values (:r, :s, :k, :re, :su)"),
                         {"r": run_id, "s": src["id"], "k": e["section_key"], "re": e["reason"], "su": e["summary"]})
        for c in changes:
            fingerprint = _fingerprint(src["competitor_id"], c["field_path"], c["curr"])
            event_id = conn.execute(text("""
                insert into change_events (run_id, source_id, competitor_id, change_type, field_path, prev_value, curr_value, delta_pct,
                    status, before_snapshot_id, after_snapshot_id, excerpt, observed_at, prev_observed_at, fingerprint, is_demo_data)
                values (:r, :s, :c, :t, :f, cast(:pv as jsonb), cast(:cv as jsonb), :d, :st, :b, :a, cast(:ex as jsonb), :o, :po, :fp, :demo)
                returning id
            """), {"r": run_id, "s": src["id"], "c": src["competitor_id"], "t": c["change_type"], "f": c["field_path"],
                   "pv": json.dumps(c["prev"]), "cv": json.dumps(c["curr"]), "d": c["delta_pct"], "st": c["status"],
                   "b": prev["id"], "a": snap_id, "o": observed_at, "po": prev["observed_at"], "fp": fingerprint, "demo": src["is_demo_data"],
                   "ex": json.dumps({"before": _excerpt(prev["text"], c["prev"]), "after": _excerpt(snap_text, c["curr"])})}).scalar()
            raise_alert(conn, ctx, src, event_id, c, fingerprint, show(c["prev"]), show(c["curr"]), observed_at)
        counts["diffs"] += len(ledger) + len(changes)
        counts["ignored"] += len(ledger)
        counts["meaningful"] += sum(c["status"] == "confirmed" for c in changes)
        counts["needs_review"] += sum(c["status"] == "needs_review" for c in changes)

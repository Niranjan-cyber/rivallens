"""Milestone 1: GET /profiles/{id}/setup gathers what the business has collected and returns the setup plan (service.plan)."""
from collections import Counter
from datetime import UTC, datetime, timedelta
from uuid import UUID
from zoneinfo import ZoneInfo

from fastapi import APIRouter, HTTPException
from sqlalchemy import Connection, text

from app.auth import UserDep
from app.db import ConnDep
from app.modules.alerts.service import alert_text
from app.modules.changes.runs import show
from app.modules.customers.router import customer_summary
from app.modules.discovery.pipeline import card_value
from app.modules.money.router import money_summary
from app.modules.products.router import COLS, comparison_data
from app.modules.setup.service import plan

router = APIRouter(prefix="/api/v1", tags=["setup"])
RECENT = timedelta(days=30)
IST = ZoneInfo("Asia/Kolkata")


def _day(ts) -> str | None:
    ts = ts and ts.astimezone(IST)
    return f"{ts.day} {ts.strftime('%b %Y')}" if ts else None


def _products(conn: Connection, profile_id: UUID) -> list[dict]:
    out = []
    for p in conn.execute(text(f"select {COLS} from products where profile_id = :p order by stage, created_at"), {"p": profile_id}).mappings():
        p = dict(p)
        row = {"id": str(p["id"]), "name": p["name"], "price": float(p["price"]) if p["price"] is not None else None, "unit": p["unit"],
               "category_path": p["category_path"], "niche": p["niche"], "like_for_like": 0, "broad": 0, "position": None, "sources": [], "seen": None}
        if p["taxonomy_id"]:
            c = comparison_data(conn, p)
            priced = [r for r in c["rows"] if r["price"] is not None]
            like = [r for r in priced if r["same_niche"]]
            row |= {"like_for_like": len(like), "broad": len(priced), "sources": list(dict.fromkeys(r["domain"] for r in like)),
                    "position": c["position"] if c["basis"] == "niche" else None,
                    "seen": _day(max((r["observed_at"] for r in like), default=None))}
        out.append(row)
    return out


def _discovery(conn: Connection, profile_id: UUID) -> dict | None:
    job = conn.execute(text("""select id, status, result, error from jobs where profile_id = :p and kind = 'discovery'
                               order by created_at desc limit 1"""), {"p": profile_id}).mappings().first()
    if not job:
        return None
    reasons = Counter(r for row in conn.execute(text("select reasons from discovery_candidates where job_id = :j and status = 'rejected'"),
                                                {"j": job["id"]}) for r in row[0])
    res = job["result"] or {}
    return {"status": job["status"], "verified": res.get("verified", 0), "rejected": res.get("rejected", 0),
            "reasons": [r for r, _ in reasons.most_common(3)], "error": (job["error"] or {}).get("message")}


def _monitoring(conn: Connection, profile_id: UUID) -> dict:
    runs = conn.execute(text("""select min(started_at) filter (where kind = 'baseline' and status = 'done') as baseline,
                                       max(started_at) filter (where status = 'done') as last from runs where profile_id = :p"""),
                        {"p": profile_id}).mappings().one()
    failed = [r[0] for r in conn.execute(text("""
        select distinct c.name from competitors c join sources s on s.competitor_id = c.id
        join lateral (select status from snapshots where source_id = s.id order by observed_at desc limit 1) sn on true
        where c.profile_id = :p and c.selected and sn.status <> 'ok'"""), {"p": profile_id})]
    return {"baseline_at": _day(runs["baseline"]), "last_run_at": _day(runs["last"]), "failed": failed}


def _receipt(conn: Connection, profile_id: UUID) -> dict | None:
    e = conn.execute(text("""
        select e.id, c.name, e.change_type, e.field_path, e.prev_value, e.curr_value, e.delta_pct, e.observed_at
        from change_events e join competitors c on c.id = e.competitor_id
        where c.profile_id = :p and e.status = 'confirmed' and e.observed_at > :since order by e.observed_at desc limit 1"""),
                     {"p": profile_id, "since": datetime.now(UTC) - RECENT}).mappings().first()
    if not e:
        return None
    change = {"field_path": e["field_path"], "delta_pct": e["delta_pct"]}
    return {"id": str(e["id"]), "observed_at": _day(e["observed_at"]),
            "text": alert_text(e["name"], change, show(e["prev_value"]), show(e["curr_value"]), "").split(" · observed")[0]}


@router.get("/profiles/{profile_id}/setup")
def get_setup(profile_id: UUID, user: UserDep, conn: ConnDep) -> dict:
    prof = conn.execute(text("select card from profiles where id = :p and user_id = :u"), {"p": profile_id, "u": user.id}).mappings().first()
    if not prof:
        raise HTTPException(404, {"code": "not_found", "message": "Business not found."})
    card = prof["card"] or {}
    markets = card_value(card, "india_markets") or []
    comp = conn.execute(text("select count(*) filter (where selected) as selected, count(*) as total from competitors where profile_id = :p"),
                        {"p": profile_id}).mappings().one()
    money = money_summary(conn, profile_id, card)
    cust = customer_summary(conn, profile_id)
    complaints = sorted((t for t in cust["themes"] if t["kind"] == "complaint"), key=lambda t: -t.get("count", len(t["mention_ids"])))
    state = {
        "card": {"target_customer": card_value(card, "target_customer"), "markets": markets if isinstance(markets, list) else [markets]},
        "products": _products(conn, profile_id), "discovery": _discovery(conn, profile_id), "competitors": dict(comp),
        "monitoring": _monitoring(conn, profile_id), "receipt": _receipt(conn, profile_id),
        "money": {"transactions": money["transactions_count"], "has_costs": money["metrics"]["monthly_expenses"] is not None,
                  "runway_months": money["metrics"]["runway_months"]},
        "customers": {"total": cust["total"],
                      "complaint": {"label": complaints[0]["label"], "count": complaints[0].get("count", len(complaints[0]["mention_ids"]))} if complaints else None},
    }
    return plan(state, f"/app/{profile_id}")

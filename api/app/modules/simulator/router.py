import json
import statistics
from uuid import UUID

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import Connection, text

from app.auth import UserDep
from app.db import ConnDep
from app.modules.comparison.router import competitor_cells
from app.modules.discovery.pipeline import card_value
from app.modules.simulator.service import DEFAULTS, inr, simulate, viability_flags

router = APIRouter(prefix="/api/v1", tags=["simulator"])
UNITS = {"segment_size": "accounts", "base_conversion": "share", "elasticity_best": "", "elasticity_expected": "", "elasticity_worst": "",
         "coverage_weight": "", "ramp_months": "months", "upfront_cost": "₹", "monthly_cost": "₹ a month"}


class AssumptionsIn(BaseModel):
    assumptions: dict[str, float]


class OptionIn(BaseModel):
    price_inr: float = Field(gt=0, le=10_000_000)


def _market(conn: Connection, profile_id: UUID) -> tuple[list[dict], list[dict], set[str]]:
    rows = conn.execute(text("""
        select c.id, c.name, c.relation, c.india_signals,
               (select json_build_object('snapshot_id', sn.id, 'observed_at', sn.observed_at, 'url', s.url, 'text', sn.text, 'fields', o.fields)
                from sources s join snapshots sn on sn.source_id = s.id join observations o on o.snapshot_id = sn.id
                where s.competitor_id = c.id and sn.status = 'ok' order by sn.observed_at desc limit 1) as latest,
               (select e.id from change_events e where e.competitor_id = c.id and e.change_type like 'price_%'
                order by e.observed_at desc limit 1) as receipt_id,
               (select reasons[array_length(reasons, 1)] from discovery_candidates d where d.profile_id = c.profile_id and d.domain = c.domain
                order by created_at desc limit 1) as reason
        from competitors c where c.profile_id = :p and c.selected order by c.created_at
    """), {"p": profile_id}).mappings().all()
    comparables, inspiration, features = [], [], set()
    for r in rows:
        latest = r["latest"]
        mid = competitor_cells(latest["fields"], latest["text"], latest)["mid_price"] if latest else {"known": False}
        item = {"name": r["name"], "india_verified": (r["india_signals"] or {}).get("score", 0) >= 1, "reason": r["reason"],
                "evidence_id": str(r["receipt_id"]) if r["receipt_id"] else None,
                "price_inr": mid["value"] if mid.get("known") else None, "source_url": latest["url"] if latest else None,
                "observed_at": latest["observed_at"] if latest else None}
        if r["relation"] == "comparable":
            comparables.append(item)
            if latest:
                features |= {f.lower() for pl in latest["fields"].get("plans", []) for f in pl.get("features", [])}
        else:
            inspiration.append(item)
    return comparables, inspiration, features


def compute(conn: Connection, profile_id: UUID, overrides: dict, extra_option: float | None) -> dict:
    card = conn.execute(text("select card from profiles where id = :p"), {"p": profile_id}).scalar() or {}
    comparables, inspiration, union = _market(conn, profile_id)
    priced = [c for c in comparables if c["price_inr"]]  # free mid tiers can't anchor a price (median 0)
    planned = (card_value(card, "price") or {}).get("amount")
    if len(priced) >= 2:
        m, m_origin = statistics.median(c["price_inr"] for c in priced), "evidence"
    elif planned and planned > 0:
        m, m_origin = float(planned), "your assumption"  # ideas and thin markets: anchor on the user's own price, labelled
    else:
        raise HTTPException(409, {"code": "insufficient_price_data", "message": "Need prices from at least 2 comparable competitors, or your own price on the card."})
    card_assumptions = card_value(card, "sim_assumptions") or {}
    a = {**DEFAULTS, **card_assumptions, **overrides}
    mine = {f.lower() for k in ("attributes", "planned_features") for f in (card_value(card, k) or [])}
    f = len(mine & union) / len(union) if union else 0.5
    sim = simulate(m, f, a, planned=planned, extra=extra_option)
    sim["assumptions"] = a
    flags = viability_flags(sim, comparables, inspiration)
    sim["assumption_list"] = [{"key": k, "value": v, "unit": UNITS.get(k, ""),
                               "origin": "user" if k in overrides else "your assumption" if k in card_assumptions else "default"} for k, v in a.items()]
    sim["market"] = {"median_price_inr": m, "origin": m_origin, "n_priced": len(priced),
                     "evidence": [{k: c[k] for k in ("name", "price_inr", "source_url", "observed_at", "evidence_id")} for c in priced]}
    sim["viability_flags"] = flags
    sim["price_unit"] = "" if (card_value(card, "price") or {}).get("period") == "one_time" else "/month"  # products: price per unit sold
    return sim


def save_version(conn: Connection, profile_id: UUID, overrides: dict, extra: float | None, trigger=None, summary=None) -> dict:
    prev = conn.execute(text("select version, recommended_price_inr from simulations where profile_id = :p order by version desc limit 1"),
                        {"p": profile_id}).mappings().first()
    sim = compute(conn, profile_id, overrides, extra)
    version = (prev["version"] if prev else 0) + 1
    conn.execute(text("""
        insert into simulations (profile_id, version, assumptions, options, recommended_option, recommended_price_inr, reason, viability_flags,
                                 result, replanned_from_version, trigger_change_event_id, replan_summary)
        values (:p, :v, cast(:a as jsonb), cast(:o as jsonb), :ro, :rp, :r, cast(:f as jsonb), cast(:res as jsonb), :fv, :t, :s)
    """), {"p": profile_id, "v": version, "a": json.dumps(overrides), "o": json.dumps({"extra": extra}), "ro": sim["recommended_option"],
           "rp": sim["recommended_price_inr"], "r": sim["reason"], "f": json.dumps(sim["viability_flags"]), "res": json.dumps(sim, default=str),
           "fv": prev["version"] if (prev and trigger) else None, "t": trigger, "s": summary})
    return _load(conn, profile_id)


def _load(conn: Connection, profile_id: UUID) -> dict | None:
    row = conn.execute(text("""select version, result, replanned_from_version, trigger_change_event_id, replan_summary, assumptions, options
        from simulations where profile_id = :p order by version desc limit 1"""), {"p": profile_id}).mappings().first()
    if row is None:
        return None
    replanned = ({"from_version": row["replanned_from_version"], "trigger_change_event_id": row["trigger_change_event_id"], "summary": row["replan_summary"]}
                 if row["trigger_change_event_id"] else None)
    return {**row["result"], "version": row["version"], "replanned": replanned, "label": "Scenario model, not a forecast",
            "_overrides": row["assumptions"], "_extra": (row["options"] or {}).get("extra")}


def replan(conn: Connection, profile_id: UUID, trigger_id: UUID, competitor: str, field: str, delta_pct: float | None) -> None:
    """Called by a monitoring run after a price/plan/feature change at a comparable competitor (specs §1 C-11)."""
    before = _load(conn, profile_id)
    try:
        if before is None:
            before = save_version(conn, profile_id, {}, None)
        after = compute(conn, profile_id, before["_overrides"], before["_extra"])
    except HTTPException:
        return  # not enough price data to simulate yet
    plan = field.split(".")[1] if field.startswith("plans.") else field
    change = f"{plan} {'+' if (delta_pct or 0) > 0 else '−'}{abs(delta_pct):g}%" if delta_pct else plan
    summary = f"Recommended {inr(before['recommended_price_inr'])} → {inr(after['recommended_price_inr'])} because {competitor} {change}"
    save_version(conn, profile_id, before["_overrides"], before["_extra"], trigger_id, summary)


def _own(conn: Connection, profile_id: UUID, user_id: UUID) -> None:
    if not conn.execute(text("select 1 from profiles where id = :p and user_id = :u"), {"p": profile_id, "u": user_id}).first():
        raise HTTPException(404, {"code": "not_found", "message": "Profile not found."})


def _public(sim: dict) -> dict:
    return {k: v for k, v in sim.items() if not k.startswith("_")}


@router.get("/profiles/{profile_id}/simulation")
def get_simulation(profile_id: UUID, user: UserDep, conn: ConnDep) -> dict:
    _own(conn, profile_id, user.id)
    return _public(_load(conn, profile_id) or save_version(conn, profile_id, {}, None))


@router.put("/profiles/{profile_id}/simulation/assumptions")
def put_assumptions(profile_id: UUID, body: AssumptionsIn, user: UserDep, conn: ConnDep) -> dict:
    _own(conn, profile_id, user.id)
    current = _load(conn, profile_id) or {"_overrides": {}, "_extra": None}
    allowed = {k: v for k, v in body.assumptions.items() if k in DEFAULTS and v >= 0}
    return _public(save_version(conn, profile_id, {**current["_overrides"], **allowed}, current["_extra"]))


@router.post("/profiles/{profile_id}/simulation/options")
def add_option(profile_id: UUID, body: OptionIn, user: UserDep, conn: ConnDep) -> dict:
    _own(conn, profile_id, user.id)
    current = _load(conn, profile_id) or {"_overrides": {}, "_extra": None}
    return _public(save_version(conn, profile_id, current["_overrides"], body.price_inr))

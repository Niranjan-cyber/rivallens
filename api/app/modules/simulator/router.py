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
from app.llm.gateway import LLMUnavailable, complete_json
from app.modules.simulator.service import (ASSUMPTION_LABEL, DEFAULTS, calibrate_segment, checked_segment, conversion, feature_coverage, inr,
                                           launch_cash_months, request_boost, runway_flag, runway_with, scenario_diff, sensitivity,
                                           sentiment_shift, simulate, unit_cost, viability_flags)

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
    period = (card_value(card, "price") or {}).get("period")
    one_off = period == "one_time" or (period is None and card_value(card, "offering_type") == "product")
    sim["price_unit"] = "" if one_off else "/month"  # products: price per unit sold
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


# ---- B14i: a simulator and a suggested segment per product, fed by Market, Money and Customers ----

LINKS = {"market": "dashboard", "money": "finance", "customers": "customers", "product": "product-detail", "default": None}


KIND = {"market": "observed", "money": "yours", "customers": "yours", "product": "yours", "default": "estimate"}


def _in(label: str, value: str, source: str, evidence_id: str | None = None, kind: str | None = None) -> dict:
    """kind: observed (read from a public page), yours (entered or uploaded), estimate (benchmark or derived)."""
    return {"label": label, "value": value, "source": source, "link": LINKS[source], "evidence_id": evidence_id, "kind": kind or KIND[source]}


def _product(conn: Connection, product_id: UUID, user_id: UUID) -> tuple[dict, dict, dict]:
    from app.modules.products.router import _owned_product, comparison_data
    p = _owned_product(conn, product_id, user_id)
    card = conn.execute(text("select card from profiles where id = :p"), {"p": p["profile_id"]}).scalar() or {}
    return p, card, comparison_data(conn, p)


def _units_per_month(conn: Connection, profile_id, name: str) -> float | None:
    """This product's units sold a month in Finance (the last 3 months of sales data), or None."""
    v = conn.execute(text("""
        select sum(coalesce(quantity, 1))::float / 3 from transactions
        where profile_id = :p and kind = 'sale' and lower(product) = lower(:n)
          and date > (select max(date) from transactions where profile_id = :p and kind = 'sale') - 90"""), {"p": profile_id, "n": name}).scalar()
    return round(v, 1) if v else None


SHOWN = ("segment_size", "base_conversion", "elasticity_expected", "ramp_months", "upfront_cost", "monthly_cost")


def product_sim(conn: Connection, p: dict, card: dict, comp: dict) -> dict:
    """Workstream 4: unit cost → gross profit → break-even and runway, calibrated to real sales when Finance has them.
    Every input and assumption says where it comes from; the founder can override any assumption for this product."""
    from app.modules.customers.router import customer_summary
    from app.modules.money.router import money_summary
    pid, pos, inputs = p["profile_id"], comp["position"], []
    price = float(p["price"]) if p["price"] is not None else None
    existing = p["stage"] == "existing"
    if pos["n"] >= 3:  # like-for-like only, the same bar as the product page and setup
        m = pos["median"]
        inputs.append(_in("Market price (median)", f"{inr(m)} across {pos['n']} like-for-like products", "market"))
    else:
        priced = [c for c in _market(conn, pid)[0] if c["price_inr"]]
        if len(priced) >= 2:
            m = statistics.median(c["price_inr"] for c in priced)
            inputs.append(_in("Market price (median)", f"{inr(m)} across {len(priced)} monitored competitors", "market"))
        elif price:
            m = price
            inputs.append(_in("Market price", f"{inr(m)}: your own price, no market prices yet", "product", kind="estimate"))
        else:
            raise HTTPException(409, {"code": "insufficient_price_data", "message": "Find comparable products or set this product's price first."})
    receipt = conn.execute(text("""select e.id, c.name, e.delta_pct from change_events e join competitors c on c.id = e.competitor_id
        where c.profile_id = :p and e.change_type like 'price_%' order by e.observed_at desc limit 1"""), {"p": pid}).mappings().first()
    if receipt:
        d = receipt["delta_pct"]
        inputs.append(_in("Latest competitor price change", f"{receipt['name']} {float(d):+g}%" if d is not None else receipt["name"],
                          "market", str(receipt["id"])))

    # Assumptions: defaults < an existing product's (its costs are already in Finance, it sells from month 1) < business < this product
    mine = {k: float(v) for k, v in (p.get("sim_assumptions") or {}).items() if k in DEFAULTS}
    a = {**DEFAULTS, **({"upfront_cost": 0, "monthly_cost": 0, "ramp_months": 1} if existing else {}),
         **(card_value(card, "sim_assumptions") or {}), **mine}
    origin = {k: "yours" if k in mine else "default" for k in DEFAULTS}

    money = money_summary(conn, pid, card)
    met, bench = money["metrics"], money["benchmark"] or {}
    cash, burn, runway = money["cash"], met["monthly_burn"], met["runway_months"]
    uc, uc_source = unit_cost(price or m, float(p["unit_cost"]) if p["unit_cost"] is not None else None, bench.get("gross_margin"))
    if uc is not None:
        inputs.append(_in("Unit cost", f"{inr(uc)} (yours)" if uc_source == "product" else
                          f"{inr(uc)}: {bench['industry']} gross margin {bench['gross_margin']:.1%}, Damodaran India",
                          "product" if uc_source == "product" else "money", kind="yours" if uc_source == "product" else "estimate"))
    if met["operating_margin"] is not None:
        inputs.append(_in("Your operating margin", f"{met['operating_margin']:.1%}", "money"))
    inputs.append(_in("Runway", f"{runway:g} months" if runway is not None else
                      "not burning cash" if burn == 0 else
                      "unknown: add your costs" if burn is None else "unknown: add cash in the bank", "money"))

    cs = customer_summary(conn, pid)
    features = [str(x) for x in p["features"] or []]
    f, covered = request_boost(feature_coverage(features, [r["features"] or [] for r in comp["rows"]]), features, cs["themes"])
    inputs.append(_in("Feature coverage", f"{f:.0%} of comparables' features", "market", kind="estimate"))
    if covered:
        inputs.append(_in("Customer requests you answer", ", ".join(covered[:3]), "customers"))

    # Calibrate to real sales: the segment that makes today's price sell what Finance says it sold
    units = _units_per_month(conn, pid, p["name"]) if existing and price else None
    seg = calibrate_segment(units, conversion(price, m, f, a["base_conversion"], a["elasticity_expected"], a["coverage_weight"])) if units else None
    if seg and "segment_size" not in mine:
        a["segment_size"], origin["segment_size"] = seg, "your sales"
        inputs.append(_in("Units sold a month", f"{units:g} (last 3 months of sales)", "money"))
    else:  # real sales already reflect what customers think; only an uncalibrated model is nudged by sentiment
        shift = sentiment_shift(cs["sentiment"])
        if shift is not None and "base_conversion" not in mine:
            a["base_conversion"], origin["base_conversion"] = round(a["base_conversion"] * (1 + shift), 4), "estimate"
            sp = cs["sentiment"]
            inputs.append(_in("Customer sentiment", f"{sp.get('positive', 0)} positive, {sp.get('negative', 0)} negative → conversion {shift:+.0%}",
                              "customers", kind="estimate"))
    if existing:
        inputs.append(_in("Launch and running costs", "₹0: already selling, its costs are in your Finance numbers", "product"))

    sim = simulate(m, f, a, planned=price, unit_cost=uc)
    flags = []
    now_gp = None
    if existing and price and uc is not None:  # today's monthly gross profit, the baseline every option's runway moves from
        now_gp = (price - uc) * a["segment_size"] * conversion(price, m, f, a["base_conversion"], a["elasticity_expected"], a["coverage_weight"])
    for o in sim["options"]:
        e = o["scenarios"]["expected"]
        if existing and o["origin"] == "your planned price":
            o["origin"] = "your price today"
        if uc is not None:
            o["unit_margin_inr"] = round(o["price_inr"] - uc)
            o["gross_profit_12m_inr"] = e["gross_profit_12m_inr"]
        if existing:
            o["runway_months"] = runway_with(cash, burn, e["monthly_gross_profit"][11] - now_gp) if now_gp is not None else None
            o["after_runway"] = False
        else:
            # without a unit cost there is no gross profit to pay costs from: the cash path stays unknown rather than counting revenue as profit
            o["cash_out_month"] = launch_cash_months(cash, burn, a["upfront_cost"], a["monthly_cost"], e["monthly_gross_profit"]) if uc is not None else None
            o["after_runway"] = runway_flag(o, runway) is not None
        e.pop("monthly_gross_profit", None)
        for s in o["scenarios"].values():
            s.pop("monthly_gross_profit", None)
    chosen = next(o for o in sim["options"] if o["id"] == sim["recommended_option"])
    if not existing and chosen.get("cash_out_month"):
        flags.append({"code": "cash_runs_out", "severity": "high", "evidence_ids": [], "assumption_keys": ["upfront_cost", "monthly_cost"],
                      "text": f"With this launch at {inr(chosen['price_inr'])}, cash runs out in month {chosen['cash_out_month']}: "
                              "today's burn plus the launch and running costs outpace its gross profit."})
    elif not existing and (flag := runway_flag(chosen, runway)):
        flags.append(flag)
    if existing and chosen.get("runway_months") is not None and runway is not None and chosen["runway_months"] < runway:
        flags.append({"code": "shorter_runway", "severity": "medium", "evidence_ids": [], "assumption_keys": [],
                      "text": f"At {inr(chosen['price_inr'])} runway goes from {runway:g} to {chosen['runway_months']:g} months."})
    if uc is not None and chosen["unit_margin_inr"] <= 0:
        flags.append({"code": "negative_unit_margin", "severity": "high", "evidence_ids": [], "assumption_keys": [],
                      "text": f"At {inr(chosen['price_inr'])} each unit costs more than it sells for ({inr(uc)})."})
    assumptions = [{"key": k, "label": ASSUMPTION_LABEL[k], "value": a[k], "origin": origin[k]}
                   for k in SHOWN if not (existing and k in ("upfront_cost", "monthly_cost", "ramp_months"))]
    return sim | {"assumptions": a, "assumption_list": assumptions, "inputs": inputs, "viability_flags": flags,
                  "sensitivity": sensitivity(m, f, a, uc, price), "existing": existing, "current_price_inr": price,
                  "runway_now_months": runway, "basis": "gross profit" if uc is not None else "revenue",
                  "price_unit": "" if p["unit"] == "one_time" else f"/{p['unit']}",
                  "label": "Scenario model, not a forecast", "product_id": str(p["id"])}


class ProductAssumptionsIn(BaseModel):
    assumptions: dict[str, float | None]  # None resets that assumption to its default


@router.put("/products/{product_id}/assumptions")
def put_product_assumptions(product_id: UUID, body: ProductAssumptionsIn, user: UserDep, conn: ConnDep) -> dict:
    p, card, comp = _product(conn, product_id, user.id)
    bad = [k for k, v in body.assumptions.items() if k not in DEFAULTS or (v is not None and v < 0)]
    if bad:
        raise HTTPException(422, {"code": "bad_assumption", "message": f"Unknown or negative: {', '.join(bad)}."})
    mine = {**(p.get("sim_assumptions") or {}), **{k: v for k, v in body.assumptions.items() if v is not None}}
    for k, v in body.assumptions.items():
        if v is None:
            mine.pop(k, None)
    conn.execute(text("update products set sim_assumptions = cast(:a as jsonb) where id = :id"), {"a": json.dumps(mine), "id": product_id})
    return product_sim(conn, *_product(conn, product_id, user.id))


def _scenarios(conn: Connection, product_id: UUID) -> list[dict]:
    rows = [dict(r) for r in conn.execute(text("""select id, created_at, assumptions, inputs, recommended_price_inr::float as recommended_price_inr, result
        from product_scenarios where product_id = :p order by created_at"""), {"p": product_id}).mappings()]
    out = []
    for i, r in enumerate(rows):
        out.append({"id": str(r["id"]), "created_at": r["created_at"].isoformat(), "recommended_price_inr": r["recommended_price_inr"],
                    "reason": r["result"].get("reason"), "flags": [f["text"] for f in r["result"].get("viability_flags", [])],
                    "changes": scenario_diff(rows[i - 1], r) if i else []})
    return list(reversed(out))


@router.post("/products/{product_id}/scenarios", status_code=201)
def save_scenario(product_id: UUID, user: UserDep, conn: ConnDep) -> list[dict]:
    sim = product_sim(conn, *_product(conn, product_id, user.id))
    conn.execute(text("""insert into product_scenarios (product_id, assumptions, inputs, recommended_price_inr, result)
        values (:p, cast(:a as jsonb), cast(:i as jsonb), :r, cast(:res as jsonb))"""),
                 {"p": product_id, "a": json.dumps(sim["assumptions"]), "i": json.dumps([{"label": x["label"], "value": x["value"]} for x in sim["inputs"]]),
                  "r": sim["recommended_price_inr"], "res": json.dumps({k: sim[k] for k in ("reason", "viability_flags", "options")})})
    return _scenarios(conn, product_id)


@router.get("/products/{product_id}/scenarios")
def list_scenarios(product_id: UUID, user: UserDep, conn: ConnDep) -> list[dict]:
    _product(conn, product_id, user.id)
    return _scenarios(conn, product_id)


@router.get("/products/{product_id}/simulation")
def get_product_simulation(product_id: UUID, user: UserDep, conn: ConnDep) -> dict:
    return product_sim(conn, *_product(conn, product_id, user.id))


class Segment(BaseModel):
    segment: str = Field(description="Who to sell this product to, in under 12 words")
    why: list[str] = Field(description="2-4 short reasons, each grounded in the evidence")
    evidence_ids: list[str] = Field(description="Ids of the evidence lines the reasons rest on")


@router.get("/products/{product_id}/segment")
def get_segment(product_id: UUID, user: UserDep, conn: ConnDep) -> dict:
    from app.modules.customers.router import customer_summary
    p, card, comp = _product(conn, product_id, user.id)
    pos, evidence = comp["position"], {}
    if pos["pct_vs_median"] is not None:
        side = "above" if pos["pct_vs_median"] >= 0 else "below"
        evidence["P1"] = {"text": f"Price {inr(float(p['price']))} is {abs(pos['pct_vs_median'])}% {side} the median {inr(pos['median'])} "
                                  f"of {pos['n']} comparable products", "source": "market"}
    themes = customer_summary(conn, p["profile_id"])["themes"][:6]
    for i, t in enumerate(themes, 1):
        evidence[f"T{i}"] = {"text": f"Customer {t['kind']}: {t['label']} ({t['count']} mentions)", "source": "customers"}
    if p.get("target_customer"):
        evidence["C1"] = {"text": f"Who this product is for, in your words: {p['target_customer']}", "source": "product"}
    elif tc := card_value(card, "target_customer"):
        evidence["C1"] = {"text": f"Target customer named at onboarding: {tc}", "source": "profile"}
    if cities := card_value(card, "india_markets"):
        evidence["C2"] = {"text": "Where it sells: " + ", ".join(cities if isinstance(cities, list) else [str(cities)]), "source": "profile"}
    out = {"segment": None, "why": [], "evidence_ids": [], "evidence": [{"id": k, **v} for k, v in evidence.items()]}
    if not evidence:
        return out | {"message": "Set a price, find comparables or collect customer reviews first."}
    try:
        seg = complete_json("product_segment", Segment, {
            "instructions": "Suggest the customer segment this product should target in India. Use only the evidence lines and cite their ids. "
                            "Cite the price line and at least two customer themes when they exist. No invented facts or numbers.",
            "product": f"{p['name']} ({p['niche'] or p['category_path'] or ''})",
            "evidence": "\n".join(f"{k}: {v['text']}" for k, v in evidence.items()),
        }, "product_segment.v1")
    except LLMUnavailable:
        return out | {"message": "The AI is busy; try again in a minute."}
    checked = checked_segment(seg.model_dump(), set(evidence))
    return out | (checked or {"message": "The suggestion didn't cite any evidence, so it was dropped."})

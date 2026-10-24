"""§4.4 launch simulator: deterministic scenario model, not a forecast."""
import re

DEFAULTS = {"segment_size": 4000, "base_conversion": 0.03, "elasticity_best": 0.8, "elasticity_expected": 1.2, "elasticity_worst": 1.8,
            "coverage_weight": 0.6, "ramp_months": 12, "upfront_cost": 500000, "monthly_cost": 150000}
SCENARIOS = ("best", "expected", "worst")


def inr(n: float) -> str:
    """Indian digit grouping: 3358585 → ₹33,58,585."""
    s = str(int(round(n)))
    head, tail = s[:-3], s[-3:]
    while len(head) > 2:
        tail, head = f"{head[-2:]},{tail}", head[:-2]
    return f"₹{head},{tail}" if head else f"₹{tail}"


def round_99(x: float) -> int:
    """Price ending in 9 at a step that fits the price: ₹1,349 → ₹1,399, ₹130 → ₹129, ₹45 → ₹44."""
    step = 100 if x >= 1000 else 10 if x >= 100 else 1
    return max(step - 1, int((x + 1) / step + 0.5) * step - 1) if step > 1 else max(1, round(x) - 1)


def propose_options(m: float, planned: float | None = None, extra: float | None = None) -> list[dict]:
    opts = [{"id": i, "price_inr": round_99(f * m), "origin": "proposed"} for i, f in (("A", 0.85), ("B", 1.0), ("C", 1.15))]
    if planned:  # your price is always a row: it replaces a proposed option within 5% of it (₹109 next to ₹110 says nothing)
        near = min(opts, key=lambda o: abs(o["price_inr"] - planned))
        if abs(near["price_inr"] - planned) / planned <= 0.05:
            near.update(price_inr=planned, origin="your planned price")
        else:
            opts.append({"id": "P", "price_inr": planned, "origin": "your planned price"})
    if extra:
        opts.append({"id": "U", "price_inr": extra, "origin": "user"})
    return opts


def conversion(p: float, m: float, f: float, c0: float, e: float, k: float) -> float:
    return min(max(c0 * (p / m) ** (-e) * (1 + k * (f - 0.5)), 0.0), 0.5)


def _customers(conv: float, month: int, a: dict) -> float:
    return a["segment_size"] * conv * min(1, month / max(a["ramp_months"], 1))


def break_even_month(p: float, conv: float, a: dict, unit_cost: float | None = None) -> int | None:
    """First month cumulative gross profit (revenue when unit cost is unknown) covers launch and running costs."""
    margin = p - unit_cost if unit_cost is not None else p
    if margin <= 0:
        return None
    cum = 0.0
    for month in range(1, 37):
        cum += margin * _customers(conv, month, a)
        if cum >= a["upfront_cost"] + a["monthly_cost"] * month:
            return month
    return None


def recommend(options: list[dict]) -> tuple[str, bool]:
    """Highest expected 12-month gross profit (revenue if unit cost is unknown) among options whose worst case breaks even;
    ties go to the lower price."""
    viable = [o for o in options if o["scenarios"]["worst"]["break_even_month"] is not None]
    pool = viable or options
    value = lambda e: e["gross_profit_12m_inr"] if e.get("gross_profit_12m_inr") is not None else e["revenue_12m_inr"]  # profit when costs are known
    best = min(pool, key=lambda o: (-value(o["scenarios"]["expected"]), o["price_inr"]))
    return best["id"], not viable


def simulate(m: float, f: float, a: dict, planned: float | None = None, extra: float | None = None, unit_cost: float | None = None) -> dict:
    options = propose_options(m, planned, extra)
    for o in options:
        o["scenarios"] = {}
        margin = o["price_inr"] - unit_cost if unit_cost is not None else None
        for s in SCENARIOS:
            conv = conversion(o["price_inr"], m, f, a["base_conversion"], a[f"elasticity_{s}"], a["coverage_weight"])
            o["scenarios"][s] = {"conversion": round(conv, 4), "customers_m12": round(_customers(conv, 12, a)),
                                 "revenue_12m_inr": round(sum(o["price_inr"] * _customers(conv, mo, a) for mo in range(1, 13))),
                                 "gross_profit_12m_inr": round(sum(margin * _customers(conv, mo, a) for mo in range(1, 13))) if margin is not None else None,
                                 "monthly_gross_profit": [round(margin * _customers(conv, mo, a)) for mo in range(1, 37)] if margin is not None else None,
                                 "break_even_month": break_even_month(o["price_inr"], conv, a, unit_cost)}
    rec, warning = recommend(options)
    chosen = next(o for o in options if o["id"] == rec)
    exp = chosen["scenarios"]["expected"]
    what = (f"gross profit ({inr(exp['gross_profit_12m_inr'])})" if exp["gross_profit_12m_inr"] is not None else f"revenue ({inr(exp['revenue_12m_inr'])})")
    reason = (f"Highest expected 12-month {what} "
              + ("among options that break even even in the worst case." if not warning else
                 "but no option breaks even in the worst case under these assumptions."))
    return {"market_median_inr": m, "feature_coverage": round(f, 2), "options": options, "recommended_option": rec,
            "recommended_price_inr": chosen["price_inr"], "reason": reason, "warning": warning}


def viability_flags(sim: dict, comparables: list[dict], inspiration: list[dict]) -> list[dict]:
    """comparables/inspiration: [{name, india_verified, reason, evidence_id}]. Each flag cites evidence and assumptions."""
    flags = []
    chosen = next(o for o in sim["options"] if o["id"] == sim["recommended_option"])
    if not any(c["india_verified"] for c in comparables):
        flags.append({"code": "no_verified_india_competitors", "severity": "medium", "evidence_ids": [], "assumption_keys": [],
                      "text": "No comparable competitor is verified as serving India, so the market price is thin evidence."})
    if len(comparables) >= 10:
        flags.append({"code": "crowded_segment", "severity": "medium", "assumption_keys": [], "evidence_ids": [c["evidence_id"] for c in comparables],
                      "text": f"{len(comparables)} comparable competitors: a crowded segment."})
    if all(o["scenarios"][s]["break_even_month"] is None for o in sim["options"] for s in SCENARIOS):
        flags.append({"code": "no_breakeven_36m", "severity": "high", "evidence_ids": [],
                      "assumption_keys": ["upfront_cost", "monthly_cost", "segment_size", "base_conversion"],
                      "text": "No break-even within 36 months under these assumptions, at any option or scenario."})
    monthly_m12 = chosen["price_inr"] * chosen["scenarios"]["expected"]["customers_m12"]
    if sim["assumptions"]["upfront_cost"] > 12 * monthly_m12:
        flags.append({"code": "capital_intensive", "severity": "high", "evidence_ids": [], "assumption_keys": ["upfront_cost"],
                      "text": f"Upfront cost ({inr(sim['assumptions']['upfront_cost'])}) is more than a year of expected revenue at month 12 "
                              f"({inr(monthly_m12)} a month)."})
    big = [c for c in inspiration if re.search(r"large|incumbent|enterprise|leader|giant", c.get("reason") or "", re.I)]
    if len(big) >= 3:
        flags.append({"code": "incumbent_heavy", "severity": "medium", "assumption_keys": [], "evidence_ids": [c["evidence_id"] for c in big],
                      "text": "Large incumbents dominate: " + "; ".join(f"{c['name']} ({c['reason']})" for c in big[:3])})
    return flags


# ---- B14i: per-product inputs from the other dashboards. They feed the formula above; they don't change it. ----

def sentiment_shift(split: dict) -> float | None:
    """Customers' net sentiment moves base conversion by at most ±20%; under 3 labelled mentions it moves nothing."""
    pos, neg, neu = (split.get(k, 0) for k in ("positive", "negative", "neutral"))
    n = pos + neg + neu
    return round(max(-0.2, min(0.2, 0.2 * (pos - neg) / n)), 3) if n >= 3 else None


def _words(s: str) -> set[str]:
    from app.modules.products.taxonomy import tokens
    return tokens(s)


def feature_coverage(mine: list[str], theirs: list[list[str]]) -> float:
    """Share of the comparables' features that share a word with one of this product's features."""
    union = list({f.lower(): f for fs in theirs for f in fs}.values())
    if not union:
        return 0.5
    own = set().union(*(_words(f) for f in mine)) if mine else set()
    return sum(bool(_words(f) & own) for f in union) / len(union)


def request_boost(f: float, mine: list[str], themes: list[dict]) -> tuple[float, list[str]]:
    """Each customer request this product already answers adds 0.05 to feature coverage (capped at 1)."""
    own = set().union(*(_words(x) for x in mine)) if mine else set()
    covered = [t["label"] for t in themes if t["kind"] == "request" and _words(t["label"]) & own]
    return round(min(1.0, f + 0.05 * len(covered)), 2), covered


def unit_cost(price: float, own: float | None, gross_margin: float | None) -> tuple[float | None, str]:
    if own is not None:
        return own, "product"
    if gross_margin is not None:
        return round(price * (1 - gross_margin)), "benchmark"
    return None, "default"


def runway_flag(option: dict, runway_months: float | None) -> dict | None:
    be = option["scenarios"]["expected"]["break_even_month"]
    if runway_months is None or (be is not None and be <= runway_months):
        return None
    return {"code": "break_even_after_runway", "severity": "high", "evidence_ids": [], "assumption_keys": [],
            "text": f"Cash lasts about {runway_months:g} months at the current burn, but this price "
                    + (f"breaks even in month {be}." if be else "doesn't break even within 36 months.")}


def calibrate_segment(units_per_month: float | None, conv_at_current: float) -> int | None:
    """Reachable customers that make today's price reproduce the units actually sold (Finance), instead of a default."""
    return round(units_per_month / conv_at_current) if units_per_month and conv_at_current > 0 else None


def runway_with(cash: float | None, burn: float | None, extra_monthly_profit: float) -> float | None:
    """Months of cash if this price changes monthly gross profit by extra_monthly_profit; None if unknown or no longer burning."""
    if cash is None or burn is None:
        return None
    new_burn = burn - extra_monthly_profit
    return round(cash / new_burn, 1) if new_burn > 0 else None


def launch_cash_months(cash: float | None, burn: float | None, upfront: float, monthly_cost: float, profits: list[float]) -> int | None:
    """New product: the month cash runs out, paying today's burn, the launch and its running cost, earning its ramping gross profit.
    None if cash is unknown or lasts the 36 months modelled."""
    if cash is None or burn is None:
        return None
    left = cash - upfront
    for month, gp in enumerate(profits[:36], 1):
        left += gp - burn - monthly_cost
        if left < 0:
            return month
    return None


ASSUMPTION_LABEL = {"segment_size": "Reachable customers", "base_conversion": "Conversion at market price", "elasticity_expected": "Price sensitivity",
                    "coverage_weight": "Weight of features", "ramp_months": "Months to reach full sales", "upfront_cost": "Launch cost",
                    "monthly_cost": "Monthly running cost", "elasticity_best": "Price sensitivity (best case)", "elasticity_worst": "Price sensitivity (worst case)"}


def _headline(sim: dict) -> tuple[int, int | None]:
    chosen = next(o for o in sim["options"] if o["id"] == sim["recommended_option"])
    e = chosen["scenarios"]["expected"]
    return chosen["price_inr"], e["gross_profit_12m_inr"] if e["gross_profit_12m_inr"] is not None else e["revenue_12m_inr"]


def sensitivity(m: float, f: float, a: dict, unit_cost: float | None, planned: float | None = None) -> list[dict]:
    """Each key assumption 20% lower and higher: the recommended price and its expected 12-month gross profit (revenue if no unit cost).
    Price sensitivity is the one that can change the answer; conversion scales every option alike, so it moves profit, not the pick."""
    base_price, _ = _headline(simulate(m, f, a, planned, unit_cost=unit_cost))
    rows = []
    cases = [("Price sensitivity", "elasticity_expected"), ("Unit cost", None), ("Conversion", "base_conversion")]
    for name, key in cases:
        if key is None and unit_cost is None:
            continue
        for change, k in (("−20%", 0.8), ("+20%", 1.2)):
            aa, uc = ({**a, key: a[key] * k}, unit_cost) if key else (a, unit_cost * k)
            price, value = _headline(simulate(m, f, aa, planned, unit_cost=uc))
            rows.append({"assumption": name, "change": change, "recommended_price_inr": price, "gross_profit_12m_inr": value,
                         "same_recommendation": price == base_price})
    return rows


def scenario_diff(prev: dict, curr: dict) -> list[str]:
    """What changed between two saved scenarios: the recommendation first, then inputs and assumptions."""
    out = []
    if prev["recommended_price_inr"] != curr["recommended_price_inr"]:
        out.append(f"Recommended {inr(prev['recommended_price_inr'])} → {inr(curr['recommended_price_inr'])}")
    before = {i["label"]: i["value"] for i in prev.get("inputs", [])}
    for i in curr.get("inputs", []):
        if i["label"] in before and before[i["label"]] != i["value"]:
            out.append(f"{i['label']}: {before[i['label']]} → {i['value']}")
        elif i["label"] not in before:
            out.append(f"New input: {i['label']}: {i['value']}")
    pa, ca = prev.get("assumptions", {}), curr.get("assumptions", {})
    for k in sorted(set(pa) | set(ca)):
        if pa.get(k) != ca.get(k):
            out.append(f"{ASSUMPTION_LABEL.get(k, k)}: {pa.get(k)} → {ca.get(k)}")
    return out


def checked_segment(seg: dict, evidence: set[str]) -> dict | None:
    """Keep a suggested segment only if it cites evidence that exists."""
    ids = [i for i in seg.get("evidence_ids", []) if i in evidence]
    return {**seg, "evidence_ids": ids} if ids and seg.get("segment") else None

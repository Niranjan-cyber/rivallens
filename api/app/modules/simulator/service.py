"""§4.4 launch simulator: deterministic scenario model, not a forecast."""
import re

DEFAULTS = {"segment_size": 4000, "base_conversion": 0.03, "elasticity_best": 0.8, "elasticity_expected": 1.2, "elasticity_worst": 1.8,
            "coverage_weight": 0.6, "ramp_months": 12, "upfront_cost": 500000, "monthly_cost": 150000}
SCENARIOS = ("best", "expected", "worst")


def round_99(x: float) -> int:
    return max(99, int((x + 1) / 100 + 0.5) * 100 - 1)


def propose_options(m: float, planned: float | None = None, extra: float | None = None) -> list[dict]:
    opts = [{"id": i, "price_inr": round_99(f * m), "origin": "proposed"} for i, f in (("A", 0.85), ("B", 1.0), ("C", 1.15))]
    if planned and abs(planned - m) / m > 0.05 and planned not in {o["price_inr"] for o in opts}:
        opts.append({"id": "P", "price_inr": planned, "origin": "your planned price"})
    if extra:
        opts.append({"id": "U", "price_inr": extra, "origin": "user"})
    return opts


def conversion(p: float, m: float, f: float, c0: float, e: float, k: float) -> float:
    return min(max(c0 * (p / m) ** (-e) * (1 + k * (f - 0.5)), 0.0), 0.5)


def _customers(conv: float, month: int, a: dict) -> float:
    return a["segment_size"] * conv * min(1, month / max(a["ramp_months"], 1))


def break_even_month(p: float, conv: float, a: dict) -> int | None:
    cum = 0.0
    for month in range(1, 37):
        cum += p * _customers(conv, month, a)
        if cum >= a["upfront_cost"] + a["monthly_cost"] * month:
            return month
    return None


def recommend(options: list[dict]) -> tuple[str, bool]:
    """Highest expected 12-month revenue among options whose worst case breaks even; ties go to the lower price."""
    viable = [o for o in options if o["scenarios"]["worst"]["break_even_month"] is not None]
    pool = viable or options
    best = min(pool, key=lambda o: (-o["scenarios"]["expected"]["revenue_12m_inr"], o["price_inr"]))
    return best["id"], not viable


def simulate(m: float, f: float, a: dict, planned: float | None = None, extra: float | None = None) -> dict:
    options = propose_options(m, planned, extra)
    for o in options:
        o["scenarios"] = {}
        for s in SCENARIOS:
            conv = conversion(o["price_inr"], m, f, a["base_conversion"], a[f"elasticity_{s}"], a["coverage_weight"])
            o["scenarios"][s] = {"conversion": round(conv, 4), "customers_m12": round(_customers(conv, 12, a)),
                                 "revenue_12m_inr": round(sum(o["price_inr"] * _customers(conv, mo, a) for mo in range(1, 13))),
                                 "break_even_month": break_even_month(o["price_inr"], conv, a)}
    rec, warning = recommend(options)
    chosen = next(o for o in options if o["id"] == rec)
    exp = chosen["scenarios"]["expected"]
    reason = (f"Highest expected 12-month revenue (₹{exp['revenue_12m_inr']:,}) "
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
                      "text": f"Upfront cost (₹{sim['assumptions']['upfront_cost']:,.0f}) is more than a year of expected revenue at month 12 "
                              f"(₹{monthly_m12:,.0f} a month)."})
    big = [c for c in inspiration if re.search(r"large|incumbent|enterprise|leader|giant", c.get("reason") or "", re.I)]
    if len(big) >= 3:
        flags.append({"code": "incumbent_heavy", "severity": "medium", "assumption_keys": [], "evidence_ids": [c["evidence_id"] for c in big],
                      "text": "Large incumbents dominate: " + "; ".join(f"{c['name']} ({c['reason']})" for c in big[:3])})
    return flags

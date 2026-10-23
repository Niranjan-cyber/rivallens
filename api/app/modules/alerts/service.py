"""C-09 prioritizer: explainable score, buckets and template alert text (specs §1 C-09)."""

MAGNITUDE = {"plan_added": 0.7, "plan_removed": 0.7, "feature_added": 0.6, "feature_removed": 0.6, "positioning_change": 0.4}
GROUP = {"price_increase": "price", "price_decrease": "price", "feature_added": "feature", "feature_removed": "feature",
         "plan_added": "plan", "plan_removed": "plan", "positioning_change": "positioning"}


def _undercut(change: dict, planned_price: float | None) -> bool:
    """A comparable plan's price moved from at/above your planned price to below it."""
    prev, curr = change.get("prev"), change.get("curr")
    if planned_price is None or not isinstance(prev, dict) or not isinstance(curr, dict):
        return False
    return prev["amount"] is not None and curr["amount"] is not None and curr["amount"] < planned_price <= prev["amount"]


def score(change: dict, relation: str, planned_price: float | None, archive: bool = False) -> tuple[int, dict]:
    if change["change_type"] in ("price_increase", "price_decrease"):
        m = min(abs(change["delta_pct"] or 0) / 50, 1)
    else:
        m = MAGNITUDE.get(change["change_type"], 0.3)
    undercut = relation == "comparable" and _undercut(change, planned_price)
    r = min((1.0 if relation == "comparable" else 0.5) + (0.2 if undercut else 0), 1.0)
    s = 0.7 if archive else 1.0
    raw = 100 * (0.5 * m + 0.35 * r + 0.15 * s)
    return int(raw + 0.5 + 1e-9), {"m": round(m, 2), "r": r, "s": s, "undercut": undercut}  # half up, float-safe


def bucket(priority: int) -> str:
    return "high" if priority >= 70 else "medium" if priority >= 40 else "low"


def alert_text(competitor: str, change: dict, prev: str | None, curr: str | None, observed: str, undercut_below: str | None = None) -> str:
    parts = change["field_path"].split(".")
    field = "headline" if parts[0] == "headline" else " ".join(parts[1:])
    delta = change.get("delta_pct")
    delta_txt = f" ({'+' if delta > 0 else '−'}{abs(delta):g}%)" if delta else ""
    note = f" · now below your planned {undercut_below}" if undercut_below else ""
    return f"{competitor} {field} {prev or 'none'} → {curr or 'none'}{delta_txt} · observed {observed}{note}"

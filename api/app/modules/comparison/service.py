"""C-10 comparison engine, pure parts: price normalization and the unknown-aware weighted score."""


def monthly_inr(price: dict | None, usd_inr: float) -> float | None:
    if not price or price.get("amount") is None or price.get("period") in ("hour", "user", "seat"):
        return None
    amount = price["amount"] * (usd_inr if price.get("currency") == "USD" else 1)
    return round(amount / 12, 2) if price.get("period") == "year" else amount


def score_rows(rows: list[dict], criteria: list[dict]) -> list[dict]:
    """score = Σ w·s / Σ w over known cells; s is min-max scaled per criterion (inverted when lower is better)."""
    active = [c for c in criteria if c["enabled"] and c["weight"] > 0 and c["direction"] != "info"]
    total = sum(c["weight"] for c in active) or 1
    ranges = {}
    for c in active:
        vals = [float(r["cells"][c["key"]]["value"]) for r in rows if r["cells"].get(c["key"], {}).get("known")]
        ranges[c["key"]] = (min(vals), max(vals)) if vals else None
    out = []
    for r in rows:
        num = known_w = 0.0
        unknown = 0
        for c in active:
            cell = r["cells"].get(c["key"], {})
            if not cell.get("known"):
                unknown += 1
                continue
            lo, hi = ranges[c["key"]]
            s = 1.0 if hi == lo else (float(cell["value"]) - lo) / (hi - lo)
            num += c["weight"] * (1 - s if c["direction"] == "lower_better" else s)
            known_w += c["weight"]
        pct = round(100 * known_w / total)
        out.append({**r, "score": round(num / known_w, 3) if known_w else None, "known_weight_pct": pct,
                    "unknown_count": unknown, "ranked": pct >= 50})
    return out

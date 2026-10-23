"""C-08 change detector: section noise rules → ledger, field diff → meaningful changes (specs §1 C-08)."""
import re

from app.modules.collector.service import normalize

CHROME = ("nav", "header", "footer", "aside")


def _lines(snap: dict, s: dict) -> list[str]:
    return snap["text"][s["start"]:s["end"]].split("\n")


def _short(text: str, n: int = 60) -> str:
    return text if len(text) <= n else text[: n - 1] + "…"


def _noise(prev: dict, curr: dict, p: dict, c: dict) -> tuple[str, str] | None:
    """Reason and summary if this changed section is noise; None if the field diff has to decide."""
    before, after = _lines(prev, p), _lines(curr, c)
    if c["landmark"] in CHROME:
        return "navigation_or_footer", "Menu order changed" if sorted(before) == sorted(after) else f"{c['landmark'].title()} text changed"
    if c["promo"]:
        return "promo_banner", f"Banner now reads “{_short(' '.join(after))}”"
    if p["raw_hash"] == c["raw_hash"]:
        return "formatting_only", "Markup or CSS classes changed; visible text is identical"
    if p["hash"] == c["hash"]:
        return "whitespace", "Only spacing or capitalisation changed"
    if sorted(before) == sorted(after):
        return "reordering", "Same lines in a different order"
    if not c["pricing"] and re.sub(r"\d", "", normalize("\n".join(before))) == re.sub(r"\d", "", normalize("\n".join(after))):
        return "dynamic_content", "Only a time, date or counter changed"
    if c["pricing"] or c["has_h1"]:
        return None
    return "outside_pricing", f"Text changed outside pricing and headline ({c['heading'] or c['key']})"


def _price_change(name: str, pp: dict, cp: dict) -> dict | None:
    field = f"plans.{name}.price"
    if pp["amount"] is None and cp["amount"] is None or (pp["amount"], pp["currency"]) == (cp["amount"], cp["currency"]):
        return None
    if cp["amount"] is None or pp["amount"] is None:  # a price disappeared (or appeared) while the page fetched fine
        kind = "price_missing" if cp["amount"] is None else "price_added"
        return {"change_type": kind, "field_path": field, "prev": pp, "curr": cp, "delta_pct": None, "status": "needs_review"}
    delta = round((cp["amount"] - pp["amount"]) / pp["amount"] * 100, 1) if pp["amount"] else None
    suspicious = pp["currency"] != cp["currency"] or (delta is not None and abs(delta) > 80)
    kind = "price_increase" if cp["amount"] > pp["amount"] else "price_decrease" if cp["amount"] < pp["amount"] else "currency_change"
    return {"change_type": kind, "field_path": field, "prev": pp, "curr": cp, "delta_pct": delta,
            "status": "needs_review" if suspicious else "confirmed"}


def _similarity(a: str, b: str) -> float:
    x, y = set(normalize(a).split()), set(normalize(b).split())
    return len(x & y) / len(x | y) if x | y else 1.0


def field_diff(prev: dict, curr: dict) -> list[dict]:
    def change(kind, field, before, after):
        return {"change_type": kind, "field_path": field, "prev": before, "curr": after, "delta_pct": None, "status": "confirmed"}

    out = []
    before = {normalize(p["name"]): p for p in prev["plans"]}
    after = {normalize(p["name"]): p for p in curr["plans"]}
    for key, p in before.items():
        if key not in after:
            out.append(change("plan_removed", f"plans.{p['name']}", p["name"], None))
    for key, c in after.items():
        p = before.get(key)
        if p is None:
            out.append(change("plan_added", f"plans.{c['name']}", None, c["name"]))
            continue
        if price := _price_change(c["name"], p["price"], c["price"]):
            out.append(price)
        out += [change("feature_added", f"plans.{c['name']}.features", None, f) for f in c["features"] if f not in p["features"]]
        out += [change("feature_removed", f"plans.{c['name']}.features", f, None) for f in p["features"] if f not in c["features"]]
    hp, hc = prev.get("headline"), curr.get("headline")
    if hp and hc and _similarity(hp["text"], hc["text"]) < 0.8:
        out.append(change("positioning_change", "headline", hp["text"], hc["text"]))
    return out


def compare(prev: dict, curr: dict) -> tuple[list[dict], list[dict]]:
    """prev/curr: {text, sections, fields}. Returns (ledger entries, changes). Every section diff lands in one of them."""
    ledger, unexplained = [], []
    prev_sections = {s["key"]: s for s in prev["sections"]}
    curr_keys = {s["key"] for s in curr["sections"]}
    for c in curr["sections"]:
        p = prev_sections.get(c["key"])
        if p is None:
            if not (c["pricing"] or c["has_h1"]):
                ledger.append({"section_key": c["key"], "reason": "outside_pricing", "summary": f"New section ({c['heading'] or c['key']})"})
            continue
        if (p["raw_hash"], p["html_hash"]) == (c["raw_hash"], c["html_hash"]):
            continue
        if noise := _noise(prev, curr, p, c):
            ledger.append({"section_key": c["key"], "reason": noise[0], "summary": noise[1]})
        else:
            unexplained.append(c)
    for key, p in prev_sections.items():
        if key not in curr_keys and not (p["pricing"] or p["has_h1"]):
            ledger.append({"section_key": key, "reason": "outside_pricing", "summary": f"Section removed ({p['heading'] or key})"})

    changes = field_diff(prev["fields"], curr["fields"])
    if not changes:  # text moved in a pricing/headline section but no tracked field did
        ledger += [{"section_key": c["key"], "reason": "no_tracked_field",
                    "summary": "Text changed, but no price, plan, feature or headline did"} for c in unexplained]
    return ledger, changes

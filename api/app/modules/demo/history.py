"""Demo history for the non-cloud profiles: fictional "(demo)" competitors with two dated checks and one receipt each profile.

Deterministic, so the seed user and every guest clone get the same story. Nothing here describes a real company.
"""
import json
from datetime import UTC, datetime, timedelta
from uuid import UUID

from sqlalchemy import Connection, text

from app.modules.collector.service import sha

INR_SIGNALS = {"score": 4, "hits": ["₹ / INR / Rs.", "India or an Indian city", "GST / GSTIN"]}


def _p(name, amount, period, features, raw=None):
    unit = {"month": "/month", "one_time": "", "year": "/year"}[period]
    return {"name": name, "price": {"amount": amount, "currency": "INR", "period": period, "raw": raw or f"₹{amount:,}{unit}"},
            "features": features, "method": "manual_seed"}


# profile name → competitors: (name, domain, relation, india_signals, headline, plans then, plans now)
DEMO_HISTORY = {
    "QuickKart": [
        ("ZipBasket (demo)", "zipbasket.demo", "comparable", INR_SIGNALS, "Groceries in 10 minutes across Bengaluru",
         [_p("Zip Pass", 99, "month", ["Free delivery over ₹199", "No surge fee"]), _p("Zip Pass Plus", 199, "month", ["Free delivery on all orders", "No surge fee", "Priority support"])],
         [_p("Zip Pass", 79, "month", ["Free delivery over ₹199", "No surge fee"]), _p("Zip Pass Plus", 199, "month", ["Free delivery on all orders", "No surge fee", "Priority support"])]),
        ("DashMart (demo)", "dashmart.demo", "comparable", INR_SIGNALS, "Your neighbourhood store, delivered",
         [_p("Dash Saver", 149, "month", ["Free delivery over ₹299", "Weekly deals"]), _p("Dash Unlimited", 249, "month", ["Free delivery on all orders", "Weekly deals", "Chat support"])],
         [_p("Dash Saver", 149, "month", ["Free delivery over ₹299", "Weekly deals"]), _p("Dash Unlimited", 249, "month", ["Free delivery on all orders", "Weekly deals", "Chat support"])]),
        ("Minute Pantry (demo)", "minutepantry.demo", "inspiration", INR_SIGNALS, "Everything for your kitchen in minutes",
         [_p("Pantry Club", 129, "month", ["Free delivery over ₹249", "Members-only prices", "Email support"])],
         [_p("Pantry Club", 129, "month", ["Free delivery over ₹249", "Members-only prices", "Email support"])]),
    ],
    "Stride & Co.": [
        ("PaceRun (demo)", "pacerun.demo", "comparable", INR_SIGNALS, "Running shoes made for Indian roads",
         [_p("Daily Trainer", 3499, "one_time", ["Breathable mesh", "30-day returns"]), _p("Tempo Racer", 5999, "one_time", ["Carbon plate", "30-day returns", "Priority support"])],
         [_p("Daily Trainer", 3499, "one_time", ["Breathable mesh", "30-day returns"]), _p("Tempo Racer", 4999, "one_time", ["Carbon plate", "30-day returns", "Priority support"])]),
        ("Trailhawk Footwear (demo)", "trailhawk.demo", "comparable", INR_SIGNALS, "Built for trails and monsoon runs",
         [_p("Trail Basic", 2999, "one_time", ["Grippy outsole"]), _p("Trail Pro", 6499, "one_time", ["Waterproof upper", "Grippy outsole", "Email support"])],
         [_p("Trail Basic", 2999, "one_time", ["Grippy outsole"]), _p("Trail Pro", 6499, "one_time", ["Waterproof upper", "Grippy outsole", "Email support"])]),
        ("Urban Sole (demo)", "urbansole.demo", "inspiration", INR_SIGNALS, "Everyday sneakers, made in India",
         [_p("City Walker", 1999, "one_time", ["Cushioned insole", "Free exchanges"])],
         [_p("City Walker", 1999, "one_time", ["Cushioned insole", "Free exchanges"])]),
    ],
    "Qubit Labs": [  # no India signals on purpose: the idea's "no verified India competitors" flag is real for this market
        ("QCloud Access (demo)", "qcloud.demo", "comparable", {}, "Quantum processors by the hour, from anywhere",
         [_p("Researcher", 180000, "month", ["Simulator access", "10 QPU hours"]), _p("Lab", 450000, "month", ["Simulator access", "40 QPU hours", "Research support"])],
         [_p("Researcher", 180000, "month", ["Simulator access", "10 QPU hours"]), _p("Lab", 450000, "month", ["Simulator access", "40 QPU hours", "Research support"])]),
        ("Qubitly (demo)", "qubitly.demo", "comparable", {}, "Quantum computing for enterprise R&D",
         [_p("Starter", 120000, "month", ["Simulator access"]), _p("Team", 300000, "month", ["Simulator access", "Hosted quantum processor time"])],
         [_p("Starter", 120000, "month", ["Simulator access"]), _p("Team", 300000, "month", ["Simulator access", "Hosted quantum processor time"])]),
    ],
}


def _page_text(name: str, headline: str, plans: list[dict]) -> str:
    lines = ["Demo data: fictional company. Not a real business.", name.removesuffix(" (demo)"), headline, "Pricing"]
    for p in plans:
        lines += [p["name"], p["price"]["raw"], *p["features"]]
    return "\n".join(lines)


def seed_history(conn: Connection, profile_id: UUID, profile_name: str) -> None:
    """Creates competitors, sources, two runs (baseline 10 days ago, check 2 days ago), snapshots, observations and receipts."""
    comps = DEMO_HISTORY.get(profile_name)
    if not comps:
        return
    now = datetime.now(UTC)
    t0, t1 = now - timedelta(days=10), now - timedelta(days=2)
    runs = [conn.execute(text("insert into runs (profile_id, kind, status, started_at, finished_at, counts) values (:p, :k, 'done', :t, :t, cast(:c as jsonb)) returning id"),
                         {"p": profile_id, "k": k, "t": t, "c": json.dumps({"sources": len(comps), "diffs": 0, "ignored": 0, "meaningful": 0, "needs_review": 0, "failed": 0})}).scalar()
            for k, t in (("baseline", t0), ("run", t1))]
    meaningful = 0
    for name, domain, relation, signals, headline, before, after in comps:
        cid = conn.execute(text("""insert into competitors (profile_id, name, domain, relation, origin, is_demo_data, india_signals)
            values (:p, :n, :d, :r, 'seed', true, cast(:i as jsonb)) returning id"""),
            {"p": profile_id, "n": name, "d": domain, "r": relation, "i": json.dumps(signals)}).scalar()
        sid = conn.execute(text("insert into sources (competitor_id, url, page_type, is_mock) values (:c, :u, 'pricing', false) returning id"),
                           {"c": cid, "u": f"https://{domain}/pricing"}).scalar()
        snaps = []
        for run_id, t, plans in ((runs[0], t0, before), (runs[1], t1, after)):
            body = _page_text(name, headline, plans)
            fields = {"plans": plans, "headline": {"text": headline, "method": "manual_seed"}, "extraction_status": "ok"}
            snap = conn.execute(text("""insert into snapshots (source_id, run_id, observed_at, status, http_status, sha256, text, sections, bytes)
                values (:s, :r, :t, 'ok', 200, :h, :x, '[]'::jsonb, :b) returning id"""),
                {"s": sid, "r": run_id, "t": t, "h": sha(body), "x": body, "b": len(body)}).scalar()
            conn.execute(text("insert into observations (snapshot_id, source_id, observed_at, fields, origin) values (:i, :s, :t, cast(:f as jsonb), 'seed')"),
                         {"i": snap, "s": sid, "t": t, "f": json.dumps(fields)})
            snaps.append((snap, t, body))
        for b, a in zip(before, after):
            if b["price"]["amount"] == a["price"]["amount"]:
                continue
            delta = round((a["price"]["amount"] - b["price"]["amount"]) / b["price"]["amount"] * 100, 1)
            excerpt = {side: {"start": text_.find(p["price"]["raw"]), "end": text_.find(p["price"]["raw"]) + len(p["price"]["raw"])}
                       for side, text_, p in (("before", snaps[0][2], b), ("after", snaps[1][2], a))}
            conn.execute(text("""
                insert into change_events (run_id, source_id, competitor_id, change_type, field_path, prev_value, curr_value, delta_pct, status,
                    before_snapshot_id, after_snapshot_id, excerpt, observed_at, prev_observed_at, fingerprint, is_demo_data)
                values (:r, :s, :c, :t, :f, cast(:pv as jsonb), cast(:cv as jsonb), :d, 'confirmed', :b, :a, cast(:ex as jsonb), :o, :po, :fp, true)
            """), {"r": runs[1], "s": sid, "c": cid, "t": "price_decrease" if delta < 0 else "price_increase", "f": f"plans.{a['name']}.price",
                   "pv": json.dumps(b["price"]), "cv": json.dumps(a["price"]), "d": delta, "b": snaps[0][0], "a": snaps[1][0],
                   "ex": json.dumps(excerpt), "o": t1, "po": t0, "fp": sha(f"{cid}|{a['name']}|{a['price']['amount']}")[:32]})
            meaningful += 1
    conn.execute(text("update runs set counts = counts || cast(:c as jsonb) where id = :r"),
                 {"c": json.dumps({"diffs": meaningful, "meaningful": meaningful}), "r": runs[1]})

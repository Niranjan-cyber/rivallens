"""Milestone 1: the setup plan (steps, coverage, findings, one next action) from what the business has collected."""
from app.modules.setup.service import plan

BASE = "/app/p1"


def state(**over):
    s = {
        "card": {"target_customer": "Home coffee drinkers", "markets": ["Bengaluru"]},
        "products": [{"id": "a", "name": "Filter coffee powder", "price": None, "unit": "one_time", "category_path": "Food > Beverages > Coffee",
                      "niche": "Filter coffee powder", "like_for_like": 0, "broad": 0, "position": None, "sources": [], "seen": None}],
        "discovery": None, "competitors": {"selected": 0, "total": 0},
        "monitoring": {"baseline_at": None, "last_run_at": None, "failed": []}, "receipt": None,
        "money": {"transactions": 0, "has_costs": False, "runway_months": None},
        "customers": {"total": 0, "complaint": None},
    }
    return s | over


def step(p, key):
    return next(s for s in p["steps"] if s["key"] == key)


def test_new_business_is_asked_for_its_price_first():
    p = plan(state(), BASE)
    assert step(p, "business")["status"] == "done"
    assert step(p, "products")["status"] == "todo"
    assert p["next_action"]["kind"] == "price" and p["next_action"]["product_id"] == "a"
    assert p["findings"] == []


def test_discovery_that_verified_nothing_explains_why_and_moves_on():
    s = state(discovery={"status": "done", "verified": 0, "rejected": 6, "reasons": ["no India signals", "robots.txt disallows"], "error": None})
    s["products"][0]["price"] = 450
    p = plan(s, BASE)
    comp = step(p, "competitors")
    assert comp["status"] == "blocked" and "no India signals" in comp["detail"] and comp["action"]["href"] == f"{BASE}/competitors"
    assert p["next_action"]["key"] == "comparables"


def test_broad_category_matches_are_not_a_price_position():
    s = state()
    s["products"][0] |= {"price": 450, "broad": 4, "like_for_like": 0}
    p = plan(s, BASE)
    assert "not filter coffee powder" in step(p, "comparables")["detail"].lower()
    assert p["findings"] == []
    assert any(c["area"] == "Products" and c["status"] == "missing" for c in p["coverage"])


def test_like_for_like_prices_give_a_finding_with_evidence_and_an_action():
    s = state()
    s["products"][0] |= {"price": 300, "like_for_like": 5, "position": {"median": 500, "pct_vs_median": -40, "n": 5},
                         "sources": ["bluetokaicoffee.com", "sleepyowl.co"], "seen": "2026-10-24"}
    p = plan(s, BASE)
    f = p["findings"][0]
    assert "40% below" in f["text"] and "5 like-for-like" in f["text"]
    assert f["evidence"]["href"] == f"{BASE}/product-detail?id=a"
    assert "higher price" in f["action"]["label"]


def test_short_runway_is_the_first_finding_and_needs_costs():
    s = state(money={"transactions": 40, "has_costs": True, "runway_months": 3.5},
              receipt={"id": "r1", "text": "Blue Tokai price ₹500 → ₹450", "observed_at": "2026-10-20"})
    p = plan(s, BASE)
    assert p["findings"][0]["kind"] == "runway" and p["findings"][1]["kind"] == "receipt"
    assert p["findings"][1]["evidence"]["href"] == f"{BASE}/receipt?id=r1"
    no_costs = plan(state(money={"transactions": 40, "has_costs": False, "runway_months": None}), BASE)
    assert not any(f["kind"] == "runway" for f in no_costs["findings"])
    assert step(no_costs, "finance")["status"] == "optional" and "cost" in step(no_costs, "finance")["detail"].lower()


def test_monitoring_waits_for_competitors_and_reports_failed_pages():
    assert step(plan(state(), BASE), "monitoring")["status"] == "blocked"
    s = state(competitors={"selected": 3, "total": 4}, monitoring={"baseline_at": "2026-10-24", "last_run_at": "2026-10-24", "failed": ["Zepto"]})
    m = step(plan(s, BASE), "monitoring")
    assert m["status"] == "done" and "Zepto" in m["detail"]
    assert any(c["area"] == "Market" and c["status"] == "failed" for c in plan(s, BASE)["coverage"])


def test_when_setup_is_done_the_next_action_is_the_top_finding():
    s = state(competitors={"selected": 3, "total": 3}, monitoring={"baseline_at": "2026-10-24", "last_run_at": "2026-10-24", "failed": []})
    s["products"][0] |= {"price": 300, "like_for_like": 5, "position": {"median": 500, "pct_vs_median": -40, "n": 5}, "sources": ["a.com"], "seen": "2026-10-24"}
    p = plan(s, BASE)
    assert all(st["status"] in ("done", "optional") for st in p["steps"])
    assert p["next_action"]["href"] == p["findings"][0]["action"]["href"]


def test_a_huge_gap_is_flagged_for_checking_not_concluded():
    s = state()
    s["products"][0] |= {"price": 155, "like_for_like": 10, "position": {"median": 549, "pct_vs_median": -72, "n": 10}, "sources": ["winni.in"], "seen": "x"}
    f = plan(s, BASE)["findings"][0]
    assert f["kind"] == "check" and "below" not in f["text"] and "no conclusion" in f["text"]


def test_after_searching_every_product_the_step_explains_and_moves_on():
    s = state(competitors={"selected": 2, "total": 2})
    s["products"][0] |= {"price": 450, "broad": 6, "searched": {"stores": 5, "pages_read": 12}}
    p = plan(s, BASE)
    c = step(p, "comparables")
    assert c["status"] == "blocked" and "12 product pages from 5 stores" in c["detail"]
    assert p["next_action"]["kind"] == "monitor"

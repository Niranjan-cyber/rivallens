"""C-09 priority score (specs §1 C-09): score = round(100 × (0.5·m + 0.35·r + 0.15·s))."""
from app.modules.alerts.service import alert_text, bucket, score

INR = lambda a: {"amount": a, "currency": "INR", "period": "month", "raw": f"₹{a}"}  # noqa: E731


def change(kind, prev=None, curr=None, delta=None, field="plans.Pro.price"):
    return {"change_type": kind, "field_path": field, "prev": prev, "curr": curr, "delta_pct": delta}


def test_price_cut_that_undercuts_your_planned_price_is_high():
    p, b = score(change("price_decrease", INR(1499), INR(899), -40.0), relation="comparable", planned_price=999)
    assert (p, bucket(p)) == (90, "high")  # m=0.8, r=1.0 (+0.2 capped), s=1.0
    assert b == {"m": 0.8, "r": 1.0, "s": 1.0, "undercut": True}


def test_small_price_move_is_medium_and_inspiration_counts_half():
    assert score(change("price_increase", INR(1000), INR(1100), 10.0), "comparable", 999)[0] == 60
    p, b = score(change("positioning_change", "Old pitch", "New pitch", field="headline"), "inspiration", None)
    assert (p, bucket(p), b["undercut"]) == (53, "medium", False)  # 52.5 rounds half up


def test_feature_and_plan_magnitudes():
    assert score(change("feature_added", None, "Mumbai region", field="plans.Pro.features"), "comparable", None)[0] == 80
    assert score(change("plan_removed", "Pro", None, field="plans.Pro"), "comparable", None)[0] == 85


def test_alert_text_is_a_template():
    text = alert_text("NimbusDeploy (demo)", change("price_decrease", INR(1499), INR(899), -40.0), "₹1,499/month", "₹899/month",
                      "23 Oct 2026", undercut_below="₹999")
    assert text == "NimbusDeploy (demo) Pro price ₹1,499/month → ₹899/month (−40%) · observed 23 Oct 2026 · now below your planned ₹999"

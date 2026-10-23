"""§4.4 launch simulator, hand-computed cases."""
from app.modules.simulator.service import DEFAULTS, break_even_month, conversion, propose_options, recommend, round_99, simulate, viability_flags


def test_round_99_and_proposed_options():
    assert (round_99(1146.65), round_99(1349), round_99(1551.35)) == (1099, 1399, 1599)
    assert [o["price_inr"] for o in propose_options(1349, planned=999)] == [1099, 1399, 1599, 999]  # P added: 999 is >5% off
    assert [o["id"] for o in propose_options(1049, planned=1049)] == ["A", "B", "C"]  # planned ≈ B, no P


def test_conversion_is_c0_at_market_price_and_half_coverage():
    assert conversion(1000, 1000, 0.5, c0=0.03, e=1.2, k=0.6) == 0.03
    assert round(conversion(500, 1000, 0.5, c0=0.03, e=1.0, k=0.6), 4) == 0.06  # half price, unit elasticity → double
    assert conversion(1, 1000, 1.0, c0=0.03, e=1.8, k=0.6) == 0.5  # clamped


def test_break_even_month():
    a = {**DEFAULTS, "segment_size": 100, "ramp_months": 1, "upfront_cost": 5000}
    # 100 accounts × 10% = 10 customers × ₹1,000 = ₹10,000 a month from month 1
    assert break_even_month(1000, 0.1, {**a, "monthly_cost": 0}) == 1
    assert break_even_month(1000, 0.1, {**a, "monthly_cost": 9000}) == 5  # 10000m ≥ 5000 + 9000m
    assert break_even_month(1000, 0.1, {**a, "monthly_cost": 10000}) is None


def test_recommendation_prefers_viable_worst_case_then_lower_price_on_ties():
    opts = [{"id": "A", "price_inr": 900, "scenarios": {"expected": {"revenue_12m_inr": 100}, "worst": {"break_even_month": None}}},
            {"id": "B", "price_inr": 1000, "scenarios": {"expected": {"revenue_12m_inr": 90}, "worst": {"break_even_month": 20}}},
            {"id": "C", "price_inr": 1100, "scenarios": {"expected": {"revenue_12m_inr": 90}, "worst": {"break_even_month": 30}}}]
    assert recommend(opts)[0] == "B"  # A earns most but never breaks even in the worst case; B beats C on the tie by price
    no_viable = [{**o, "scenarios": {**o["scenarios"], "worst": {"break_even_month": None}}} for o in opts]
    best, warning = recommend(no_viable)
    assert (best, warning) == ("A", True)


def test_flags_fire_for_an_unfundable_idea():
    a = {**DEFAULTS, "segment_size": 50, "upfront_cost": 5_00_00_000, "monthly_cost": 20_00_000}
    sim = {**simulate(50000, 0.5, a, planned=50000), "assumptions": a}
    codes = {f["code"] for f in viability_flags(sim, comparables=[], inspiration=[])}
    assert {"no_breakeven_36m", "capital_intensive", "no_verified_india_competitors"} <= codes

"""§4.4 launch simulator, hand-computed cases."""
from app.modules.simulator.service import DEFAULTS, break_even_month, conversion, propose_options, recommend, round_99, simulate, viability_flags


def test_round_99_and_proposed_options():
    assert (round_99(1146.65), round_99(1349), round_99(1551.35)) == (1099, 1399, 1599)
    assert [o["price_inr"] for o in propose_options(1349, planned=999)] == [1099, 1399, 1599, 999]  # P added: 999 is >5% off
    assert [o["id"] for o in propose_options(1049, planned=1049)] == ["A", "B", "C"]  # planned ≈ B, no P
    # under ₹1,000 the step is ₹10, so a ₹130 brownie gets three distinct options, not ₹99 twice
    assert [o["price_inr"] for o in propose_options(130)] == [109, 129, 149]
    assert round_99(45) == 44 and round_99(5) == 4


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


def test_zero_ramp_is_treated_as_immediate():
    assert break_even_month(1000, 0.1, {**DEFAULTS, "segment_size": 100, "ramp_months": 0, "upfront_cost": 5000, "monthly_cost": 0}) == 1


def test_indian_digit_grouping():
    from app.modules.simulator.service import inr
    assert (inr(999), inr(1499), inr(3358585), inr(50000000)) == ("₹999", "₹1,499", "₹33,58,585", "₹5,00,00,000")


# ---- B14i: per-product inputs from Money, Customers and Market ----
from app.modules.simulator.service import checked_segment, feature_coverage, request_boost, runway_flag, sentiment_shift, unit_cost


def test_sentiment_shift_is_bounded_and_needs_three_labelled_mentions():
    assert sentiment_shift({"positive": 1, "negative": 1}) is None  # too few to move anything
    assert sentiment_shift({"positive": 3, "negative": 1, "neutral": 1, "unrated": 9}) == 0.08  # 0.2 × (3 − 1) / 5
    assert sentiment_shift({"negative": 10}) == -0.2
    assert sentiment_shift({"positive": 10}) == 0.2


def test_feature_coverage_by_shared_words():
    assert feature_coverage(["Cushioned midsole", "Breathable mesh"], [["EVA cushioning midsole"], ["Rubber outsole", "breathable mesh upper"]]) == 2 / 3
    assert feature_coverage(["anything"], []) == 0.5  # nothing to compare against


def test_requests_the_product_covers_raise_coverage():
    themes = [{"label": "Wider sizes", "kind": "request"}, {"label": "Mesh that breathes", "kind": "request"},
              {"label": "Breathable mesh", "kind": "praise"}]
    f, covered = request_boost(0.5, ["Breathable mesh upper"], themes)
    assert (f, covered) == (0.55, ["Mesh that breathes"])
    assert request_boost(0.98, ["mesh"], themes)[0] == 1.0


def test_unit_cost_prefers_the_product_then_the_industry_margin():
    assert unit_cost(1999, 800, 0.5) == (800, "product")
    assert unit_cost(2000, None, 0.535) == (930, "benchmark")
    assert unit_cost(2000, None, None) == (None, "default")


def test_runway_flag_when_break_even_is_later_than_runway():
    opt = {"scenarios": {"expected": {"break_even_month": 9}}}
    assert runway_flag(opt, 4.5)["code"] == "break_even_after_runway"
    assert runway_flag(opt, 12) is None
    assert runway_flag(opt, None) is None  # profitable or no cash entered
    assert runway_flag({"scenarios": {"expected": {"break_even_month": None}}}, 30)["severity"] == "high"


def test_segment_must_cite_existing_evidence():
    ev = {"E1", "E2", "E3"}
    assert checked_segment({"segment": "Weekend runners", "why": ["a"], "evidence_ids": ["E1", "E9"]}, ev)["evidence_ids"] == ["E1"]
    assert checked_segment({"segment": "Anyone", "why": [], "evidence_ids": ["E7"]}, ev) is None


# ---- Workstream 4: the model checks out against hand-worked numbers ----
from app.modules.simulator.service import calibrate_segment, launch_cash_months, runway_with, scenario_diff, sensitivity


def test_break_even_counts_gross_profit_when_unit_cost_is_known():
    a = {**DEFAULTS, "segment_size": 1000, "ramp_months": 1, "upfront_cost": 10000, "monthly_cost": 0}
    # 1000 × 10% = 100 units a month. Revenue: ₹100 × 100 = ₹10,000 → month 1. Gross profit at unit cost ₹60: ₹4,000 → month 3.
    assert break_even_month(100, 0.10, a) == 1
    assert break_even_month(100, 0.10, a, unit_cost=60) == 3
    assert break_even_month(100, 0.10, a, unit_cost=100) is None  # no margin, never


def test_existing_product_is_calibrated_to_its_real_sales():
    # 300 units a month at today's price, model conversion 3% there → a reachable segment of 10,000
    assert calibrate_segment(300, 0.03) == 10000
    assert calibrate_segment(None, 0.03) is None and calibrate_segment(300, 0) is None


def test_runway_moves_with_the_change_in_monthly_gross_profit():
    # ₹6 L cash, ₹1 L burn: 6 months. A price that earns ₹20,000 more a month → burn ₹80,000 → 7.5 months.
    assert runway_with(600000, 100000, 20000) == 7.5
    assert runway_with(600000, 100000, -50000) == 4.0
    assert runway_with(600000, 100000, 150000) is None  # stops burning
    assert runway_with(None, 100000, 0) is None and runway_with(600000, None, 0) is None


def test_launch_cash_path_month_by_month():
    # ₹3 L cash, ₹50k burn, ₹1 L launch, ₹20k a month to run, gross profit 10k, 20k, 30k…
    profits = [10000 * m for m in range(1, 37)]
    # cash after launch 2,00,000; month m spends 70,000 and earns 10,000m: 1.4 L, 0.9 L, 0.5 L, 0.2 L, 0, then −10,000 → out in month 6
    assert launch_cash_months(300000, 50000, 100000, 20000, profits) == 6
    assert launch_cash_months(300000, 0, 0, 0, profits) is None  # never runs out within 36 months
    assert launch_cash_months(300000, 50000, 100000, 20000, [0] * 36) == 3  # 2,00,000 / 70,000 → out during month 3
    assert launch_cash_months(None, 50000, 0, 0, [0] * 36) is None


def test_sensitivity_reports_whether_the_recommendation_holds():
    a = {**DEFAULTS, "ramp_months": 1, "upfront_cost": 0, "monthly_cost": 0}
    rows = sensitivity(1000, 0.5, a, unit_cost=400)
    names = [r["assumption"] for r in rows]
    assert names == ["Price sensitivity", "Price sensitivity", "Unit cost", "Unit cost", "Conversion", "Conversion"]
    assert {r["change"] for r in rows} == {"−20%", "+20%"}
    assert all("recommended_price_inr" in r and "gross_profit_12m_inr" in r and "same_recommendation" in r for r in rows)
    assert len(sensitivity(1000, 0.5, a, unit_cost=None)) == 4  # no unit cost, nothing to vary


def test_scenario_diff_says_what_changed_and_why():
    prev = {"assumptions": {"base_conversion": 0.03}, "inputs": [{"label": "Market price (median)", "value": "₹3,249"}], "recommended_price_inr": 2999}
    curr = {"assumptions": {"base_conversion": 0.04}, "inputs": [{"label": "Market price (median)", "value": "₹3,024"}], "recommended_price_inr": 2799}
    d = scenario_diff(prev, curr)
    assert "Recommended ₹2,999 → ₹2,799" in d[0]
    assert any("Market price (median): ₹3,249 → ₹3,024" in x for x in d) and any("Conversion at market price" in x for x in d)
    assert scenario_diff(curr, curr) == []


def test_recommendation_maximises_gross_profit_when_unit_cost_is_known():
    a = {**DEFAULTS, "ramp_months": 1, "upfront_cost": 0, "monthly_cost": 0}
    by_revenue = simulate(1000, 0.5, a)
    by_profit = simulate(1000, 0.5, a, unit_cost=800)
    # elasticity 1.2 > 1: the cheapest option has the most revenue, but at ₹800 a unit its margin is thin
    assert by_revenue["recommended_price_inr"] < by_profit["recommended_price_inr"]
    assert "gross profit" in by_profit["reason"]


def test_your_price_replaces_a_proposed_option_within_5_percent():
    opts = propose_options(130, planned=110)
    assert [o["price_inr"] for o in opts] == [110, 129, 149] and opts[0]["origin"] == "your planned price"

"""B14f: competitors' revenue and funding, only as quoted by a source."""
from app.modules.money.facts import amount_inr, verified


def test_amounts_as_news_writes_them():
    assert amount_inr("₹1,774.1 crore") == 17_741_000_000
    assert amount_inr("Rs 210 Cr") == 2_100_000_000
    assert amount_inr("INR 45 lakh") == 4_500_000
    assert amount_inr("$20 million") == 1_680_000_000  # at ₹84/$ like the rest of the app
    assert amount_inr("USD 1.5 Mn") == 126_000_000
    assert amount_inr("revenue of INR 343.3 Crores for the quarter") == 3_433_000_000
    assert amount_inr("PAT was at INR 22.2 Crin Q1 FY26") == 222_000_000  # "Crin": a typo in the company's own press release
    assert amount_inr("raised $48.8M over 4 rounds") == 4_099_200_000
    assert amount_inr("revenue grew 11%") is None


def test_a_fact_must_be_quoted_from_its_source_and_match_the_amount():
    source = "Campus Activewear's revenue from operations rose 11.4% to Rs 1,774.1 crore in FY26."
    assert verified({"kind": "revenue", "period": "FY26", "quote": "revenue from operations rose 11.4% to Rs 1,774.1 crore", "amount_inr": 17_741_000_000}, source)
    assert not verified({"quote": "revenue rose to Rs 2,000 crore", "amount_inr": 20_000_000_000}, source)  # not in the text
    assert not verified({"quote": "to Rs 1,774.1 crore in FY26", "amount_inr": 1_774_100}, source)  # amount doesn't match the quote


def test_comparison_figures_and_undated_results_are_dropped():
    src = "Revenue climbed to Rs 385 crore in Q1 FY27, up 12.2 per cent from Rs 343.4 crore in the corresponding period last year."
    assert verified({"kind": "revenue", "period": "Q1 FY27", "quote": "Revenue climbed to Rs 385 crore in Q1 FY27", "amount_inr": 3_850_000_000}, src)
    assert not verified({"kind": "revenue", "period": "Q1 FY26", "quote": "from Rs 343.4 crore in the corresponding period last year", "amount_inr": 3_434_000_000}, src)
    assert not verified({"kind": "revenue", "period": None, "quote": "Revenue climbed to Rs 385 crore", "amount_inr": 3_850_000_000}, src)
    assert verified({"kind": "funding", "period": None, "quote": "raised $48.8M over 4 rounds", "amount_inr": 4_099_200_000}, "Campus has raised $48.8M over 4 rounds.")


def test_from_amount_alone_is_a_comparison():
    src = "Net profit rose to Rs 26.1 crore in Q1 FY27 from Rs 22.2 crore."
    assert not verified({"kind": "profit", "period": "Q1 FY27", "quote": "from Rs 22.2 crore", "amount_inr": 222_000_000}, src)

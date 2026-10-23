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
    assert verified({"quote": "revenue from operations rose 11.4% to Rs 1,774.1 crore", "amount_inr": 17_741_000_000}, source)
    assert not verified({"quote": "revenue rose to Rs 2,000 crore", "amount_inr": 20_000_000_000}, source)  # not in the text
    assert not verified({"quote": "to Rs 1,774.1 crore in FY26", "amount_inr": 1_774_100}, source)  # amount doesn't match the quote

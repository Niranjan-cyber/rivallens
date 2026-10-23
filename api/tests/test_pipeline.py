"""Monitoring pipeline at its three seams: split_sections → extract → compare (specs §1 C-06, C-07, C-08)."""
from pathlib import Path

from app.modules.collector.service import split_sections
from app.modules.changes.service import compare
from app.modules.extractor.service import extract, parse_price

FIXTURES = Path(__file__).resolve().parents[2] / "fixtures"


def mock(variant: str) -> str:
    return (FIXTURES / "mock-pages" / f"nimbusdeploy-{variant}.html").read_text(encoding="utf-8")


def test_splitter_finds_landmarks_banner_and_main_sections():
    text, sections = split_sections(mock("v1"))
    by_key = {s["key"]: s for s in sections}
    assert set(by_key) == {"aside", "nav", "banner", "main#hero", "main#pricing", "main#faq", "footer"}
    assert by_key["main#pricing"]["pricing"] and not by_key["main#faq"]["pricing"]
    assert by_key["banner"]["promo"]
    pricing = by_key["main#pricing"]
    assert "₹1,499 /month" in text[pricing["start"]:pricing["end"]]
    assert "<script" not in text and "body{" not in text
    assert [s["key"] for s in sections] == ["aside", "nav", "banner", "main#hero", "main#pricing", "main#faq", "footer"]


def fields(variant: str) -> dict:
    return extract(mock(variant))


def test_rules_extract_plans_prices_features_and_headline():
    f = fields("v1")
    plans = {p["name"]: p for p in f["plans"]}
    assert list(plans) == ["Starter", "Pro", "Business"]
    assert plans["Pro"]["price"] == {"amount": 1499.0, "currency": "INR", "period": "month", "raw": "₹1,499 /month"}
    assert "Autoscaling" in plans["Pro"]["features"]
    assert f["headline"]["text"] == "Ship Node, Python and Go apps from Git in minutes."
    assert f["extraction_status"] == "ok"


def test_price_rule_keeps_plan_prices_and_drops_marketing_numbers_from_real_pages():
    assert parse_price("₹1,499 /month") == {"amount": 1499.0, "currency": "INR", "period": "month", "raw": "₹1,499 /month"}
    assert parse_price("H100 from $7.99/hr")["period"] == "hour"  # E2E Networks served USD to India
    # Verbatim lines from fixtures/pricing-pages (DigitalOcean, Railway)
    assert parse_price("benefits of $2.37 million over three years versus costs of $829,000") is None
    assert parse_price("$1,000 - $4,999 per month") is not None  # a bare range is still a price...
    assert parse_price("What's your current monthly infrastructure spend? $1,000 - $4,999 per month") is None  # ...in a spend survey it isn't
    assert parse_price("Contact sales") is None


def snap(variant: str) -> dict:
    html = mock(variant)
    text, sections = split_sections(html)
    return {"text": text, "sections": sections, "fields": extract(html)}


def test_cosmetic_redesign_is_all_noise_with_a_reason_per_diff():
    ledger, changes = compare(snap("v1"), snap("cosmetic"))
    assert changes == []
    assert {(e["section_key"], e["reason"]) for e in ledger} == {
        ("nav", "navigation_or_footer"), ("banner", "promo_banner"),
        ("main#pricing", "formatting_only"), ("main#hero", "dynamic_content"),
    }
    assert all(e["summary"] for e in ledger)


def test_price_cut_is_one_meaningful_price_decrease():
    ledger, changes = compare(snap("cosmetic"), snap("cosmetic_price_cut_40"))
    assert ledger == []
    [c] = changes
    assert (c["change_type"], c["field_path"], c["status"]) == ("price_decrease", "plans.Pro.price", "confirmed")
    assert (c["prev"]["amount"], c["curr"]["amount"], c["delta_pct"]) == (1499.0, 899.0, -40.0)


def test_feature_and_positioning_changes():
    [c] = compare(snap("v1"), snap("add_feature"))[1]
    assert (c["change_type"], c["field_path"], c["curr"]) == ("feature_added", "plans.Pro.features", "Mumbai region")
    [c] = compare(snap("v1"), snap("positioning"))[1]
    assert c["change_type"] == "positioning_change"


def test_identical_page_has_no_diffs():
    assert compare(snap("v1"), snap("v1")) == ([], [])


def test_suspicious_price_changes_need_review():
    prev = snap("v1")
    curr = snap("cosmetic_price_cut_40")
    curr["fields"]["plans"][1]["price"] = {"amount": 99.0, "currency": "INR", "period": "month", "raw": "₹99 /month"}  # −93%
    assert compare(prev, curr)[1][0]["status"] == "needs_review"
    curr["fields"]["plans"][1]["price"] = {"amount": None, "currency": None, "period": None, "raw": None}  # price vanished
    assert compare(prev, curr)[1][0]["status"] == "needs_review"

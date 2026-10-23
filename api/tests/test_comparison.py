"""C-10 comparison seams: price normalization and the unknown-aware weighted score (specs §1 C-10)."""
from app.modules.comparison.service import monthly_inr, score_rows

CRIT = [{"key": "price", "weight": 3, "direction": "lower_better", "enabled": True},
        {"key": "features", "weight": 1, "direction": "higher_better", "enabled": True}]


def row(name, price=None, features=None):
    cells = {"price": {"value": price, "known": price is not None}, "features": {"value": features, "known": features is not None}}
    return {"name": name, "cells": cells}


def test_normalizes_usd_and_yearly_to_inr_per_month():
    assert monthly_inr({"amount": 12, "currency": "USD", "period": "year"}, usd_inr=84) == 84.0
    assert monthly_inr({"amount": 999, "currency": "INR", "period": "month"}, usd_inr=84) == 999
    assert monthly_inr({"amount": 2, "currency": "USD", "period": "hour"}, usd_inr=84) is None  # hourly isn't a monthly price


def test_unknown_cells_never_count_against_anyone():
    rows = score_rows([row("cheap", 500, 3), row("dear", 1500, 3), row("mystery", None, 9)], CRIT)
    by = {r["name"]: r for r in rows}
    assert by["cheap"]["score"] > by["dear"]["score"]
    assert (by["mystery"]["unknown_count"], by["mystery"]["known_weight_pct"], by["mystery"]["ranked"]) == (1, 25, False)
    assert by["mystery"]["score"] == 1.0  # scored only on what is known


def test_weight_zero_changes_the_ranking():
    rows = [row("cheap", 500, 2), row("rich", 900, 8)]
    first = lambda crit: max(score_rows(rows, crit), key=lambda r: r["score"])["name"]  # noqa: E731
    assert first(CRIT) == "cheap"
    assert first([{**CRIT[0], "weight": 0}, CRIT[1]]) == "rich"

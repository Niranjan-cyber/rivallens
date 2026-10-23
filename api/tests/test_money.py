"""B14e Money: uploads (bank, payment, retail exports) → transactions → revenue, margin, burn, runway."""
from datetime import date

from app.modules.money.service import benchmark, metrics, parse_amount, parse_date, parse_table, suggest_mapping, to_transactions

UCI = b"""Invoice,StockCode,Description,Quantity,InvoiceDate,Price,Customer ID,Country
489434,85048,STRIDE RUNNER,2,01/12/2025 07:45,1999.00,13085,India
489434,79323P,RUNNING SOCKS,6,01/12/2025 07:45,299.00,13085,India
C489449,85048,STRIDE RUNNER,-1,02/12/2025 10:00,1999.00,16321,India
"""
BANK = "Date,Narration,Withdrawal Amt.,Deposit Amt.,Closing Balance\n05/01/2026,RAZORPAY SETTLEMENT,,\"1,20,000.00\",\"5,20,000\"\n07/01/2026,RENT PUNE,\"45,000.00\",,\"4,75,000\"\n".encode()


def test_amounts_and_dates_in_indian_formats():
    assert parse_amount("₹1,23,456.50") == 123456.5
    assert parse_amount("Rs. 500") == 500
    assert parse_amount("(2,000)") == -2000
    assert parse_amount("") is None
    assert parse_date("05/01/2026") == date(2026, 1, 5)  # day first, as Indian banks write it
    assert parse_date("2026-01-05T10:00:00Z") == date(2026, 1, 5)
    assert parse_date("01/12/2025 07:45") == date(2025, 12, 1)


def test_retail_export_is_quantity_times_price_per_product():
    headers, rows = parse_table("orders.csv", UCI)
    m = suggest_mapping(headers)
    assert m == {"date": "InvoiceDate", "quantity": "Quantity", "unit_price": "Price", "product": "Description", "description": "Description"}
    txs = to_transactions(rows, m, "orders.csv")
    assert [(t["date"], t["kind"], t["amount"], t["product"], t["quantity"]) for t in txs] == [
        (date(2025, 12, 1), "sale", 3998.0, "STRIDE RUNNER", 2.0),
        (date(2025, 12, 1), "sale", 1794.0, "RUNNING SOCKS", 6.0),
        (date(2025, 12, 2), "sale", -1999.0, "STRIDE RUNNER", -1.0),  # a cancellation is a negative sale
    ]


def test_bank_statement_splits_deposits_and_withdrawals():
    headers, rows = parse_table("hdfc.csv", BANK)
    m = suggest_mapping(headers)
    assert m == {"date": "Date", "credit": "Deposit Amt.", "debit": "Withdrawal Amt.", "description": "Narration"}
    txs = to_transactions(rows, m, "hdfc.csv")
    assert [(t["kind"], t["amount"], t["description"]) for t in txs] == [("sale", 120000.0, "RAZORPAY SETTLEMENT"), ("expense", 45000.0, "RENT PUNE")]


def test_metrics_revenue_margin_burn_runway():
    txs = [
        {"date": date(2026, 1, 10), "kind": "sale", "amount": 300000, "product": "Stride Runner", "quantity": 150},
        {"date": date(2026, 1, 20), "kind": "expense", "amount": 360000, "product": None, "quantity": None},
        {"date": date(2026, 2, 10), "kind": "sale", "amount": 330000, "product": "Stride Runner", "quantity": 165},
        {"date": date(2026, 2, 20), "kind": "expense", "amount": 390000, "product": None, "quantity": None},
        {"date": date(2026, 3, 10), "kind": "sale", "amount": 360000, "product": "Stride Runner", "quantity": 180},
        {"date": date(2026, 3, 20), "kind": "expense", "amount": 420000, "product": None, "quantity": None},
        {"date": date(2025, 11, 1), "kind": "funding", "amount": 5000000, "product": None, "quantity": None},
    ]
    m = metrics(txs, cash=1200000)
    assert m["months"] == [{"month": "2026-01", "revenue": 300000, "expenses": 360000}, {"month": "2026-02", "revenue": 330000, "expenses": 390000},
                           {"month": "2026-03", "revenue": 360000, "expenses": 420000}]
    assert m["monthly_revenue"] == 330000 and m["monthly_expenses"] == 390000
    assert m["operating_margin"] == -0.1818  # (990k − 1,170k) / 990k over the last 3 months
    assert m["monthly_burn"] == 60000 and m["runway_months"] == 20.0
    assert m["funding_total"] == 5000000
    assert m["products"] == [{"product": "Stride Runner", "units": 495, "revenue": 990000, "avg_price": 2000}]


def test_no_burn_means_no_runway_limit():
    m = metrics([{"date": date(2026, 1, 1), "kind": "sale", "amount": 100, "product": None, "quantity": None}], cash=50)
    assert m["monthly_burn"] == 0 and m["runway_months"] is None


def test_benchmark_lookup():
    b = benchmark("Shoe")
    assert b["firms"] == 13 and b["operating_margin"] == 0.0825 and b["gross_margin"] == 0.5197
    assert benchmark("Nope") is None


def test_bank_settlements_are_not_double_counted_with_order_exports():
    txs = [
        {"date": date(2026, 1, 3), "kind": "sale", "amount": 4000, "product": "Stride Runner", "quantity": 2},   # order export
        {"date": date(2026, 1, 9), "kind": "sale", "amount": 3900, "product": None, "quantity": None},           # the same money, settled
        {"date": date(2026, 2, 9), "kind": "sale", "amount": 5000, "product": None, "quantity": None},           # no orders this month
    ]
    assert [m["revenue"] for m in metrics(txs, cash=None)["months"]] == [4000, 5000]

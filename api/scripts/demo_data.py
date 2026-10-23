"""Demo business exports, modelled on real data (D-75). Re-runnable and deterministic.

Stride & Co. (fictional footwear D2C, Pune):
- orders-*.xlsx: the order rhythm of UCI Online Retail II (CC BY 4.0, Chen 2012, doi:10.24432/C5CG6D): one in SAMPLE invoices
  of Dec 2010–Nov 2011, each mapped to a Stride product, dates moved to Oct 2025–Sep 2026; cancellations kept as returns.
- bank-statement-*.csv: costs from Campus Activewear's FY26 results (gross margin 53.5% → stock costs 46.5% of revenue),
  plus fixed rent and salaries and variable ads and shipping; one seed round.

Usage (from api/): .venv/Scripts/python -m scripts.demo_data <uci-2010-11.csv>
  (the CSV is the 'Year 2010-2011' sheet saved as: Invoice,StockCode,Quantity,InvoiceDate,Price,Country)
"""
import csv
import sys
import zlib
from collections import defaultdict
from datetime import date, datetime
from pathlib import Path

from openpyxl import Workbook

OUT = Path(__file__).resolve().parents[2] / "fixtures" / "demo" / "stride"
SAMPLE = 7
SHIFT_MONTHS = 14 * 12 + 10  # Dec 2010 → Oct 2025
PRODUCTS = [("Stride Runner", 1999, 8), ("Stride Trail", 2499, 5), ("Stride Running Socks (3 pairs)", 299, 7)]  # name, ₹, weight of 20
COGS = 0.465  # Campus Activewear FY26 gross margin 53.5%
FIXED = [("WAREHOUSE RENT PUNE", 65000), ("SALARIES - 6 STAFF", 240000)]
VARIABLE = [("META ADS", 0.18), ("SHIPROCKET LOGISTICS", 0.08)]
SEED = (date(2025, 10, 3), "SEED FUNDING - ANGEL ROUND", 5000000)


def _shift(d: datetime) -> date:
    m = d.year * 12 + d.month - 1 + SHIFT_MONTHS
    return date(m // 12, m % 12 + 1, min(d.day, 28))


def _product(code: str):
    h = zlib.crc32(code.encode()) % 20
    for name, price, weight in PRODUCTS:
        if h < weight:
            return name, price
        h -= weight
    return PRODUCTS[0][:2]


def build_stride(uci_csv: Path) -> dict:
    OUT.mkdir(parents=True, exist_ok=True)
    orders, seen = [], set()
    with uci_csv.open(encoding="utf-8") as f:
        for inv, code, qty, when, _price, _country in csv.reader(f):
            if not inv.lstrip("C").isdigit():  # 'A' rows are bad-debt adjustments, not orders
                continue
            num = int(inv.lstrip("C"))
            d = datetime.fromisoformat(when)
            if num % SAMPLE or (d.year, d.month) == (2011, 12) or inv in seen or not code[:1].isdigit():
                continue
            seen.add(inv)  # one line per sampled invoice: a D2C order, not a wholesale basket
            name, price = _product(code)
            q = (1 if abs(int(qty)) <= 12 else 2) * (-1 if inv.startswith("C") else 1)
            orders.append((f"SC-{inv}", _shift(d), name, q, price))

    wb = Workbook()
    ws = wb.active
    ws.title = "Orders"
    ws.append(["Order ID", "Order Date", "Product", "Quantity", "Unit Price (INR)"])
    for o in sorted(orders, key=lambda o: o[1]):
        ws.append([o[0], o[1].strftime("%d/%m/%Y"), o[2], o[3], o[4]])
    first, last = min(o[1] for o in orders), max(o[1] for o in orders)
    tag = f"{first:%b%Y}-{last:%b%Y}".lower()
    wb.save(OUT / f"orders-{tag}.xlsx")

    revenue = defaultdict(float)
    for _, d, _, q, p in orders:
        revenue[(d.year, d.month)] += q * p
    rows, balance = [], 0.0
    rows.append((SEED[0], SEED[1], None, SEED[2]))
    for (y, m), rev in sorted(revenue.items()):
        rows.append((date(y, m, 5), "INVENTORY - FACTORY PAYMENT AGRA", round(rev * COGS), None))
        rows.append((date(y, m, 28), "RAZORPAY SETTLEMENT", None, round(rev)))
        rows += [(date(y, m, 1), n, amt, None) for n, amt in FIXED]
        rows += [(date(y, m, 15), n, round(rev * share), None) for n, share in VARIABLE]
    with (OUT / f"bank-statement-{tag}.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["Date", "Narration", "Withdrawal Amt.", "Deposit Amt.", "Closing Balance"])
        for d, n, out, inn in sorted(rows, key=lambda r: r[0]):
            balance += (inn or 0) - (out or 0)
            w.writerow([d.strftime("%d/%m/%Y"), n, f"{out:.2f}" if out else "", f"{inn:.2f}" if inn else "", f"{balance:.2f}"])
    return {"orders": len(orders), "months": len(revenue), "avg_monthly_revenue": round(sum(revenue.values()) / len(revenue)),
            "closing_balance": round(balance), "files": sorted(p.name for p in OUT.iterdir())}


if __name__ == "__main__":
    print(build_stride(Path(sys.argv[1])))

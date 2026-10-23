"""Kesar Bakehouse (fictional Pune bakery) order export, modelled on real data (D-75). Deterministic.

- Orders: every transaction of The Bread Basket, a real Edinburgh bakery (CC0; OpenML 43422, Kaggle mittalvasu95/the-bread-basket),
  the five complete months Nov 2016 – Mar 2017, dates moved forward 113 months (to Apr – Aug 2026).
- Prices: each item is priced at a comparable item on Theobroma's public online menu (theobroma.in, a Mumbai/Pune bakery chain),
  read on 24 Oct 2026 through the app's robots.txt-respecting fetcher. Items with no comparable on that menu are dropped.

Usage (from api/): .venv/Scripts/python -m scripts.bakery_data <The-Bread-Basket.arff>
"""
import csv
import sys
from datetime import datetime
from pathlib import Path

OUT = Path(__file__).resolve().parents[2] / "fixtures" / "demo" / "bakery" / "orders-apr2026-aug2026.csv"
SHIFT_MONTHS = 113
THEOBROMA = "https://theobroma.in/products/"
# Bread Basket item → (name on the export, ₹, Theobroma product it's priced from)
PRICES = {
    "Coffee": ("Cappuccino", 175, "cappuccino-250ml"),
    "Bread": ("Wheat bread loaf", 90, "wheat-bread-loaf-400g"),
    "Tea": ("Iced tea", 104, "lemon-iced-tea-300-ml"),
    "Cake": ("Chocolate cake slice", 155, "rich-chocolate-pastry-1-piece"),
    "Pastry": ("Dutch truffle pastry", 140, "dutch-truffle-pastry-1-piece"),
    "Sandwich": ("Stuffed roll", 120, "chicken-ham-cheese-stuffed-roll"),
    "Hot chocolate": ("Hot chocolate", 195, "hot-chocolate-250ml"),
    "Brownie": ("Choco chip brownie", 110, "choco-chip-brownie-1-piece"),
    "Farm House": ("Multigrain loaf", 110, "multigrain-loaf-400g"),
    "Muffin": ("Chocolate cupcake", 130, "chocolate-cupcake-1-piece"),
    "Juice": ("Orange juice", 170, "valencia-orange-juice-200-ml"),
    "Baguette": ("French baguette", 100, "french-baguette-140g"),
    "Tiffin": ("Baked wada pao", 35, "baked-wada-pao-1-piece"),
}


def shift(d: datetime) -> datetime:
    m = d.month - 1 + SHIFT_MONTHS
    y, m = d.year + m // 12, m % 12 + 1
    for day in (d.day, 30, 29, 28):
        try:
            return d.replace(year=y, month=m, day=day)
        except ValueError:
            continue


def main(arff: str) -> None:
    rows = []
    for line in Path(arff).read_text(encoding="utf-8").splitlines():
        if not line or line[0] in "@%":
            continue
        tx, item, when = [p.strip().strip("'") for p in line.split(",")[:3]]
        if item in PRICES and when[3:10] not in ("10-2016", "04-2017"):  # partial first and last months
            name, price, _ = PRICES[item]
            rows.append((shift(datetime.strptime(when, "%d-%m-%Y %H:%M")), f"KB-{int(tx):05d}", name, price))
    with OUT.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["Order Date", "Order ID", "Item", "Quantity", "Unit Price (INR)"])
        for when, tx, name, price in rows:
            w.writerow([when.strftime("%Y-%m-%d %H:%M"), tx, name, 1, price])
    print(len(rows), "items written to", OUT)


if __name__ == "__main__":
    main(sys.argv[1])

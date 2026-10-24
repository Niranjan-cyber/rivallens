"""B14d: like-for-like comparison inside one category."""
from app.modules.products.market import niche_overlap, price_position, product_links


def test_price_position_against_the_category_median():
    pos = price_position(1999, [999, 1499, 1699, 2499, 3999])
    assert pos == {"n": 5, "median": 1699, "min": 999, "max": 3999, "q75": 2499, "pct_vs_median": 18, "rank": 4}


def test_price_position_without_your_price_or_comparables():
    assert price_position(None, [999, 1499])["pct_vs_median"] is None
    assert price_position(999, []) == {"n": 0, "median": None, "min": None, "max": None, "q75": None, "pct_vs_median": None, "rank": None}


def test_product_links_prefer_the_niche_and_stay_on_the_site():
    html = """<a href="/products/hurricane-running-shoes-men">x</a><a href="/products/flip-flop-blue">y</a>
    <a href="https://other.com/products/run-1">z</a><a href="/collections/products/trail-running-shoe?variant=2">w</a>
    <a href="/products/hurricane-running-shoes-men">dup</a>"""
    links = product_links("https://www.shoes.in/", html, {"running", "shoe"}, 3)
    assert links == ["https://www.shoes.in/products/hurricane-running-shoes-men", "https://www.shoes.in/collections/products/trail-running-shoe",
                     "https://www.shoes.in/products/flip-flop-blue"]


def test_niche_overlap_ignores_the_category_word_itself():
    assert niche_overlap("Running shoes", "Men's running shoe", leaf="Shoes") is True
    assert niche_overlap("Running shoes", "Women's sneakers", leaf="Shoes") is False


def test_in_category_counts_sub_categories_only():
    from app.modules.products.market import in_category
    bakery = "Food, Beverages & Tobacco > Food Items > Bakery"
    assert in_category(bakery, bakery)
    assert in_category(bakery + " > Pastries & Scones", bakery)
    assert not in_category("Food, Beverages & Tobacco > Food Items > Bakery Mixes", bakery)  # a prefix, not a child
    assert not in_category("Food, Beverages & Tobacco > Food Items", bakery)  # the parent is broader
    assert not in_category(None, bakery)


def test_catalogue_links_pick_matching_products_not_merch():
    from app.modules.products.market import catalogue_links
    cat = {"products": [
        {"handle": "aramse-coffee-journal", "title": "Coffee Journal", "product_type": "Merchandise", "tags": ["gift"]},
        {"handle": "french-press", "title": "Coffee + French Press", "product_type": "Equipment", "tags": []},
        {"handle": "vienna-roast", "title": "Vienna Roast", "product_type": "Coffee", "tags": ["filter", "ground"]},
        {"handle": "south-indian-filter-coffee", "title": "South Indian Filter Coffee Powder", "product_type": "Coffee", "tags": []},
    ]}
    assert catalogue_links("https://www.bluetokaicoffee.com/products.json?limit=250", cat, {"filter", "powder"}, 5) == [
        "https://www.bluetokaicoffee.com/products/south-indian-filter-coffee",
        "https://www.bluetokaicoffee.com/products/vienna-roast"]
    assert catalogue_links("https://x.in/products.json", {"products": []}, {"filter"}, 5) == []
    assert catalogue_links("https://x.in/products.json", {"oops": 1}, {"filter"}, 5) == []


def test_niche_overlap_needs_every_distinguishing_word():
    assert niche_overlap("Filter coffee powder", "Filter coffee powder South Indian Traditional Filter Coffee", leaf="Coffee") is True
    assert niche_overlap("Filter coffee powder", "Instant coffee powder Classic Protein Coffee Powder", leaf="Coffee") is False
    assert niche_overlap("Cold brew coffee bags", "Canned cold brew Orange Mint", leaf="Coffee") is False
    assert niche_overlap("Coffee", "Coffee Cappuccino", leaf="Coffee") is False  # nothing beyond the category word

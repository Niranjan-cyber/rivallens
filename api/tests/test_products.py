"""B14c: exact categories from the Google product taxonomy, and products read from schema.org JSON-LD."""
from app.modules.products.taxonomy import candidates, path_of
from app.modules.products.pages import product_from_html


def ids(text: str, n: int = 5) -> list[int]:
    return [c["id"] for c in candidates(text, n)]


def test_indian_football_is_a_soccer_ball_not_an_american_football():
    assert ids("Size 5 training football")[0] == 1112  # Sporting Goods > Athletics > Soccer > Soccer Balls


def test_chair_lands_in_chairs():
    assert ids("Ergonomic office chair")[0] == 2045  # Furniture > Office Furniture > Office Chairs


def test_running_shoes_land_in_shoes():
    assert 187 in ids("Stride Runner running shoes for Indian roads")  # Apparel & Accessories > Shoes


def test_bakery_items():  # the prefilter only needs recall: the LLM picks from these 20
    assert 2194 in ids("Chocolate truffle cake 1 kg", 20)  # Bakery > Cakes & Dessert Bars
    assert 424 in ids("Whole wheat bread loaf")  # Bakery > Breads & Buns


def test_path_lookup():
    assert path_of(2045) == "Furniture > Office Furniture > Office Chairs"
    assert path_of(-1) is None


def test_product_from_json_ld():
    html = """<html><head><script type="application/ld+json">
    {"@context":"https://schema.org","@graph":[{"@type":"Organization","name":"X"},
     {"@type":"Product","name":"Campus North Plus Running Shoes","brand":{"@type":"Brand","name":"Campus"},
      "description":"Lightweight mesh runner","offers":{"@type":"Offer","price":"1499.00","priceCurrency":"INR"},
      "aggregateRating":{"ratingValue":"4.2","reviewCount":"318"}}]}
    </script></head><body></body></html>"""
    p = product_from_html(html)
    assert p == {"name": "Campus North Plus Running Shoes", "brand": "Campus", "description": "Lightweight mesh runner",
                 "price": 1499.0, "currency": "INR", "rating": 4.2, "review_count": 318}


def test_product_from_html_without_json_ld_is_none():
    assert product_from_html("<html><body><h1>Hi</h1></body></html>") is None

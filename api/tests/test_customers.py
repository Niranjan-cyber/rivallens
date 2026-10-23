"""B14g Customers: reviews and comments from uploads and pages; themes must cite real mentions."""
from datetime import date

from app.modules.customers.service import checked_themes, mentions_from_rows, reviews_from_html, suggest_review_mapping


def test_review_export_columns_are_recognised():
    headers = ["Id", "ProductId", "UserId", "ProfileName", "Score", "Time", "Summary", "Text"]
    assert suggest_review_mapping(headers) == {"text": "Text", "rating": "Score", "date": "Time", "author": "ProfileName", "title": "Summary", "product": "ProductId"}
    insta = ["Comment", "Username", "Posted on", "Post link"]
    assert suggest_review_mapping(insta) == {"text": "Comment", "date": "Posted on", "author": "Username", "url": "Post link"}


def test_rows_become_mentions_with_unix_or_text_dates():
    rows = [{"Text": "Great cake, too sweet though", "Score": "4", "Time": "1303862400", "ProfileName": "A", "Summary": "Nice"},
            {"Text": "", "Score": "5", "Time": "1303862400", "ProfileName": "B", "Summary": ""}]
    m = mentions_from_rows(rows, {"text": "Text", "rating": "Score", "date": "Time", "author": "ProfileName", "title": "Summary"}, "reviews.csv")
    assert m == [{"text": "Nice. Great cake, too sweet though", "rating": 4.0, "date": date(2011, 4, 27), "author": "A", "url": None,
                  "product": None, "source": "reviews.csv", "source_type": "upload"}]


def test_reviews_from_json_ld():
    html = """<script type="application/ld+json">{"@type":"Product","name":"Runner","review":[
      {"@type":"Review","reviewBody":"Runs small, order a size up","reviewRating":{"ratingValue":"3"},"author":{"name":"Priya"},"datePublished":"2026-08-01"},
      {"@type":"Review","reviewBody":"Very comfortable","reviewRating":{"ratingValue":5},"author":"Arjun"}]}</script>"""
    assert reviews_from_html(html) == [
        {"text": "Runs small, order a size up", "rating": 3.0, "author": "Priya", "date": date(2026, 8, 1)},
        {"text": "Very comfortable", "rating": 5.0, "author": "Arjun", "date": None},
    ]


def test_themes_keep_only_real_mention_ids_and_drop_empty_ones():
    themes = [{"label": "Wider sizes", "kind": "request", "mention_ids": [0, 2, 99]},
              {"label": "Invented", "kind": "complaint", "mention_ids": [42]}]
    assert checked_themes(themes, n_mentions=3) == [{"label": "Wider sizes", "kind": "request", "mention_ids": [0, 2], "count": 2}]

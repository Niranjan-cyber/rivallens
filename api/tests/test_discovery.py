"""C-05 discovery seams: India signals, domain blocklist/dedupe, similarity (specs §1 C-05)."""
from pathlib import Path

from app.modules.collector.service import split_sections
from app.modules.discovery.service import blocked, india_signals, registrable_domain, similarity

PAGES = Path(__file__).resolve().parents[2] / "fixtures" / "pricing-pages"


def page_text(name: str) -> str:
    return split_sections((PAGES / f"{name}-pricing.html").read_text(encoding="utf-8", errors="replace"))[0]


def test_india_signals_weights():
    s = india_signals("Plans from ₹499/month. GST extra. Servers in Mumbai. Call +91 98765 43210", "https://example.in")
    assert s["score"] == 2 + 2 + 1 + 1 + 1 + 1  # ₹, .in, India/city, +91, GST, region
    assert india_signals("Pricing in USD for teams worldwide", "https://example.com") == {"score": 0, "hits": []}


def test_e2e_networks_fixture_is_india_verified_and_render_is_not():
    assert india_signals(page_text("e2enetworks"), "https://www.e2enetworks.com/pricing")["score"] >= 1
    assert india_signals(page_text("render"), "https://render.com/pricing")["score"] == 0


def test_blocklist_and_registrable_domain():
    assert registrable_domain("https://www.e2enetworks.com/pricing") == "e2enetworks.com"
    assert registrable_domain("https://blog.render.co.in/x") == "render.co.in"
    assert all(blocked(u) for u in ["https://en.wikipedia.org/wiki/X", "https://www.g2.com/p", "https://www.capterra.in/x",
                                     "https://economictimes.indiatimes.com/a", "https://www.amazon.in/x", "https://medium.com/@x"])
    assert not blocked("https://railway.com/pricing")


def test_similarity_ranks_a_cloud_host_above_an_unrelated_page():
    card = "managed app deployment cloud hosting for developers deploy apps servers"
    assert similarity(card, page_text("railway")) > similarity(card, "Fresh organic vegetables delivered to your door in 10 minutes")
    assert similarity(card, page_text("railway")) >= 0.08

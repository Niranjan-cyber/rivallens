"""C-05 discovery, pure parts: India signals, domain handling, similarity (specs §1 C-05)."""
import math
import re
from collections import Counter
from urllib.parse import urlsplit

CITIES = r"india|pune|mumbai|delhi|bengaluru|bangalore|hyderabad|chennai|kolkata|ahmedabad|noida|gurugram|gurgaon|jaipur"
REGIONS = r"mumbai|delhi|hyderabad|chennai|bangalore|bengaluru"
SIGNALS = [  # (label, weight, test on text)
    ("₹ / INR / Rs.", 2, lambda t: re.search(r"₹|\bINR\b|\bRs\.", t)),
    ("India or an Indian city", 1, lambda t: re.search(rf"\b({CITIES})\b", t, re.I)),
    ("+91 phone number", 1, lambda t: re.search(r"\+91[\s-]?\d", t)),
    ("GST / GSTIN", 1, lambda t: re.search(r"\bGST(IN)?\b", t)),
    ("India region", 1, lambda t: re.search(rf"\b({REGIONS})\b", t, re.I)),
]
BLOCKLIST = re.compile(r"(^|\.)(wikipedia\.org|g2\.com|capterra\.(com|in)|getapp\.com|trustradius\.com|crunchbase\.com|linkedin\.com|"
                       r"youtube\.com|reddit\.com|quora\.com|medium\.com|github\.com|amazon\.(in|com)|flipkart\.com|indiamart\.com|"
                       r"justdial\.com|indiatimes\.com|livemint\.com|moneycontrol\.com|yourstory\.com|inc42\.com|techcrunch\.com|"
                       r"forbes\.com|thehindu\.com|ndtv\.com|business-standard\.com|economictimes\.com|x\.com|twitter\.com|facebook\.com|"
                       r"instagram\.com|producthunt\.com|stackshare\.io|slashdot\.org|sourceforge\.net)$")
SECOND_LEVEL = {"co.in", "org.in", "net.in", "ac.in", "gov.in", "co.uk", "com.au", "com.sg"}
STOP = set("the and for with your you our are from that this all can get any per not use more into via has have will was its out new "
           "one how what when who why which also each free plan plans pricing price month year team teams".split())


def registrable_domain(url: str) -> str:
    host = (urlsplit(url if "//" in url else f"//{url}").hostname or "").lower().removeprefix("www.")
    parts = host.split(".")
    return ".".join(parts[-3:]) if ".".join(parts[-2:]) in SECOND_LEVEL else ".".join(parts[-2:])


def blocked(url: str) -> bool:
    return bool(BLOCKLIST.search(registrable_domain(url)))


def india_signals(text: str, url: str) -> dict:
    hits = [(label, w) for label, w, test in SIGNALS if test(text)]
    if registrable_domain(url).endswith(".in"):
        hits.insert(1, (".in domain", 2))
    return {"score": sum(w for _, w in hits), "hits": [label for label, _ in hits]}


def _terms(text: str) -> Counter:
    return Counter(w for w in re.findall(r"[a-z]{3,}", text.lower()) if w not in STOP)


def similarity(card_text: str, page_text: str) -> float:
    """Cosine of term frequencies (log-scaled). Two documents give no useful IDF, so this is TF-only."""
    a, b = _terms(card_text), _terms(page_text)
    wa = {t: 1 + math.log(c) for t, c in a.items()}
    wb = {t: 1 + math.log(c) for t, c in b.items()}
    dot = sum(v * wb.get(t, 0) for t, v in wa.items())
    norm = math.sqrt(sum(v * v for v in wa.values())) * math.sqrt(sum(v * v for v in wb.values()))
    return round(dot / norm, 3) if norm else 0.0

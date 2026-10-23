"""Google product taxonomy (2021-09-21, ~5,600 paths): exact categories for products.

candidates() is a cheap keyword prefilter for recall; the LLM then picks one path from its shortlist (classify.py).
"""
import re
from functools import cache
from pathlib import Path

FILE = Path(__file__).resolve().parents[2] / "data" / "google-product-taxonomy.txt"
STOP = {"for", "and", "with", "the", "of", "in", "on", "a", "an", "to", "by", "kg", "g", "ml", "size", "pack", "set", "new", "my", "our", "indian", "india", "made", "hand", "premium", "best", "quality"}
# Indian English and seller vocabulary → taxonomy words. REPLACE drops the original word
# (in India "football" is soccer, and "runner" is a shoe, not an aisle runner).
REPLACE = {"football": ["soccer", "ball"], "sneaker": ["shoe"], "trainer": ["shoe"], "runner": ["shoe"], "chappal": ["sandal"]}
SYNONYMS = {"saas": ["software"], "app": ["software"], "hosting": ["software"], "mobile": ["phone"], "biscuit": ["cookie"]}


def _singular(w: str) -> str:
    if w.endswith("ies") and len(w) > 4:
        return w[:-3] + "y"
    if w.endswith("shoes"):
        return w[:-1]
    if w.endswith("s") and not w.endswith("ss") and len(w) > 3:
        return w[:-1]
    return w


def tokens(text: str, query: bool = False) -> set[str]:
    out = set()
    for w in re.findall(r"[a-z]+", text.lower()):
        w = _singular(w)
        if w in STOP or len(w) < 3:
            continue
        if query and w in REPLACE:
            out.update(REPLACE[w])
            continue
        out.add(w)
        if query:
            out.update(SYNONYMS.get(w, []))
    return out


@cache
def _paths() -> list[tuple[int, str, set[str], set[str]]]:
    rows = []
    for line in FILE.read_text(encoding="utf-8").splitlines():
        if line.startswith("#") or " - " not in line:
            continue
        id_, path = line.split(" - ", 1)
        parts = path.split(" > ")
        rows.append((int(id_), path, tokens(parts[-1]), tokens(" ".join(parts[:-1]))))
    return rows


def path_of(taxonomy_id: int) -> str | None:
    return next((p for i, p, _, _ in _paths() if i == taxonomy_id), None)


def candidates(text: str, n: int = 20) -> list[dict]:
    words = tokens(text, query=True)
    scored = []
    for id_, path, leaf, parents in _paths():
        hit = len(words & leaf)
        if not hit:
            continue
        # Leaf words matter most; leaf words the text doesn't mention count against (Shoes beats Shoe Covers).
        score = 3 * hit - (len(leaf) - hit) + 0.5 * len(words & parents)
        scored.append((score, -path.count(">"), id_, path))
    scored.sort(reverse=True)
    return [{"id": i, "path": p} for _, _, i, p in scored[:n]]

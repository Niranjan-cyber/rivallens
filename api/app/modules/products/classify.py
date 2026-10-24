"""Exact category for a product: keyword shortlist from the Google taxonomy → the LLM picks one, plus a niche label.

The taxonomy stops at "Shoes", so the niche ("Running shoes") is what comparisons match on inside a path.
"""
from pydantic import BaseModel, Field

from app.llm.gateway import LLMUnavailable, complete_json
from app.modules.products.taxonomy import candidates

PROMPT_VERSION = "classify_product.v1"
INSTRUCTIONS = (
    "Pick the single best category id for this product from the candidate list (Google product taxonomy). "
    "The seller is in India: 'football' means association football (soccer). "
    "Also give a niche: 2-4 words naming the product type buyers compare within, e.g. 'Running shoes', 'Ergonomic office chairs', "
    "'Celebration cakes', 'Managed app hosting'. Lower case except the first letter."
)


class Classified(BaseModel):
    taxonomy_id: int = Field(description="One id from the candidate list")
    niche: str = Field(description="2-4 word product type")


def classify(name: str, description: str = "", business: str = "") -> dict:
    """Returns {taxonomy_id, path, niche, source}; source is 'ai' or 'top_match' (LLM unavailable)."""
    text = f"{name}. {description}".strip()
    shortlist = candidates(f"{text} {business}", 20) or candidates(business, 20)
    if not shortlist:
        return {"taxonomy_id": None, "path": None, "niche": None, "source": "none"}
    try:
        out = complete_json("classify_product", Classified, {
            "instructions": INSTRUCTIONS, "product": text, "business": business,
            "candidates": "\n".join(f"{c['id']}: {c['path']}" for c in shortlist),
        }, PROMPT_VERSION)
        pick = next((c for c in shortlist if c["id"] == out.taxonomy_id), None)
        if pick:
            return {"taxonomy_id": pick["id"], "path": pick["path"], "niche": out.niche[:60], "source": "ai"}
    except LLMUnavailable:
        pass
    return {"taxonomy_id": shortlist[0]["id"], "path": shortlist[0]["path"], "niche": None, "source": "top_match"}


class Pick(BaseModel):
    index: int
    taxonomy_id: int
    niche: str


class Picks(BaseModel):
    items: list[Pick]


BATCH = 8  # free models answer only the first ~9 of a long list; the rest silently fell back to the root category (L-25)


def classify_many(names: list[str], business: str = "") -> list[dict]:
    """One LLM call per batch of products; same output per product as classify()."""
    if len(names) > BATCH:
        return [c for i in range(0, len(names), BATCH) for c in classify_many(names[i:i + BATCH], business)]
    shortlists = [candidates(f"{n} {business}", 15) or candidates(business, 15) for n in names]
    top = [{"taxonomy_id": s[0]["id"], "path": s[0]["path"], "niche": None, "source": "top_match"} if s else
           {"taxonomy_id": None, "path": None, "niche": None, "source": "none"} for s in shortlists]
    try:
        out = complete_json("classify_products", Picks, {
            "instructions": INSTRUCTIONS + " Answer one item per numbered product, using that product's own candidate list.",
            "business": business,
            "products": "\n\n".join(f"Product {i}: {n}\nCandidates:\n" + "\n".join(f"{c['id']}: {c['path']}" for c in s)
                                    for i, (n, s) in enumerate(zip(names, shortlists))),
        }, PROMPT_VERSION)
    except LLMUnavailable:
        return top
    for p in out.items:
        if 0 <= p.index < len(names):
            pick = next((c for c in shortlists[p.index] if c["id"] == p.taxonomy_id), None)
            if pick:
                top[p.index] = {"taxonomy_id": pick["id"], "path": pick["path"], "niche": p.niche[:60], "source": "ai"}
    return top

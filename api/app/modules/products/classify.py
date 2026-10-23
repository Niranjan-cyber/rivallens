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

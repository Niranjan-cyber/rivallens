"""C-04 card drafting: description or homepage → CardDraft via the LLM task draft_card (specs §1 C-04, §4.2)."""
from typing import Literal

from pydantic import BaseModel, Field

from app.jobs import Job
from app.llm.gateway import LLMUnavailable, complete_json
from app.modules.collector.service import fetch, split_sections

PROMPT_VERSION = "draft_card.v1"


class Price(BaseModel):
    amount: float | None = None
    currency: str | None = Field(None, description="ISO code, e.g. INR")
    period: Literal["month", "year", "one_time", "hour", "user"] | None = None


class CardDraft(BaseModel):
    name: str | None = Field(None, description="Business or product name, if stated")
    industry: str | None = None
    category: str | None = Field(None, description="Short market category, e.g. 'Managed app deployment'")
    offering_type: Literal["product", "service"] | None = None
    india_markets: list[str] = Field(default_factory=list, description="Indian cities or regions served, if stated")
    attributes: list[str] = Field(default_factory=list, description="Up to 5 key attributes or features")
    price: Price | None = None
    problem: str | None = None
    target_customer: str | None = None
    planned_features: list[str] = Field(default_factory=list)


class DraftFailed(Exception):
    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code


def draft_card(kind: str, description: str | None, url: str | None) -> dict:
    text = description or ""
    if url:
        page = fetch(url)
        if page["status"] == "blocked_robots":
            raise DraftFailed("blocked_robots", "That site's robots.txt doesn't allow us to read it. Describe your business instead.")
        if page["status"] != "ok":
            raise DraftFailed("site_unreadable", "We couldn't read that site. Describe your business in one line instead.")
        text = f"{text}\n\nHomepage text:\n{split_sections(page['html'])[0][:12000]}".strip()
    try:
        draft = complete_json("draft_card", CardDraft, {"kind": kind, "description": text}, PROMPT_VERSION)
    except LLMUnavailable:
        raise DraftFailed("drafting_unavailable", "The AI drafting service is busy. Fill the card in manually; it takes a minute.")
    out = draft.model_dump(mode="json")
    if url:
        out["website"] = url
    return out


def draft_job(job: Job, kind: str, description: str | None, url: str | None) -> dict:
    job.step("read", "running", None, "Reading your site…" if url else "Reading your description…")
    result = draft_card(kind, description, url)  # DraftFailed carries the job error code
    job.step("draft", "done", None, "Card drafted")
    return result

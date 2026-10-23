"""C-14 gateway seams: cache first, Gemini → Groq fallback, one schema repair, replay never calls a provider."""
import pytest
from pydantic import BaseModel

from app.llm import gateway
from app.llm.gateway import LLMUnavailable, complete_json


class Out(BaseModel):
    name: str
    amount: int | None


@pytest.fixture
def world(monkeypatch):
    cache, calls, script = {}, [], {"gemini": [], "groq": []}
    monkeypatch.setattr(gateway, "_cache_get", lambda key: cache.get(key))
    monkeypatch.setattr(gateway, "_cache_put", lambda key, task, provider, model, data: cache.__setitem__(key, data))
    monkeypatch.setattr(gateway, "LLM_MODE", "live")

    def provider(name):
        def call(system, user):
            calls.append(name)
            nxt = script[name].pop(0)
            if isinstance(nxt, Exception):
                raise nxt
            return nxt
        return call
    monkeypatch.setattr(gateway, "PROVIDERS", {"gemini": provider("gemini"), "groq": provider("groq")})
    return cache, calls, script


def test_second_identical_call_is_a_cache_hit(world):
    cache, calls, script = world
    script["gemini"].append('{"name": "StackNest", "amount": 999}')
    assert complete_json("t", Out, {"text": "x"}).amount == 999
    assert complete_json("t", Out, {"text": "x"}).name == "StackNest"
    assert calls == ["gemini"]


def test_gemini_rate_limit_falls_back_to_groq(world):
    _, calls, script = world
    script["gemini"].append(gateway.ProviderError("429"))
    script["groq"].append('{"name": "G", "amount": null}')
    assert complete_json("t", Out, {"text": "y"}).name == "G"
    assert calls == ["gemini", "groq"]


def test_invalid_json_gets_one_repair_then_falls_back(world):
    _, calls, script = world
    script["gemini"] += ['{"name": 1', '{"nope": true}']
    script["groq"].append('{"name": "R", "amount": 5}')
    assert complete_json("t", Out, {"text": "z"}).name == "R"
    assert calls == ["gemini", "gemini", "groq"]


def test_both_down_raises_unavailable(world):
    _, _, script = world
    script["gemini"].append(gateway.ProviderError("500"))
    script["groq"].append(gateway.ProviderError("timeout"))
    with pytest.raises(LLMUnavailable):
        complete_json("t", Out, {"text": "w"})


def test_replay_mode_never_calls_a_provider(world, monkeypatch):
    _, calls, _ = world
    monkeypatch.setattr(gateway, "LLM_MODE", "replay")
    with pytest.raises(LLMUnavailable):
        complete_json("t", Out, {"text": "unseen"})
    assert calls == []


def test_draft_card_replays_the_recorded_gemini_answer(monkeypatch):
    """fixtures/llm/draft_card-*.json was recorded from a live Gemini call on 23 Oct 2026."""
    from app.modules.profiles.drafting import draft_card
    monkeypatch.setattr(gateway, "LLM_MODE", "replay")
    monkeypatch.setattr(gateway, "_cache_get", lambda key: None)
    d = draft_card("business", "Pune startup, managed app deployment for Indian developers, Pro ₹999/mo", None)
    assert (d["offering_type"], d["price"]["amount"], d["price"]["currency"], d["price"]["period"]) == ("service", 999.0, "INR", "month")
    assert "Pune" in d["india_markets"]


def test_answers_failing_cache_if_are_not_cached(world):
    cache, calls, script = world
    script["gemini"] += ['{"name": "", "amount": null}', '{"name": "Real", "amount": 1}']
    keep = lambda out: bool(out.name)  # noqa: E731
    assert complete_json("t", Out, {"text": "e"}, cache_if=keep).name == ""
    assert complete_json("t", Out, {"text": "e"}, cache_if=keep).name == "Real"  # the empty answer wasn't reused
    assert calls == ["gemini", "gemini"]

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

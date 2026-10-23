"""C-14 LLM gateway: cache → Gemini → Groq, JSON validated by Pydantic with one repair (specs §1 C-14)."""
import hashlib
import json
import logging
import os
import threading
import time
from pathlib import Path

import httpx
from pydantic import BaseModel, ValidationError
from sqlalchemy import text

from app.db import engine

log = logging.getLogger("llm")
LLM_MODE = os.getenv("LLM_MODE", "live")  # live | replay | record
GEMINI_KEY, GROQ_KEY = os.getenv("GEMINI_API_KEY", "").strip(), os.getenv("GROQ_API_KEY", "").strip()
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-flash-latest")
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
RPM = {"gemini": int(os.getenv("GEMINI_RPM", "5")), "groq": int(os.getenv("GROQ_RPM", "30"))}
FIXTURES = Path(__file__).resolve().parents[3] / "fixtures" / "llm"
SYSTEM = ("Use only the provided text. Return null for anything unknown. Do not infer prices or features. "
          "Reply with one JSON object that matches this JSON schema exactly:\n")


class ProviderError(Exception):
    pass


class LLMUnavailable(Exception):
    pass


_lock = threading.Lock()
_next_slot: dict[str, float] = {}


def _wait_for_capacity(provider: str) -> None:
    """Token bucket as a minimum interval: wait up to 30 s, otherwise give up on this provider."""
    with _lock:
        now = time.monotonic()
        slot = max(_next_slot.get(provider, now), now)
        if slot - now > 30:
            raise ProviderError(f"{provider} busy")
        _next_slot[provider] = slot + 60 / RPM[provider]
    time.sleep(max(slot - now, 0))


def _gemini(system: str, user: str) -> str:
    if not GEMINI_KEY:
        raise ProviderError("no gemini key")
    _wait_for_capacity("gemini")
    try:
        r = httpx.post(f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent",
                       headers={"x-goog-api-key": GEMINI_KEY}, timeout=20,
                       json={"systemInstruction": {"parts": [{"text": system}]}, "contents": [{"role": "user", "parts": [{"text": user}]}],
                             "generationConfig": {"responseMimeType": "application/json", "temperature": 0}})
    except httpx.HTTPError as e:
        raise ProviderError(f"gemini {type(e).__name__}")
    if r.status_code != 200:
        raise ProviderError(f"gemini {r.status_code}")
    return r.json()["candidates"][0]["content"]["parts"][0]["text"]


def _groq(system: str, user: str) -> str:
    if not GROQ_KEY:
        raise ProviderError("no groq key")
    _wait_for_capacity("groq")
    try:
        r = httpx.post("https://api.groq.com/openai/v1/chat/completions", headers={"Authorization": f"Bearer {GROQ_KEY}"}, timeout=20,
                       json={"model": GROQ_MODEL, "temperature": 0, "response_format": {"type": "json_object"},
                             "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}]})
    except httpx.HTTPError as e:
        raise ProviderError(f"groq {type(e).__name__}")
    if r.status_code != 200:
        raise ProviderError(f"groq {r.status_code}")
    return r.json()["choices"][0]["message"]["content"]


PROVIDERS = {"gemini": _gemini, "groq": _groq}
MODELS = {"gemini": GEMINI_MODEL, "groq": GROQ_MODEL}


def _cache_get(key: str) -> dict | None:
    with engine.begin() as conn:
        return conn.execute(text("select response from llm_cache where key = :k"), {"k": key}).scalar()


def _cache_put(key: str, task: str, provider: str, model: str, data: dict) -> None:
    with engine.begin() as conn:
        conn.execute(text("""insert into llm_cache (key, task, provider, model, prompt_version, response)
                             values (:k, :t, :p, :m, :v, cast(:r as jsonb)) on conflict (key) do nothing"""),
                     {"k": key, "t": task, "p": provider, "m": model, "v": key.split(":")[0], "r": json.dumps(data)})


def complete_json(task: str, schema: type[BaseModel], prompt_vars: dict, prompt_version: str = "v1", max_input_chars: int = 12000):
    user = "\n\n".join(f"{k}:\n{str(v)[:max_input_chars]}" for k, v in prompt_vars.items())
    key = f"{prompt_version}:" + hashlib.sha256(f"{task}|{prompt_version}|{user}".encode()).hexdigest()
    fixture = FIXTURES / f"{task}-{key[-16:]}.json"

    cached = _cache_get(key)
    if cached is None and LLM_MODE == "replay" and fixture.exists():
        cached = json.loads(fixture.read_text(encoding="utf-8"))
    if cached is not None:
        log.info("llm cache hit task=%s key=%s", task, key[-16:])
        return schema.model_validate(cached)
    if LLM_MODE == "replay":
        raise LLMUnavailable(f"replay miss for {task}")

    system = SYSTEM + json.dumps(schema.model_json_schema())
    for provider, call in PROVIDERS.items():
        try:
            raw = call(system, user)
            try:
                out = schema.model_validate_json(raw)
            except ValidationError as e:  # one repair attempt with the validation error
                raw = call(system, f"{user}\n\nYour previous reply was invalid ({str(e)[:300]}). Reply again with valid JSON only.")
                out = schema.model_validate_json(raw)
        except (ProviderError, ValidationError, KeyError, IndexError) as e:
            log.warning("llm %s failed for %s: %s", provider, task, str(e)[:120])
            continue
        data = out.model_dump(mode="json")
        _cache_put(key, task, provider, MODELS[provider], data)
        if LLM_MODE == "record":
            fixture.write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")
        log.info("llm provider call task=%s provider=%s", task, provider)
        return out
    raise LLMUnavailable(f"all providers failed for {task}")

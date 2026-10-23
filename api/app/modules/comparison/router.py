import json
import os
import re
from datetime import datetime
from typing import Literal
from uuid import UUID

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import Connection, text

from app.auth import UserDep
from app.db import ConnDep
from app.modules.comparison.service import monthly_inr, score_rows
from app.modules.discovery.pipeline import card_value

router = APIRouter(prefix="/api/v1", tags=["comparison"])
USD_INR_RATE = float(os.getenv("USD_INR_RATE", "84"))
INDIA = re.compile(r"\b(india|mumbai|delhi|bengaluru|bangalore|hyderabad|chennai|pune|kolkata)\b", re.I)
SUPPORT = [(re.compile(r"priority|phone|dedicated|account manager|24/7", re.I), 3), (re.compile(r"email|chat", re.I), 2),
           (re.compile(r"community", re.I), 1)]
SERVICE = [
    {"key": "entry_price", "label": "Entry price", "weight": 3, "direction": "lower_better"},
    {"key": "mid_price", "label": "Mid-tier price", "weight": 2, "direction": "lower_better"},
    {"key": "free_tier", "label": "Free tier", "weight": 1, "direction": "higher_better"},
    {"key": "india_region", "label": "India region", "weight": 2, "direction": "higher_better"},
    {"key": "support", "label": "Support level", "weight": 1, "direction": "higher_better"},
    {"key": "features", "label": "Key features", "weight": 2, "direction": "higher_better"},
    {"key": "positioning", "label": "Positioning", "weight": 0, "direction": "info"},
]


class Criterion(BaseModel):
    key: str
    label: str
    weight: int = Field(ge=0, le=5)
    direction: Literal["lower_better", "higher_better", "info"]
    enabled: bool = True


class CriterionIn(BaseModel):
    key: str
    enabled: bool
    weight: int = Field(ge=0, le=5)


class CriteriaIn(BaseModel):
    criteria: list[CriterionIn]


def _rupees(v: float, unit: str = "/mo") -> str:
    from app.modules.simulator.service import inr
    return f"{inr(v)}{unit}"


def _cell(value, display: str, observed_at=None, source_url=None, evidence_id=None) -> dict:
    return {"value": value, "display": display, "observed_at": observed_at, "source_url": source_url, "evidence_id": evidence_id,
            "known": value is not None}


def _unknown() -> dict:
    return _cell(None, "Unknown")


def competitor_cells(fields: dict, page_text: str, src: dict) -> dict:
    meta = {"observed_at": src["observed_at"], "source_url": src["url"], "evidence_id": src["snapshot_id"]}
    prices = sorted(p for p in (monthly_inr(pl["price"], USD_INR_RATE) for pl in fields.get("plans", [])) if p is not None)
    unit = "" if all(pl["price"].get("period") in ("one_time", None) for pl in fields.get("plans", [])) else "/mo"
    features = {f for pl in fields.get("plans", []) for f in pl.get("features", [])}
    support = max((w for f in features for rx, w in SUPPORT if rx.search(f) and "support" in f.lower()), default=None)
    headline = (fields.get("headline") or {}).get("text")
    return {
        "entry_price": _cell(prices[0], _rupees(prices[0], unit), **meta) if prices else _unknown(),
        "mid_price": _cell(prices[len(prices) // 2], _rupees(prices[len(prices) // 2], unit), **meta) if len(prices) >= 2 else _unknown(),
        "free_tier": _cell(int(prices[0] == 0), "Yes" if prices[0] == 0 else "No", **meta) if prices else _unknown(),
        "india_region": _cell(1, "Yes", **meta) if INDIA.search(page_text or "") else (_cell(0, "Not stated", **meta) if page_text else _unknown()),
        "support": _cell(support, {1: "Community", 2: "Email or chat", 3: "Priority or phone"}[support], **meta) if support else _unknown(),
        "features": _cell(len(features), f"{len(features)} listed", **meta) if features else _unknown(),
        "positioning": _cell(headline, headline, **meta) if headline else _unknown(),
    }


def your_cells(card: dict) -> dict:
    price = monthly_inr(card_value(card, "price"), USD_INR_RATE)
    markets = card_value(card, "india_markets") or []
    attrs = card_value(card, "attributes") or []
    return {
        "entry_price": _cell(price, _rupees(price, "" if (card_value(card, "price") or {}).get("period") == "one_time" else "/mo"),
                             source_url="your card") if price is not None else _unknown(),
        "mid_price": _unknown(), "free_tier": _unknown(),
        "india_region": _cell(1, "Yes", source_url="your card") if markets else _unknown(),
        "support": _unknown(),
        "features": _cell(len(attrs), f"{len(attrs)} listed", source_url="your card") if attrs else _unknown(),
        "positioning": _unknown(),
    }


def _criteria(conn: Connection, profile_id: UUID, offering: str) -> tuple[str, list[dict]]:
    template = "service" if offering == "service" else "product"
    row = conn.execute(text("select criteria from criteria_configs where profile_id = :p"), {"p": profile_id}).scalar()
    saved = {c["key"]: c for c in (row or [])}
    return template, [{**c, "enabled": saved.get(c["key"], {}).get("enabled", True), "weight": saved.get(c["key"], {}).get("weight", c["weight"])}
                      for c in SERVICE]


@router.get("/profiles/{profile_id}/comparison")
def comparison(profile_id: UUID, user: UserDep, conn: ConnDep, set: Literal["comparable", "inspiration"] = "comparable") -> dict:
    profile = conn.execute(text("select name, offering_type, card from profiles where id = :p and user_id = :u"),
                           {"p": profile_id, "u": user.id}).mappings().first()
    if profile is None:
        raise HTTPException(404, {"code": "not_found", "message": "Profile not found."})
    template, criteria = _criteria(conn, profile_id, profile["offering_type"])
    comps = conn.execute(text("""
        select c.id, c.name, c.is_demo_data,
               (select json_build_object('snapshot_id', sn.id, 'observed_at', sn.observed_at, 'url', s.url, 'text', sn.text, 'fields', o.fields)
                from sources s join snapshots sn on sn.source_id = s.id join observations o on o.snapshot_id = sn.id
                where s.competitor_id = c.id and sn.status = 'ok' order by sn.observed_at desc limit 1) as latest
        from competitors c where c.profile_id = :p and c.selected and c.relation = :r order by c.created_at
    """), {"p": profile_id, "r": set}).mappings().all()
    rows = [{"subject": "you", "competitor_id": None, "name": f"{profile['name']} (you)", "is_demo_data": False,
             "cells": your_cells(profile["card"] or {})}]
    for c in comps:
        latest = c["latest"]
        cells = competitor_cells(latest["fields"], latest["text"], latest) if latest else {k["key"]: _unknown() for k in SERVICE}
        rows.append({"subject": "competitor", "competitor_id": c["id"], "name": c["name"], "is_demo_data": c["is_demo_data"], "cells": cells})
    scored = sorted(score_rows(rows, criteria), key=lambda r: (not r["ranked"], -(r["score"] or 0)))
    return {"template": template, "set": set, "criteria": criteria, "rows": scored, "assumptions": {"USD_INR_RATE": USD_INR_RATE}}


@router.put("/profiles/{profile_id}/criteria")
def put_criteria(profile_id: UUID, body: CriteriaIn, user: UserDep, conn: ConnDep, set: Literal["comparable", "inspiration"] = "comparable") -> dict:
    offering = conn.execute(text("select offering_type from profiles where id = :p and user_id = :u"), {"p": profile_id, "u": user.id}).scalar()
    if offering is None:
        raise HTTPException(404, {"code": "not_found", "message": "Profile not found."})
    conn.execute(text("""insert into criteria_configs (profile_id, template, criteria) values (:p, :t, cast(:c as jsonb))
        on conflict (profile_id) do update set criteria = excluded.criteria"""),
                 {"p": profile_id, "t": "service" if offering == "service" else "product", "c": json.dumps([c.model_dump() for c in body.criteria])})
    return comparison(profile_id, user, conn, set)

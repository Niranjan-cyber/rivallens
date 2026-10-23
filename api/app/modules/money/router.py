"""B14e Money dashboard (UC-17, S-24): uploads with a mapping preview, manual entries, metrics against the India benchmark."""
import json
from datetime import date
from typing import Annotated, Literal
from uuid import UUID

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from pydantic import BaseModel, Field
from sqlalchemy import Connection, text

from app.auth import UserDep
from app.db import ConnDep
from app.modules.money.service import benchmark, industries, metrics, parse_table, suggest_mapping, to_transactions
from app.modules.products.taxonomy import tokens

router = APIRouter(prefix="/api/v1", tags=["money"])
MAX_UPLOAD = 5 * 1024 * 1024
FIELDS = {"date", "amount", "credit", "debit", "quantity", "unit_price", "product", "description", "kind"}


def _own(conn: Connection, profile_id: UUID, user_id: UUID) -> dict:
    row = conn.execute(text("select card, is_demo_data from profiles where id = :p and user_id = :u"), {"p": profile_id, "u": user_id}).mappings().first()
    if not row:
        raise HTTPException(404, {"code": "not_found", "message": "Business not found."})
    return dict(row)


async def _read(file: UploadFile) -> tuple[list[str], list[dict]]:
    data = await file.read(MAX_UPLOAD + 1)
    if len(data) > MAX_UPLOAD:
        raise HTTPException(413, {"code": "too_large", "message": "Files up to 5 MB. Split the export by date range."})
    if not (file.filename or "").lower().endswith((".csv", ".txt", ".xlsx", ".xlsm")):
        raise HTTPException(415, {"code": "bad_type", "message": "Upload a CSV or Excel (.xlsx) file."})
    try:
        return parse_table(file.filename or "upload.csv", data)
    except Exception:
        raise HTTPException(422, {"code": "unreadable", "message": "We couldn't read that file. Export it again as CSV or .xlsx."})


@router.post("/profiles/{profile_id}/money/preview")
async def preview_upload(profile_id: UUID, user: UserDep, conn: ConnDep, file: Annotated[UploadFile, File()]) -> dict:
    _own(conn, profile_id, user.id)
    headers, rows = await _read(file)
    mapping = suggest_mapping(headers)
    sample = to_transactions(rows[:200], mapping, file.filename or "")[:8]
    return {"filename": file.filename, "headers": headers, "rows": len(rows), "mapping": mapping,
            "raw_sample": [{h: str(r.get(h) if r.get(h) is not None else "")[:60] for h in headers} for r in rows[:5]],
            "parsed_sample": [t | {"date": t["date"].isoformat()} for t in sample]}


@router.post("/profiles/{profile_id}/money/import", status_code=201)
async def import_upload(profile_id: UUID, user: UserDep, conn: ConnDep, file: Annotated[UploadFile, File()],
                        mapping: Annotated[str, Form()]) -> dict:
    profile = _own(conn, profile_id, user.id)
    headers, rows = await _read(file)
    m = {k: v for k, v in json.loads(mapping).items() if k in FIELDS and v in headers}
    if "date" not in m or not ({"amount", "credit", "debit"} & m.keys() or {"quantity", "unit_price"} <= m.keys()):
        raise HTTPException(422, {"code": "mapping", "message": "Pick a date column and an amount (or debit/credit, or quantity and price)."})
    txs = to_transactions(rows, m, file.filename or "upload")
    conn.execute(text("delete from transactions where profile_id = :p and source = :s"), {"p": profile_id, "s": file.filename})  # re-upload replaces
    if txs:
        conn.execute(text("""insert into transactions (profile_id, date, kind, amount, product, quantity, description, source, is_demo_data)
                             values (:p, :date, :kind, :amount, :product, :quantity, :description, :source, :demo)"""),
                     [t | {"p": profile_id, "demo": profile["is_demo_data"]} for t in txs])
    return {"imported": len(txs), "skipped": len(rows) - len(txs)}


class TransactionIn(BaseModel):
    date: date
    kind: Literal["sale", "expense", "funding"]
    amount: float = Field(gt=0)
    product: str | None = Field(None, max_length=160)
    quantity: float | None = None
    description: str | None = Field(None, max_length=300)


@router.post("/profiles/{profile_id}/money/transactions", status_code=201)
def add_transaction(profile_id: UUID, body: TransactionIn, user: UserDep, conn: ConnDep) -> dict:
    profile = _own(conn, profile_id, user.id)
    conn.execute(text("""insert into transactions (profile_id, date, kind, amount, product, quantity, description, source, is_demo_data)
                         values (:p, :date, :kind, :amount, :product, :quantity, :description, 'manual', :demo)"""),
                 body.model_dump() | {"p": profile_id, "demo": profile["is_demo_data"]})
    return {"ok": True}


@router.delete("/profiles/{profile_id}/money/sources/{source}", status_code=204)
def delete_source(profile_id: UUID, source: str, user: UserDep, conn: ConnDep) -> None:
    _own(conn, profile_id, user.id)
    conn.execute(text("delete from transactions where profile_id = :p and source = :s"), {"p": profile_id, "s": source})


class SettingsIn(BaseModel):
    cash: float | None = Field(None, ge=0)
    industry: str | None = None


@router.put("/profiles/{profile_id}/money/settings")
def save_settings(profile_id: UUID, body: SettingsIn, user: UserDep, conn: ConnDep) -> dict:
    _own(conn, profile_id, user.id)
    if body.industry and not benchmark(body.industry):
        raise HTTPException(422, {"code": "industry", "message": "Unknown industry."})
    conn.execute(text("""insert into money_settings (profile_id, cash, cash_as_of, industry) values (:p, :c, current_date, :i)
                         on conflict (profile_id) do update set cash = excluded.cash, cash_as_of = excluded.cash_as_of,
                           industry = excluded.industry, updated_at = now()"""), {"p": profile_id, "c": body.cash, "i": body.industry})
    return {"ok": True}


def guess_industry(conn: Connection, profile_id: UUID, card: dict) -> str | None:
    """Damodaran industry whose name shares the most words with the business's product categories and description."""
    paths = [r[0] for r in conn.execute(text("select category_path from products where profile_id = :p and category_path is not null"), {"p": profile_id})]
    v = lambda k: str((card.get(k) or {}).get("value") or "")
    words = tokens(" ".join(paths + [v("industry"), v("category"), v("business_type"), v("description")]), query=True)
    best = max(industries(), key=lambda i: (len(tokens(i) & words), -len(i)))
    return best if tokens(best) & words else None


def money_summary(conn: Connection, profile_id: UUID, card: dict) -> dict:
    """Shared with the overview and the simulator (B14i)."""
    s = conn.execute(text("select cash, cash_as_of, industry from money_settings where profile_id = :p"), {"p": profile_id}).mappings().first()
    rows = [dict(r) for r in conn.execute(text("""select date, kind, amount::float as amount, product, quantity::float as quantity
                                                  from transactions where profile_id = :p"""), {"p": profile_id}).mappings()]
    cash = float(s["cash"]) if s and s["cash"] is not None else None
    industry = (s and s["industry"]) or guess_industry(conn, profile_id, card)
    return {"cash": cash, "cash_as_of": s["cash_as_of"].isoformat() if s and s["cash_as_of"] else None, "industry": industry,
            "industry_guessed": not (s and s["industry"]), "benchmark": benchmark(industry), "metrics": metrics(rows, cash),
            "transactions_count": len(rows)}


@router.get("/profiles/{profile_id}/money")
def get_money(profile_id: UUID, user: UserDep, conn: ConnDep) -> dict:
    profile = _own(conn, profile_id, user.id)
    out = money_summary(conn, profile_id, profile["card"] or {})
    out["recent"] = [dict(r) | {"date": r["date"].isoformat()} for r in conn.execute(text("""
        select date, kind, amount::float as amount, product, quantity::float as quantity, description, source from transactions
        where profile_id = :p order by date desc, created_at desc limit 50"""), {"p": profile_id}).mappings()]
    out["sources"] = [dict(r) for r in conn.execute(text("""select source, count(*) as rows, min(date)::text as first, max(date)::text as last
        from transactions where profile_id = :p group by source order by source"""), {"p": profile_id}).mappings()]
    out["industries"] = industries()
    return out

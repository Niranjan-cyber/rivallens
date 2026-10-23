"""Sign-up with email and password, no confirmation email (D-83): the API creates the user already confirmed with the
server key; the browser then signs in with the same password. Nothing to configure in Supabase or Gmail."""
import httpx
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.config import SUPABASE_SECRET_KEY, SUPABASE_URL

router = APIRouter(prefix="/api/v1/accounts", tags=["accounts"])


class SignUpIn(BaseModel):
    email: str = Field(pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]+$", max_length=254)
    password: str = Field(min_length=6, max_length=72)
    name: str | None = Field(None, max_length=80)


@router.post("", status_code=201)
def sign_up(body: SignUpIn) -> dict:
    r = httpx.post(f"{SUPABASE_URL}/auth/v1/admin/users", timeout=15,
                   headers={"apikey": SUPABASE_SECRET_KEY, "Authorization": f"Bearer {SUPABASE_SECRET_KEY}"},
                   json={"email": body.email, "password": body.password, "email_confirm": True, "user_metadata": {"name": body.name or ""}})
    if r.status_code in (200, 201):
        return {"ok": True}
    msg = (r.json().get("msg") or r.json().get("message") or "") if r.headers.get("content-type", "").startswith("application/json") else ""
    if r.status_code == 422 and "already" in msg.lower():
        raise HTTPException(409, {"code": "exists", "message": "That email already has an account. Log in instead."})
    if r.status_code == 422:
        raise HTTPException(422, {"code": "weak_password", "message": msg or "Use a longer password."})
    raise HTTPException(502, {"code": "auth_unavailable", "message": "Couldn't create the account right now. Try again in a minute."})

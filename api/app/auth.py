from dataclasses import dataclass
from typing import Annotated
from uuid import UUID

import httpx
import jwt
from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.config import SUPABASE_JWT_SECRET, SUPABASE_PUBLIC_KEY, SUPABASE_URL

_bearer = HTTPBearer(auto_error=False)
_jwks = jwt.PyJWKClient(f"{SUPABASE_URL}/auth/v1/.well-known/jwks.json", cache_keys=True) if SUPABASE_URL else None


@dataclass(frozen=True)
class User:
    id: UUID
    is_anonymous: bool
    email: str | None


def _decode(token: str) -> dict:
    # Current projects sign with asymmetric keys (JWKS, verified locally). Legacy HS256 tokens are verified
    # with the shared secret if we have it, otherwise by asking Supabase Auth (one HTTP call).
    if jwt.get_unverified_header(token).get("alg") != "HS256":
        key = _jwks.get_signing_key_from_jwt(token)
        return jwt.decode(token, key, algorithms=["RS256", "ES256"], audience="authenticated")
    if SUPABASE_JWT_SECRET:
        return jwt.decode(token, SUPABASE_JWT_SECRET, algorithms=["HS256"], audience="authenticated")
    r = httpx.get(f"{SUPABASE_URL}/auth/v1/user", headers={"apikey": SUPABASE_PUBLIC_KEY, "Authorization": f"Bearer {token}"}, timeout=10)
    if r.status_code != 200:
        raise jwt.InvalidTokenError("rejected by Supabase Auth")
    u = r.json()
    return {"sub": u["id"], "is_anonymous": u.get("is_anonymous", False), "email": u.get("email")}


def current_user(creds: Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer)]) -> User:
    if creds is None:
        raise HTTPException(401, {"code": "unauthenticated", "message": "Log in to continue."})
    try:
        claims = _decode(creds.credentials)
    except jwt.PyJWTError:
        raise HTTPException(401, {"code": "invalid_token", "message": "Your session expired. Log in again."})
    return User(id=UUID(claims["sub"]), is_anonymous=bool(claims.get("is_anonymous")), email=claims.get("email"))


UserDep = Annotated[User, Depends(current_user)]

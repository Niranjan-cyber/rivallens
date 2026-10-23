from dataclasses import dataclass
from typing import Annotated
from uuid import UUID

import jwt
from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.config import SUPABASE_JWT_SECRET, SUPABASE_URL

_bearer = HTTPBearer(auto_error=False)
_jwks = jwt.PyJWKClient(f"{SUPABASE_URL}/auth/v1/.well-known/jwks.json", cache_keys=True) if SUPABASE_URL else None


@dataclass(frozen=True)
class User:
    id: UUID
    is_anonymous: bool
    email: str | None


def _decode(token: str) -> dict:
    # Legacy projects sign with a shared HS256 secret; current ones publish asymmetric keys via JWKS.
    if SUPABASE_JWT_SECRET:
        return jwt.decode(token, SUPABASE_JWT_SECRET, algorithms=["HS256"], audience="authenticated")
    key = _jwks.get_signing_key_from_jwt(token)
    return jwt.decode(token, key, algorithms=["RS256", "ES256"], audience="authenticated")


def current_user(creds: Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer)]) -> User:
    if creds is None:
        raise HTTPException(401, {"code": "unauthenticated", "message": "Log in to continue."})
    try:
        claims = _decode(creds.credentials)
    except jwt.PyJWTError:
        raise HTTPException(401, {"code": "invalid_token", "message": "Your session expired. Log in again."})
    return User(id=UUID(claims["sub"]), is_anonymous=bool(claims.get("is_anonymous")), email=claims.get("email"))


UserDep = Annotated[User, Depends(current_user)]

import time
import uuid

import jwt
import pytest

from app import auth

SECRET = "test-secret-at-least-32-bytes-long-000"


def token(iat_offset: int = 0, exp_offset: int = 3600) -> str:
    now = int(time.time())
    claims = {"sub": str(uuid.uuid4()), "aud": "authenticated", "iat": now + iat_offset, "exp": now + exp_offset}
    return jwt.encode(claims, SECRET, algorithm="HS256")


@pytest.fixture(autouse=True)
def secret(monkeypatch):
    monkeypatch.setattr(auth, "SUPABASE_JWT_SECRET", SECRET)


def test_fresh_token_from_a_slightly_fast_auth_clock_is_accepted():
    # Supabase's clock ran ~1 s ahead: a token used right after sign-in had iat in the future and every call got 401
    assert auth._decode(token(iat_offset=5))["aud"] == "authenticated"


def test_expired_token_is_still_rejected():
    with pytest.raises(jwt.ExpiredSignatureError):
        auth._decode(token(iat_offset=-7200, exp_offset=-120))

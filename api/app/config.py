import os

from dotenv import load_dotenv

load_dotenv()  # local dev only; Render provides real env vars

WEB_ORIGIN = os.getenv("WEB_ORIGIN", "http://localhost:3000")
GIT_SHA = os.getenv("RENDER_GIT_COMMIT", "dev")[:7]

SUPABASE_URL = os.getenv("SUPABASE_URL", "").rstrip("/")
SUPABASE_SECRET_KEY = os.getenv("SUPABASE_SECRET_KEY", "")
SUPABASE_JWT_SECRET = os.getenv("SUPABASE_JWT_SECRET", "")  # only if the project still signs with the legacy HS256 secret
DATABASE_URL = os.getenv("DATABASE_URL", "")
MOCK_BASE_URL = os.getenv("MOCK_BASE_URL", f"{WEB_ORIGIN}/mock")
SEED_USER_EMAIL = os.getenv("SEED_USER_EMAIL", "seed@rivallens.demo")

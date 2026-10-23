import os

from dotenv import load_dotenv

load_dotenv()  # local dev only; Render provides real env vars

WEB_ORIGIN = os.getenv("WEB_ORIGIN", "http://localhost:3000")
GIT_SHA = os.getenv("RENDER_GIT_COMMIT", "dev")[:7]

SUPABASE_URL = os.getenv("SUPABASE_URL", "").strip().rstrip("/")
SUPABASE_SECRET_KEY = os.getenv("SUPABASE_SECRET_KEY") or os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")
SUPABASE_PUBLIC_KEY = os.getenv("SUPABASE_PUBLISHABLE_KEY") or os.getenv("SUPABASE_ANON_KEY", "")
SUPABASE_JWT_SECRET = os.getenv("SUPABASE_JWT_SECRET", "")  # only if the project still signs with the legacy HS256 secret
DATABASE_URL = os.getenv("DATABASE_URL", "").strip()  # dashboard pastes can carry a trailing newline
MOCK_BASE_URL = os.getenv("MOCK_BASE_URL", f"{WEB_ORIGIN}/mock")
SEED_USER_EMAIL = os.getenv("SEED_USER_EMAIL", "seed@rivallens.demo")
RESEND_API_KEY = os.getenv("RESEND_API_KEY", "").strip()
ALERT_FROM = os.getenv("ALERT_FROM", "RivalLens <onboarding@resend.dev>")
ALERT_EMAIL_OVERRIDE = os.getenv("ALERT_EMAIL_OVERRIDE", "").strip()  # P1: the Resend account owner's address

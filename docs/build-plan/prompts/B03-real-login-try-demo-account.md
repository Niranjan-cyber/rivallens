# B03 — Real login + Try demo account

Build step B03 of **RivalLens (working name)** (Prototype). Paste this into Claude Code / Codex / Cursor at the repo root. Do only this step.

## Read first
- `docs/build-plan/BUILD-PLAN.md` (section B03) and `docs/build-plan/plan.json`
- `AGENTS.md`, `SKILL-PLAYBOOK.md`, `SKILLS.md`
- `hacknova26-competitor-intel-feature-scope.md` (Feature scope: only if the step touches scope or cut list; grep the heading)
- `hacknova26-competitor-intel-user-journeys.md` (User journeys: grep only the screens (S-xx) and use cases (UC-xx) this step lists)
- `hacknova26-competitor-intel-architecture.md` (Architecture: grep only the ADRs/components (C-xx) this step lists)
- `hacknova26-competitor-intel-specs.md` (Specs: grep only the sections this step cites (e.g. '### C-08', '## 2. API contracts' endpoint names))
- `fixtures/README.md` (Fixtures README: only for parser/test steps; never open raw HTML fixtures)

## The goal (the only goal of this step)
A visitor can click 'Try demo account' or sign up with email and land on S-03 showing profiles stored in Supabase for their own account.

**Why now:** Auth touches every later endpoint (user_id scoping); JWT verification and the pooler connection are a known risk best hit early.

## Slice
- Use cases: UC-01, UC-13
- Screens: S-01, S-02, S-03
- Components: C-01, C-03, C-13, C-15, C-17
- Stack: frontend: Next.js 15 App Router + TS + Tailwind + shadcn/ui on Vercel (root: web/); backend: FastAPI + SQLAlchemy 2 + psycopg 3 on Render Free, Singapore (root: api/); data: Supabase Free: Postgres (session pooler), Auth (email + anonymous), Storage bucket 'snapshots'; ai: Gemini free (primary) + Groq free (fallback) via LLM gateway with Postgres cache; integrations: Tavily search, Resend email, Internet Archive CDX

## In scope
- Supabase project; enable email/password + anonymous sign-ins
- Migration supabase/migrations/0001_core.sql: profiles, competitors, sources, mock_instances, usage_counters (specs §3), RLS enabled
- S-02 sign-up / log-in tabs + 'Try demo account' (signInAnonymously) via @supabase/ssr
- FastAPI auth dependency: verify Supabase JWT (JWKS or legacy HS256, whichever the project uses), user_id scoping; 404 on foreign ids
- scripts/seed.py: creates SEED_USER_ID with 4 profiles (cards only for now) + 3 fictional mock competitors (NimbusDeploy (demo), KiteHost (demo), Orbitly Cloud (demo)); re-runnable
- POST /api/v1/demo/guest-clone (specs §2) deep-copies seed rows + creates mock_instances; GET /profiles now reads the DB
- Logout; profile switcher in the top bar lists the user's profiles

## Out of scope for this step
- Profile creation wizard (B07)
- Guest rate limits beyond a simple usage_counters check (B08)
- Email verification (MVP)

## Suggested tasks
- Create Supabase project (same region as Render if offered: Singapore)
- DATABASE_URL = session pooler URI on Render; SUPABASE_URL + keys on Render and Vercel
- app/auth.py: JWT verification + current_user dependency
- app/modules/demo: guest-clone
- web: middleware for session, S-02 page, logout
- Run seed.py against the live DB

## Skills — use in this order
1. **supabase** — anonymous sign-in, @supabase/ssr session in Next.js, JWT verification on the API, pooler connection string
2. **supabase-postgres-best-practices** — 0001_core.sql tables, FKs, indexes, RLS on
3. **fastapi** — only if not loaded this session: auth dependency with Annotated

Always-on rules for every step: **ponytail**.

## Done when (check on the deployed app, not locally)
1. Open <FRONTEND_URL> in a private window → Try demo account → S-03 lists the 4 seeded profiles (demo badges)
2. A second private window's guest sees its own copy (deleting a profile in one doesn't affect the other)
3. Sign up with an email → empty S-03 with 'Create your first profile' → log out → log in → still the same account
4. curl <BACKEND_URL>/api/v1/profiles without a token returns 401

## If it goes wrong
If JWKS verification fights you, call Supabase /auth/v1/user with the token (one HTTP call per request) behind the same dependency.

## When finished
1. Make sure everything above is deployed (frontend, backend, database) and the done-check passes on the public URL.
2. Set `"status": "done"` for B03 in `docs/build-plan/plan.json`, then run `python C:\Users\Niranjan Iyer\.claude\skills\synced\4388f05c-eb72-4dd8-a66b-700dfbb34581_a5c3319d-ef87-457c-8cc8-fe986ddce72a\prototype-build-planner\scripts\build_plan.py render docs/build-plan/plan.json`.
3. Commit as `B03: Real login + Try demo account`.
4. Report what changed and the done-check result, then stop. Don't start the next step without being asked.

## Notes
Supabase direct DB host may be IPv6-only on free: use the session pooler URI.


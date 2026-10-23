# B02 — Walking skeleton: web ↔ deployed API

Build step B02 of **RivalLens (working name)** (Prototype). Paste this into Claude Code / Codex / Cursor at the repo root. Do only this step.

## Read first
- `docs/build-plan/BUILD-PLAN.md` (section B02) and `docs/build-plan/plan.json`
- `AGENTS.md`, `SKILL-PLAYBOOK.md`, `SKILLS.md`
- `hacknova26-competitor-intel-feature-scope.md` (Feature scope: only if the step touches scope or cut list; grep the heading)
- `hacknova26-competitor-intel-user-journeys.md` (User journeys: grep only the screens (S-xx) and use cases (UC-xx) this step lists)
- `hacknova26-competitor-intel-architecture.md` (Architecture: grep only the ADRs/components (C-xx) this step lists)
- `hacknova26-competitor-intel-specs.md` (Specs: grep only the sections this step cites (e.g. '### C-08', '## 2. API contracts' endpoint names))
- `fixtures/README.md` (Fixtures README: only for parser/test steps; never open raw HTML fixtures)

## The goal (the only goal of this step)
S-03 Home on the public URL lists profile cards fetched from the deployed FastAPI service.

**Why now:** Proves Vercel → Render CORS, env vars and the API contract before any real logic; also starts the Render cold-start clock early.

## Slice
- Use cases: UC-13
- Screens: S-03
- Components: C-01, C-03, C-24
- Stack: frontend: Next.js 15 App Router + TS + Tailwind + shadcn/ui on Vercel (root: web/); backend: FastAPI + SQLAlchemy 2 + psycopg 3 on Render Free, Singapore (root: api/); data: Supabase Free: Postgres (session pooler), Auth (email + anonymous), Storage bucket 'snapshots'; ai: Gemini free (primary) + Groq free (fallback) via LLM gateway with Postgres cache; integrations: Tavily search, Resend email, Internet Archive CDX

## In scope
- api/ FastAPI app: GET /healthz (git sha), GET /api/v1/profiles returning the 4 seed ProfileSummary objects from a fixture JSON (specs §2 Profiles shape)
- Render web service: Free, Singapore, root api/, auto-deploy on push
- CORS allow-list WEB_ORIGIN; NEXT_PUBLIC_API_BASE_URL on Vercel
- S-03 renders cards from the API with a 'Sample data' badge
- Extend scripts/smoke.sh: curl <BACKEND_URL>/healthz

## Out of scope for this step
- Database (B03)
- Auth header (B03)
- Profile creation (B07)

## Suggested tasks
- api/app/main.py + modules layout from specs §1 C-03 (create only what this step needs)
- requirements.txt with pinned versions; start command uvicorn app.main:app --host 0.0.0.0 --port $PORT
- Create Render service (Render MCP or render-deploy flow), set WEB_ORIGIN
- web/lib/api.ts fetch wrapper with base URL + error mapping
- S-03 page fetches /profiles

## Skills — use in this order
1. **fastapi** — app layout, Annotated deps, response models for /profiles
2. **render-deploy** — first and only load: create the Render web service (Singapore, Free) and env vars
3. **render-debug** — only if the first deploy fails (port binding, build errors)

Always-on rules for every step: **ponytail**.

## Done when (check on the deployed app, not locally)
1. curl <BACKEND_URL>/healthz returns {ok:true, version}
2. Open <FRONTEND_URL> → S-03 shows the 4 profile cards served by the API (check the Network tab), 'Sample data' badge visible
3. bash scripts/smoke.sh passes for both URLs

## If it goes wrong
If Render build hangs, run the API locally only for development and keep S-03 on a static fixture until fixed; don't block B03 frontend work.

## When finished
1. Make sure everything above is deployed (frontend, backend) and the done-check passes on the public URL.
2. Set `"status": "done"` for B02 in `docs/build-plan/plan.json`, then run `python C:\Users\Niranjan Iyer\.claude\skills\synced\4388f05c-eb72-4dd8-a66b-700dfbb34581_a5c3319d-ef87-457c-8cc8-fe986ddce72a\prototype-build-planner\scripts\build_plan.py render docs/build-plan/plan.json`.
3. Commit as `B02: Walking skeleton: web ↔ deployed API`.
4. Report what changed and the done-check result, then stop. Don't start the next step without being asked.

## Notes
Set up the C-25 keep-warm pinger later (B14); Render may sleep during dev, which is fine.


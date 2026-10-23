# B17 — MVP exit: real users, verified email, CI

Build step B17 of **RivalLens (working name)** (MVP — 🏁 MVP exit). Paste this into Claude Code / Codex / Cursor at the repo root. Do only this step.

## Read first
- `docs/build-plan/BUILD-PLAN.md` (section B17) and `docs/build-plan/plan.json`
- `AGENTS.md`, `SKILL-PLAYBOOK.md`, `SKILLS.md`
- `hacknova26-competitor-intel-feature-scope.md` (Feature scope: only if the step touches scope or cut list; grep the heading)
- `hacknova26-competitor-intel-user-journeys.md` (User journeys: grep only the screens (S-xx) and use cases (UC-xx) this step lists)
- `hacknova26-competitor-intel-architecture.md` (Architecture: grep only the ADRs/components (C-xx) this step lists)
- `hacknova26-competitor-intel-specs.md` (Specs: grep only the sections this step cites (e.g. '### C-08', '## 2. API contracts' endpoint names))
- `fixtures/README.md` (Fixtures README: only for parser/test steps; never open raw HTML fixtures)

## The goal (the only goal of this step)
Any signed-up user receives alert emails from a verified domain and every push runs the test suite in replay mode before deploying.

**Why now:** Closes the remaining MVP migrations.

## Slice
- Use cases: UC-08, UC-15
- Screens: S-02, S-16
- Components: C-09, C-21, C-24, C-27
- Stack: frontend: Next.js 15 App Router + TS + Tailwind + shadcn/ui on Vercel (root: web/); backend: FastAPI + SQLAlchemy 2 + psycopg 3 on Render Free, Singapore (root: api/); data: Supabase Free: Postgres (session pooler), Auth (email + anonymous), Storage bucket 'snapshots'; ai: Gemini free (primary) + Groq free (fallback) via LLM gateway with Postgres cache; integrations: Tavily search, Resend email, Internet Archive CDX

## In scope
- Verify a domain on Resend; remove ALERT_EMAIL_OVERRIDE
- Email verification + password reset in Supabase Auth
- GitHub Actions: pytest (LLM_MODE=replay) + web build
- Per-user rate limits

## Out of scope for this step
- Production items (staging, RLS policies, worker queue)

## Suggested tasks
- Domain DNS
- Auth settings
- CI workflow

## Skills — use in this order
1. **supabase** — email verification and password reset flows
2. **code-review** — review the MVP diff before tagging

Always-on rules for every step: **ponytail**.

## Done when (check on the deployed app, not locally)
1. A new email user on <FRONTEND_URL> verifies their address and receives a High alert email from the verified domain
2. A failing test blocks the GitHub Actions run

## If it goes wrong
Keep main deployed and the golden path working; if this can't land, revert to the previous step's behaviour and report.

## When finished
1. Make sure everything above is deployed (frontend, backend, infra) and the done-check passes on the public URL.
2. Set `"status": "done"` for B17 in `docs/build-plan/plan.json`, then run `python C:\Users\Niranjan Iyer\.claude\skills\synced\4388f05c-eb72-4dd8-a66b-700dfbb34581_a5c3319d-ef87-457c-8cc8-fe986ddce72a\prototype-build-planner\scripts\build_plan.py render docs/build-plan/plan.json`.
3. Commit as `B17: MVP exit: real users, verified email, CI`.
4. Report what changed and the done-check result, then stop. Don't start the next step without being asked.

## Notes
Described only.


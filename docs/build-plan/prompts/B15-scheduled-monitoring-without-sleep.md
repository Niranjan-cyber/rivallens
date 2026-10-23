# B15 — Scheduled monitoring without sleep

Build step B15 of **RivalLens (working name)** (MVP). Paste this into Claude Code / Codex / Cursor at the repo root. Do only this step.

## Read first
- `docs/build-plan/BUILD-PLAN.md` (section B15) and `docs/build-plan/plan.json`
- `AGENTS.md`, `SKILL-PLAYBOOK.md`, `SKILLS.md`
- `hacknova26-competitor-intel-feature-scope.md` (Feature scope: only if the step touches scope or cut list; grep the heading)
- `hacknova26-competitor-intel-user-journeys.md` (User journeys: grep only the screens (S-xx) and use cases (UC-xx) this step lists)
- `hacknova26-competitor-intel-architecture.md` (Architecture: grep only the ADRs/components (C-xx) this step lists)
- `hacknova26-competitor-intel-specs.md` (Specs: grep only the sections this step cites (e.g. '### C-08', '## 2. API contracts' endpoint names))
- `fixtures/README.md` (Fixtures README: only for parser/test steps; never open raw HTML fixtures)

## The goal (the only goal of this step)
A user's competitors are re-checked on a schedule and new alerts appear without anyone clicking Run monitor.

**Why now:** First MVP migration (button → cron; Render Free → Starter). Post-hackathon.

## Slice
- Use cases: UC-04, UC-08
- Screens: S-09, S-16, S-17
- Components: C-03, C-26, C-27
- Stack: frontend: Next.js 15 App Router + TS + Tailwind + shadcn/ui on Vercel (root: web/); backend: FastAPI + SQLAlchemy 2 + psycopg 3 on Render Free, Singapore (root: api/); data: Supabase Free: Postgres (session pooler), Auth (email + anonymous), Storage bucket 'snapshots'; ai: Gemini free (primary) + Groq free (fallback) via LLM gateway with Postgres cache; integrations: Tavily search, Resend email, Internet Archive CDX

## In scope
- Render Starter (no sleep), remove keep-warm
- profiles.monitor_cadence + S-17 cadence picker
- Render Cron → POST /internal/monitor-due with INTERNAL_TOKEN
- Sentry on web + API

## Out of scope for this step
- Worker queue (Production)

## Suggested tasks
- Migration
- Internal endpoint
- Cron service
- Sentry

## Skills — use in this order
1. **render-deploy** — add the cron job service
2. **fastapi** — internal endpoint with token dependency

Always-on rules for every step: **ponytail**.

## Done when (check on the deployed app, not locally)
1. Set cadence to hourly on <FRONTEND_URL> → within the hour S-09 shows a new run not started by you
2. Sentry shows a test error from both apps

## If it goes wrong
GitHub Actions schedule hitting the same endpoint.

## When finished
1. Make sure everything above is deployed (backend, worker, database) and the done-check passes on the public URL.
2. Set `"status": "done"` for B15 in `docs/build-plan/plan.json`, then run `python C:\Users\Niranjan Iyer\.claude\skills\synced\4388f05c-eb72-4dd8-a66b-700dfbb34581_a5c3319d-ef87-457c-8cc8-fe986ddce72a\prototype-build-planner\scripts\build_plan.py render docs/build-plan/plan.json`.
3. Commit as `B15: Scheduled monitoring without sleep`.
4. Report what changed and the done-check result, then stop. Don't start the next step without being asked.

## Notes
Described only for the hackathon (roadmap slide).


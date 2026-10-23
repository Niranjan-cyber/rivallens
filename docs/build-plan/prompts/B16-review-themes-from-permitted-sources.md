# B16 — Review themes from permitted sources

Build step B16 of **RivalLens (working name)** (MVP). Paste this into Claude Code / Codex / Cursor at the repo root. Do only this step.

## Read first
- `docs/build-plan/BUILD-PLAN.md` (section B16) and `docs/build-plan/plan.json`
- `AGENTS.md`, `SKILL-PLAYBOOK.md`, `SKILLS.md`
- `hacknova26-competitor-intel-feature-scope.md` (Feature scope: only if the step touches scope or cut list; grep the heading)
- `hacknova26-competitor-intel-user-journeys.md` (User journeys: grep only the screens (S-xx) and use cases (UC-xx) this step lists)
- `hacknova26-competitor-intel-architecture.md` (Architecture: grep only the ADRs/components (C-xx) this step lists)
- `hacknova26-competitor-intel-specs.md` (Specs: grep only the sections this step cites (e.g. '### C-08', '## 2. API contracts' endpoint names))
- `fixtures/README.md` (Fixtures README: only for parser/test steps; never open raw HTML fixtures)

## The goal (the only goal of this step)
S-12 shows review themes (praise, complaints, requests) for a competitor from a permitted source, each with source link, date and sample size.

**Why now:** UC-15, the main MVP Should item from the scope.

## Slice
- Use cases: UC-15
- Screens: S-12
- Components: C-03, C-14, C-15
- Stack: frontend: Next.js 15 App Router + TS + Tailwind + shadcn/ui on Vercel (root: web/); backend: FastAPI + SQLAlchemy 2 + psycopg 3 on Render Free, Singapore (root: api/); data: Supabase Free: Postgres (session pooler), Auth (email + anonymous), Storage bucket 'snapshots'; ai: Gemini free (primary) + Groq free (fallback) via LLM gateway with Postgres cache; integrations: Tavily search, Resend email, Internet Archive CDX

## In scope
- Permitted review source per domain (manual allow-list)
- reviews table
- LLM theme extraction with counts
- Low-sample warning

## Out of scope for this step
- Sentiment trend charts

## Suggested tasks
- Source allow-list
- Ingest + themes
- S-12 section

## Skills — use in this order
1. **supabase-postgres-best-practices** — reviews table + indexes
2. **tdd** — theme aggregation + low-sample warning

Always-on rules for every step: **ponytail**.

## Done when (check on the deployed app, not locally)
1. On <FRONTEND_URL> a competitor's S-12 shows ≥ 3 themes with source links and 'n reviews' counts

## If it goes wrong
Keep the seeded, labelled themes.

## When finished
1. Make sure everything above is deployed (frontend, backend, database) and the done-check passes on the public URL.
2. Set `"status": "done"` for B16 in `docs/build-plan/plan.json`, then run `python C:\Users\Niranjan Iyer\.claude\skills\synced\4388f05c-eb72-4dd8-a66b-700dfbb34581_a5c3319d-ef87-457c-8cc8-fe986ddce72a\prototype-build-planner\scripts\build_plan.py render docs/build-plan/plan.json`.
3. Commit as `B16: Review themes from permitted sources`.
4. Report what changed and the done-check result, then stop. Don't start the next step without being asked.

## Notes
Described only.


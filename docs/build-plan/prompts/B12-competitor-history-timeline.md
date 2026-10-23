# B12 — Competitor history timeline

Build step B12 of **RivalLens (working name)** (Prototype). Paste this into Claude Code / Codex / Cursor at the repo root. Do only this step.

## Read first
- `docs/build-plan/BUILD-PLAN.md` (section B12) and `docs/build-plan/plan.json`
- `AGENTS.md`, `SKILL-PLAYBOOK.md`, `SKILLS.md`
- `hacknova26-competitor-intel-feature-scope.md` (Feature scope: only if the step touches scope or cut list; grep the heading)
- `hacknova26-competitor-intel-user-journeys.md` (User journeys: grep only the screens (S-xx) and use cases (UC-xx) this step lists)
- `hacknova26-competitor-intel-architecture.md` (Architecture: grep only the ADRs/components (C-xx) this step lists)
- `hacknova26-competitor-intel-specs.md` (Specs: grep only the sections this step cites (e.g. '### C-08', '## 2. API contracts' endpoint names))
- `fixtures/README.md` (Fixtures README: only for parser/test steps; never open raw HTML fixtures)

## The goal (the only goal of this step)
S-12 shows a competitor's dated history: current fields, a timeline of runs, receipts or failures, plus a price chart.

**Why now:** Covers UC-11 (historical tracking, a judging criterion) using data that already exists.

## Slice
- Use cases: UC-11
- Screens: S-12, S-08, S-13
- Components: C-03, C-08, C-15, C-22
- Stack: frontend: Next.js 15 App Router + TS + Tailwind + shadcn/ui on Vercel (root: web/); backend: FastAPI + SQLAlchemy 2 + psycopg 3 on Render Free, Singapore (root: api/); data: Supabase Free: Postgres (session pooler), Auth (email + anonymous), Storage bucket 'snapshots'; ai: Gemini free (primary) + Groq free (fallback) via LLM gateway with Postgres cache; integrations: Tavily search, Resend email, Internet Archive CDX

## In scope
- GET /competitors/{id} (fields, timeline, price_series)
- S-12 with a Recharts line chart; links from S-08 and S-13
- Should, only if time: POST /competitors/{id}/archive-backfill using Wayback CDX (fixtures/wayback-cdx), points labelled 'Internet Archive'

## Out of scope for this step
- Review themes (MVP B16)

## Suggested tasks
- Endpoint
- S-12 UI
- Optional backfill

## Skills — use in this order
1. **vercel-react-best-practices** — only the client-component/chart rule if the chart causes hydration issues

Always-on rules for every step: **ponytail**.

## Done when (check on the deployed app, not locally)
1. On <FRONTEND_URL> StackNest → Competitors → NimbusDeploy (demo) → S-12 shows the ₹1,499 → ₹899 point on the chart and the receipt in the timeline
2. A failed fetch (if any) appears as 'Failed (not a change)'

## If it goes wrong
Skip the Wayback backfill (cut order item 1).

## When finished
1. Make sure everything above is deployed (frontend, backend) and the done-check passes on the public URL.
2. Set `"status": "done"` for B12 in `docs/build-plan/plan.json`, then run `python C:\Users\Niranjan Iyer\.claude\skills\synced\4388f05c-eb72-4dd8-a66b-700dfbb34581_a5c3319d-ef87-457c-8cc8-fe986ddce72a\prototype-build-planner\scripts\build_plan.py render docs/build-plan/plan.json`.
3. Commit as `B12: Competitor history timeline`.
4. Report what changed and the done-check result, then stop. Don't start the next step without being asked.


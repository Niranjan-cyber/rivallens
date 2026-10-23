# B14c — Customers dashboard from permitted sources

Build step B14c of **RivalLens (working name)** (Prototype). Paste this into Claude Code / Codex / Cursor at the repo root. Do only this step.

## Read first
- `docs/build-plan/BUILD-PLAN.md` (section B14c) and `docs/build-plan/plan.json`
- `AGENTS.md`, `SKILL-PLAYBOOK.md`, `SKILLS.md`
- `hacknova26-competitor-intel-feature-scope.md` (Feature scope: only if the step touches scope or cut list; grep the heading)
- `hacknova26-competitor-intel-user-journeys.md` (User journeys: grep only the screens (S-xx) and use cases (UC-xx) this step lists)
- `hacknova26-competitor-intel-architecture.md` (Architecture: grep only the ADRs/components (C-xx) this step lists)
- `hacknova26-competitor-intel-specs.md` (Specs: grep only the sections this step cites (e.g. '### C-08', '## 2. API contracts' endpoint names))
- `fixtures/README.md` (Fixtures README: only for parser/test steps; never open raw HTML fixtures)

## The goal (the only goal of this step)
On Customers, a company sees reviews from its own site, web and news mentions, and uploaded review exports, with sentiment and themes, each linked to its source.

**Why now:** Customer sentiment and requested features are simulator inputs; replaces MVP B16 with a prototype version.

## Slice
- Use cases: UC-18, UC-15
- Screens: S-22
- Components: C-30
- Stack: frontend: Next.js 15 App Router + TS + Tailwind + shadcn/ui on Vercel (root: web/); backend: FastAPI + SQLAlchemy 2 + psycopg 3 on Render Free, Singapore (root: api/); data: Supabase Free: Postgres (session pooler), Auth (email + anonymous), Storage bucket 'snapshots'; ai: Gemini free (primary) + Groq free (fallback) via LLM gateway with Postgres cache; integrations: Tavily search, Resend email, Internet Archive CDX

## In scope
- Own-site reviews: schema.org Review/AggregateRating JSON-LD + review sections, robots respected
- Web/news mentions via Tavily with URL and date
- CSV upload (text, rating, date, source)
- LLM sentiment + themes per batch (cached, replay fixture)
- customer_mentions table

## Out of scope for this step
- Instagram, LinkedIn, X (ToS / paid API)
- YouTube API

## Suggested tasks
- Migration 0012_customers
- collector reuse for review pages
- CSV parser
- themes prompt
- S-22

## Skills — use in this order
1. **tdd** — JSON-LD review parsing on a fixture, CSV parsing
2. **fastapi** — upload + collect job
3. **frontend-design** — S-22

Always-on rules for every step: **ponytail**.

## Done when (check on the deployed app, not locally)
1. On <FRONTEND_URL> Customers: upload the sample CSV → mentions, sentiment split and top themes appear
2. Collect from a real product page with schema.org reviews → reviews listed with a link

## If it goes wrong
CSV upload alone still feeds the simulator.

## When finished
1. Make sure everything above is deployed (frontend, backend, database) and the done-check passes on the public URL.
2. Set `"status": "done"` for B14c in `docs/build-plan/plan.json`, then run `python C:\Users\Niranjan Iyer\.claude\skills\synced\4388f05c-eb72-4dd8-a66b-700dfbb34581_a5c3319d-ef87-457c-8cc8-fe986ddce72a\prototype-build-planner\scripts\build_plan.py render docs/build-plan/plan.json`.
3. Commit as `B14c: Customers dashboard from permitted sources`.
4. Report what changed and the done-check result, then stop. Don't start the next step without being asked.


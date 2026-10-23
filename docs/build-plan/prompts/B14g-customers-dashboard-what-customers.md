# B14g — Customers dashboard: what customers actually want

Build step B14g of **RivalLens (working name)** (Prototype). Paste this into Claude Code / Codex / Cursor at the repo root. Do only this step.

## Read first
- `docs/build-plan/BUILD-PLAN.md` (section B14g) and `docs/build-plan/plan.json`
- `AGENTS.md`, `SKILL-PLAYBOOK.md`, `SKILLS.md`
- `hacknova26-competitor-intel-feature-scope.md` (Feature scope: only if the step touches scope or cut list; grep the heading)
- `hacknova26-competitor-intel-user-journeys.md` (User journeys: grep only the screens (S-xx) and use cases (UC-xx) this step lists)
- `hacknova26-competitor-intel-architecture.md` (Architecture: grep only the ADRs/components (C-xx) this step lists)
- `hacknova26-competitor-intel-specs.md` (Specs: grep only the sections this step cites (e.g. '### C-08', '## 2. API contracts' endpoint names))
- `fixtures/README.md` (Fixtures README: only for parser/test steps; never open raw HTML fixtures)

## The goal (the only goal of this step)
On Customers, a user sees reviews and comments from uploads, their own product pages and web mentions, with sentiment and the top requests, each linked to its source.

**Why now:** The third input to the product decisions; replaces MVP B16.

## Slice
- Use cases: UC-18, UC-15
- Screens: S-26
- Components: C-31
- Stack: frontend: Next.js 15 App Router + TS + Tailwind + shadcn/ui on Vercel (root: web/); backend: FastAPI + SQLAlchemy 2 + psycopg 3 on Render Free, Singapore (root: api/); data: Supabase Free: Postgres (session pooler), Auth (email + anonymous), Storage bucket 'snapshots'; ai: Gemini free (primary) + Groq free (fallback) via LLM gateway with Postgres cache; integrations: Tavily search, Resend email, Internet Archive CDX

## In scope
- customer_mentions (source, url, text, rating, date, product)
- CSV upload (reviews, Meta/LinkedIn/YouTube Studio insight exports)
- Own-site reviews from schema.org Review JSON-LD, robots respected
- Web mentions via Tavily
- LLM: sentiment + themes + requests per batch, each theme citing mention ids (cached, replay)
- Social metrics tiles from insight exports

## Out of scope for this step
- X, Instagram, Facebook APIs (future scope)
- YouTube API (only if time)

## Suggested tasks
- Migration 0013_customers
- parsers + themes task
- S-26

## Skills — use in this order
1. **tdd** — JSON-LD review parsing and CSV import
2. **fastapi** — upload + collect
3. **frontend-design** — S-26

Always-on rules for every step: **ponytail**.

## Done when (check on the deployed app, not locally)
1. On <FRONTEND_URL> upload the sample reviews CSV → sentiment split and top requests, each opening the quoted reviews
2. Collect from a real product page with reviews → listed with links

## If it goes wrong
Upload only.

## When finished
1. Make sure everything above is deployed (frontend, backend, database) and the done-check passes on the public URL.
2. Set `"status": "done"` for B14g in `docs/build-plan/plan.json`, then run `python C:\Users\Niranjan Iyer\.claude\skills\synced\4388f05c-eb72-4dd8-a66b-700dfbb34581_a5c3319d-ef87-457c-8cc8-fe986ddce72a\prototype-build-planner\scripts\build_plan.py render docs/build-plan/plan.json`.
3. Commit as `B14g: Customers dashboard: what customers actually want`.
4. Report what changed and the done-check result, then stop. Don't start the next step without being asked.


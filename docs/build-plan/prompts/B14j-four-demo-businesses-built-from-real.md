# B14j — Four demo businesses built from real data

Build step B14j of **RivalLens (working name)** (Prototype). Paste this into Claude Code / Codex / Cursor at the repo root. Do only this step.

## Read first
- `docs/build-plan/BUILD-PLAN.md` (section B14j) and `docs/build-plan/plan.json`
- `AGENTS.md`, `SKILL-PLAYBOOK.md`, `SKILLS.md`
- `hacknova26-competitor-intel-feature-scope.md` (Feature scope: only if the step touches scope or cut list; grep the heading)
- `hacknova26-competitor-intel-user-journeys.md` (User journeys: grep only the screens (S-xx) and use cases (UC-xx) this step lists)
- `hacknova26-competitor-intel-architecture.md` (Architecture: grep only the ADRs/components (C-xx) this step lists)
- `hacknova26-competitor-intel-specs.md` (Specs: grep only the sections this step cites (e.g. '### C-08', '## 2. API contracts' endpoint names))
- `fixtures/README.md` (Fixtures README: only for parser/test steps; never open raw HTML fixtures)

## The goal (the only goal of this step)
Four demo sign-ins (Stride & Co. footwear, a Pune bakery, StackNest SaaS, QuickKart quick commerce) each open with every dashboard filled by running the pipeline on licensed datasets and real public pages.

**Why now:** Nothing intelligent is hand-written: demo accounts get their inputs from licensed datasets or public pages, and every output is computed by the same pipeline a real user gets.

## Slice
- Use cases: UC-21, UC-16, UC-17, UC-18, UC-19
- Screens: S-21, S-22, S-24, S-25, S-26
- Components: C-28
- Stack: frontend: Next.js 15 App Router + TS + Tailwind + shadcn/ui on Vercel (root: web/); backend: FastAPI + SQLAlchemy 2 + psycopg 3 on Render Free, Singapore (root: api/); data: Supabase Free: Postgres (session pooler), Auth (email + anonymous), Storage bucket 'snapshots'; ai: Gemini free (primary) + Groq free (fallback) via LLM gateway with Postgres cache; integrations: Tavily search, Resend email, Internet Archive CDX

## In scope
- Builder script creates each account through the same endpoints a user hits (onboarding, product add, uploads, discovery, facts)
- Stride: unit economics scaled from Campus Activewear FY26 (cited), transaction pattern from UCI Online Retail II, real running-shoe pages
- Bakery: The Bread Basket transactions (CC0) priced from real Pune menu pages
- StackNest: existing real competitors + public SaaS benchmark report
- QuickKart: Eternal and Swiggy filings for competitors
- Every demo account labelled 'Demo business, modelled on …'
- Old hand-seeded histories removed

## Out of scope for this step
- Hand-written results of any kind

## Suggested tasks
- scripts/build_demo.py
- fixtures/datasets/ with ATTRIBUTION.md
- credentials in README

## Skills — use in this order
1. **fastapi** — reuse endpoints from the builder
2. **supabase** — create the four auth users

Always-on rules for every step: **ponytail**.

## Done when (check on the deployed app, not locally)
1. Sign in on <FRONTEND_URL> as each demo business → all four dashboards populated with source labels
2. Delete and rebuild Stride → same dashboards (deterministic inputs)

## If it goes wrong
Stride and StackNest first; bakery and QuickKart may ship with Product + Money only.

## When finished
1. Make sure everything above is deployed (backend, database) and the done-check passes on the public URL.
2. Set `"status": "done"` for B14j in `docs/build-plan/plan.json`, then run `python C:\Users\Niranjan Iyer\.claude\skills\synced\4388f05c-eb72-4dd8-a66b-700dfbb34581_a5c3319d-ef87-457c-8cc8-fe986ddce72a\prototype-build-planner\scripts\build_plan.py render docs/build-plan/plan.json`.
3. Commit as `B14j: Four demo businesses built from real data`.
4. Report what changed and the done-check result, then stop. Don't start the next step without being asked.


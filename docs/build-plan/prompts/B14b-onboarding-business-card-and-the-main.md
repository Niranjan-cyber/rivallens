# B14b — Onboarding, business card and the main dashboard

Build step B14b of **RivalLens (working name)** (Prototype). Paste this into Claude Code / Codex / Cursor at the repo root. Do only this step.

## Read first
- `docs/build-plan/BUILD-PLAN.md` (section B14b) and `docs/build-plan/plan.json`
- `AGENTS.md`, `SKILL-PLAYBOOK.md`, `SKILLS.md`
- `hacknova26-competitor-intel-feature-scope.md` (Feature scope: only if the step touches scope or cut list; grep the heading)
- `hacknova26-competitor-intel-user-journeys.md` (User journeys: grep only the screens (S-xx) and use cases (UC-xx) this step lists)
- `hacknova26-competitor-intel-architecture.md` (Architecture: grep only the ADRs/components (C-xx) this step lists)
- `hacknova26-competitor-intel-specs.md` (Specs: grep only the sections this step cites (e.g. '### C-08', '## 2. API contracts' endpoint names))
- `fixtures/README.md` (Fixtures README: only for parser/test steps; never open raw HTML fixtures)

## The goal (the only goal of this step)
After sign-up, a user fills a short onboarding form, confirms the drafted business card, and lands on a main dashboard with four dashboards: Product, Money, Market and Customers.

**Why now:** This is the product's front door; every later step fills one of these four dashboards.

## Slice
- Use cases: UC-21, UC-02
- Screens: S-20, S-21, S-06
- Components: C-28
- Stack: frontend: Next.js 15 App Router + TS + Tailwind + shadcn/ui on Vercel (root: web/); backend: FastAPI + SQLAlchemy 2 + psycopg 3 on Render Free, Singapore (root: api/); data: Supabase Free: Postgres (session pooler), Auth (email + anonymous), Storage bucket 'snapshots'; ai: Gemini free (primary) + Groq free (fallback) via LLM gateway with Postgres cache; integrations: Tavily search, Resend email, Internet Archive CDX

## In scope
- Onboarding step 1 (required): business name, type (startup, D2C, local business, SaaS, vendor), city, website, one-line description, main products
- Step 2 (optional): funding stage, monthly revenue range, target customers, social handles
- Card drafted by the existing card task, user edits and confirms
- Main dashboard: 4 summary cards (empty states that say what to add)
- Nav: Product (first), Money, Market (existing screens move here), Customers
- Business switcher hidden when an account has one business

## Out of scope for this step
- Dashboard contents (later steps)

## Suggested tasks
- profiles.onboarding jsonb
- S-20 onboarding
- S-21 main dashboard
- Nav regroup in screens.ts

## Skills — use in this order
1. **frontend-design** — onboarding and main dashboard in the existing DESIGN.md style
2. **fastapi** — profile create from onboarding

Always-on rules for every step: **ponytail**.

## Done when (check on the deployed app, not locally)
1. New account on <FRONTEND_URL> → onboarding → card → main dashboard with 4 cards and Product first in the nav
2. Market holds the existing monitor, competitors, comparison, alerts and reports, all still working
3. Golden path B14 still passes

## If it goes wrong
Keep the old dashboard reachable under Market if the regroup breaks a route.

## When finished
1. Make sure everything above is deployed (frontend, backend, database) and the done-check passes on the public URL.
2. Set `"status": "done"` for B14b in `docs/build-plan/plan.json`, then run `python C:\Users\Niranjan Iyer\.claude\skills\synced\4388f05c-eb72-4dd8-a66b-700dfbb34581_a5c3319d-ef87-457c-8cc8-fe986ddce72a\prototype-build-planner\scripts\build_plan.py render docs/build-plan/plan.json`.
3. Commit as `B14b: Onboarding, business card and the main dashboard`.
4. Report what changed and the done-check result, then stop. Don't start the next step without being asked.


# B14i — Customer segment and a simulator fed by every dashboard

Build step B14i of **RivalLens (working name)** (Prototype). Paste this into Claude Code / Codex / Cursor at the repo root. Do only this step.

## Read first
- `docs/build-plan/BUILD-PLAN.md` (section B14i) and `docs/build-plan/plan.json`
- `AGENTS.md`, `SKILL-PLAYBOOK.md`, `SKILLS.md`
- `hacknova26-competitor-intel-feature-scope.md` (Feature scope: only if the step touches scope or cut list; grep the heading)
- `hacknova26-competitor-intel-user-journeys.md` (User journeys: grep only the screens (S-xx) and use cases (UC-xx) this step lists)
- `hacknova26-competitor-intel-architecture.md` (Architecture: grep only the ADRs/components (C-xx) this step lists)
- `hacknova26-competitor-intel-specs.md` (Specs: grep only the sections this step cites (e.g. '### C-08', '## 2. API contracts' endpoint names))
- `fixtures/README.md` (Fixtures README: only for parser/test steps; never open raw HTML fixtures)

## The goal (the only goal of this step)
Each product shows a suggested customer segment and a simulator whose inputs come from Market (category prices, receipts), Money (cost, margin, runway) and Customers (sentiment, requests), each input linked to its dashboard.

**Why now:** Ties the four dashboards together; the decision layer the user described.

## Slice
- Use cases: UC-19, UC-22, UC-07
- Screens: S-23, S-14
- Components: C-12
- Stack: frontend: Next.js 15 App Router + TS + Tailwind + shadcn/ui on Vercel (root: web/); backend: FastAPI + SQLAlchemy 2 + psycopg 3 on Render Free, Singapore (root: api/); data: Supabase Free: Postgres (session pooler), Auth (email + anonymous), Storage bucket 'snapshots'; ai: Gemini free (primary) + Groq free (fallback) via LLM gateway with Postgres cache; integrations: Tavily search, Resend email, Internet Archive CDX

## In scope
- simulations keyed by product
- Inputs replace defaults: unit cost and margin from Money, runway flag, sentiment shifts conversion (bounded ±20%, labelled), requested features raise feature coverage
- Segment = LLM over price position, review themes and onboarding target customers, must cite evidence ids; rules check the cited ids exist
- Re-plan on receipts still works

## Out of scope for this step
- Changing the core §4.4 formula

## Suggested tasks
- Migration product_id on simulations
- inputs + tests
- segment task
- UI chips

## Skills — use in this order
1. **tdd** — input mapping and bounds on hand-computed cases
2. **fastapi** — per-product simulator
3. **frontend-design** — segment card and input chips

Always-on rules for every step: **ponytail**.

## Done when (check on the deployed app, not locally)
1. On <FRONTEND_URL> lower cash on Money → the product shows a runway flag
2. Upload negative reviews → expected conversion drops, chip links to Customers
3. Segment card cites price position and two review themes

## If it goes wrong
Show inputs beside the business-level simulator without changing its numbers.

## When finished
1. Make sure everything above is deployed (frontend, backend, database) and the done-check passes on the public URL.
2. Set `"status": "done"` for B14i in `docs/build-plan/plan.json`, then run `python C:\Users\Niranjan Iyer\.claude\skills\synced\4388f05c-eb72-4dd8-a66b-700dfbb34581_a5c3319d-ef87-457c-8cc8-fe986ddce72a\prototype-build-planner\scripts\build_plan.py render docs/build-plan/plan.json`.
3. Commit as `B14i: Customer segment and a simulator fed by every dashboard`.
4. Report what changed and the done-check result, then stop. Don't start the next step without being asked.


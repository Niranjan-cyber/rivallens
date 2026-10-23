# B14d — Per-product simulator fed by all dashboards

Build step B14d of **RivalLens (working name)** (Prototype). Paste this into Claude Code / Codex / Cursor at the repo root. Do only this step.

## Read first
- `docs/build-plan/BUILD-PLAN.md` (section B14d) and `docs/build-plan/plan.json`
- `AGENTS.md`, `SKILL-PLAYBOOK.md`, `SKILLS.md`
- `hacknova26-competitor-intel-feature-scope.md` (Feature scope: only if the step touches scope or cut list; grep the heading)
- `hacknova26-competitor-intel-user-journeys.md` (User journeys: grep only the screens (S-xx) and use cases (UC-xx) this step lists)
- `hacknova26-competitor-intel-architecture.md` (Architecture: grep only the ADRs/components (C-xx) this step lists)
- `hacknova26-competitor-intel-specs.md` (Specs: grep only the sections this step cites (e.g. '### C-08', '## 2. API contracts' endpoint names))
- `fixtures/README.md` (Fixtures README: only for parser/test steps; never open raw HTML fixtures)

## The goal (the only goal of this step)
Each product's simulator uses its category's competitor prices, the company's runway and its customers' sentiment and requested features, and shows which input came from which dashboard.

**Why now:** The integration the user asked for; it ties the four dashboards together for the demo.

## Slice
- Use cases: UC-19, UC-07
- Screens: S-14, S-20
- Components: C-12
- Stack: frontend: Next.js 15 App Router + TS + Tailwind + shadcn/ui on Vercel (root: web/); backend: FastAPI + SQLAlchemy 2 + psycopg 3 on Render Free, Singapore (root: api/); data: Supabase Free: Postgres (session pooler), Auth (email + anonymous), Storage bucket 'snapshots'; ai: Gemini free (primary) + Groq free (fallback) via LLM gateway with Postgres cache; integrations: Tavily search, Resend email, Internet Archive CDX

## In scope
- simulations keyed by product
- Runway flag: an option's months to break-even > runway
- Sentiment shifts c0 (labelled, bounded ±20%); requested features raise feature coverage
- Input chips: Market / Economics / Customers with links

## Out of scope for this step
- Changing the core formula in specs §4.4

## Suggested tasks
- Migration 0013 product_id on simulations
- simulator inputs
- tests on hand-computed cases
- S-14 per product

## Skills — use in this order
1. **tdd** — runway flag and sentiment adjustment
2. **fastapi** — per-product simulation endpoint
3. **frontend-design** — input chips on S-14

Always-on rules for every step: **ponytail**.

## Done when (check on the deployed app, not locally)
1. On <FRONTEND_URL> lower cash on Economics → the product's simulator shows a runway flag
2. Upload negative reviews → expected conversion drops and the chip links to Customers
3. The NimbusDeploy price cut still re-plans the product

## If it goes wrong
Show the inputs beside the existing profile-level simulator without changing its numbers.

## When finished
1. Make sure everything above is deployed (frontend, backend, database) and the done-check passes on the public URL.
2. Set `"status": "done"` for B14d in `docs/build-plan/plan.json`, then run `python C:\Users\Niranjan Iyer\.claude\skills\synced\4388f05c-eb72-4dd8-a66b-700dfbb34581_a5c3319d-ef87-457c-8cc8-fe986ddce72a\prototype-build-planner\scripts\build_plan.py render docs/build-plan/plan.json`.
3. Commit as `B14d: Per-product simulator fed by all dashboards`.
4. Report what changed and the done-check result, then stop. Don't start the next step without being asked.


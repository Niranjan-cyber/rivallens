# B14b — Economics dashboard with cited funding

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
On Economics, a company enters its cash, funding and monthly burn to see its runway, and sees competitors' funding and reported revenue with a source link and date.

**Why now:** Riskiest new unknown (news extraction quality for Indian private companies); its runway is a simulator input.

## Slice
- Use cases: UC-17
- Screens: S-21
- Components: C-29
- Stack: frontend: Next.js 15 App Router + TS + Tailwind + shadcn/ui on Vercel (root: web/); backend: FastAPI + SQLAlchemy 2 + psycopg 3 on Render Free, Singapore (root: api/); data: Supabase Free: Postgres (session pooler), Auth (email + anonymous), Storage bucket 'snapshots'; ai: Gemini free (primary) + Groq free (fallback) via LLM gateway with Postgres cache; integrations: Tavily search, Resend email, Internet Archive CDX

## In scope
- company_finances (cash, monthly_burn, monthly_revenue, rounds jsonb) entered by the user
- Runway = cash / (burn - revenue)
- Tavily search per competitor for funding/revenue → LLM extracts amount, round, date with the quote; page saved as a snapshot; anything not found is Unknown
- funding_facts table with evidence

## Out of scope for this step
- Paid databases (Crunchbase, Tracxn)
- Bank or accounting integrations

## Suggested tasks
- Migration 0011_economics
- economics router + funding job
- S-21

## Skills — use in this order
1. **fastapi** — finances + funding job
2. **tdd** — runway and money-amount parsing (₹ crore/lakh, $M)
3. **frontend-design** — S-21

Always-on rules for every step: **ponytail**.

## Done when (check on the deployed app, not locally)
1. On <FRONTEND_URL> Economics: enter cash ₹50L, burn ₹6L, revenue ₹1L → runway 10 months
2. Find funding for a real competitor → a round with amount, date and a working source link, or Unknown

## If it goes wrong
Manual entry of competitor figures with a source URL.

## When finished
1. Make sure everything above is deployed (frontend, backend, database) and the done-check passes on the public URL.
2. Set `"status": "done"` for B14b in `docs/build-plan/plan.json`, then run `python C:\Users\Niranjan Iyer\.claude\skills\synced\4388f05c-eb72-4dd8-a66b-700dfbb34581_a5c3319d-ef87-457c-8cc8-fe986ddce72a\prototype-build-planner\scripts\build_plan.py render docs/build-plan/plan.json`.
3. Commit as `B14b: Economics dashboard with cited funding`.
4. Report what changed and the done-check result, then stop. Don't start the next step without being asked.


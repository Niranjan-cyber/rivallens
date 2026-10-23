# B14f — Competitors' revenue and funding, cited

Build step B14f of **RivalLens (working name)** (Prototype). Paste this into Claude Code / Codex / Cursor at the repo root. Do only this step.

## Read first
- `docs/build-plan/BUILD-PLAN.md` (section B14f) and `docs/build-plan/plan.json`
- `AGENTS.md`, `SKILL-PLAYBOOK.md`, `SKILLS.md`
- `hacknova26-competitor-intel-feature-scope.md` (Feature scope: only if the step touches scope or cut list; grep the heading)
- `hacknova26-competitor-intel-user-journeys.md` (User journeys: grep only the screens (S-xx) and use cases (UC-xx) this step lists)
- `hacknova26-competitor-intel-architecture.md` (Architecture: grep only the ADRs/components (C-xx) this step lists)
- `hacknova26-competitor-intel-specs.md` (Specs: grep only the sections this step cites (e.g. '### C-08', '## 2. API contracts' endpoint names))
- `fixtures/README.md` (Fixtures README: only for parser/test steps; never open raw HTML fixtures)

## The goal (the only goal of this step)
Money and the product comparison show competitors' reported revenue, margin and funding, each with a source link and date, or Unknown.

**Why now:** Revenue comparison was asked for and must be real; listed companies publish it.

## Slice
- Use cases: UC-17, UC-20
- Screens: S-24, S-23
- Components: C-30
- Stack: frontend: Next.js 15 App Router + TS + Tailwind + shadcn/ui on Vercel (root: web/); backend: FastAPI + SQLAlchemy 2 + psycopg 3 on Render Free, Singapore (root: api/); data: Supabase Free: Postgres (session pooler), Auth (email + anonymous), Storage bucket 'snapshots'; ai: Gemini free (primary) + Groq free (fallback) via LLM gateway with Postgres cache; integrations: Tavily search, Resend email, Internet Archive CDX

## In scope
- Tavily search per competitor: revenue, funding round, filings coverage
- LLM extracts amount, period, quote; the source page saved as a snapshot (evidence)
- ₹ crore/lakh and $M parsing
- money_facts table

## Out of scope for this step
- Paid databases (Crunchbase, Tracxn: future scope)

## Suggested tasks
- Migration 0012_money_facts
- facts job
- UI columns

## Skills — use in this order
1. **tdd** — amount parsing and quote check
2. **fastapi** — facts job

Always-on rules for every step: **ponytail**.

## Done when (check on the deployed app, not locally)
1. On <FRONTEND_URL> fetch facts for Campus Activewear → FY26 revenue ≈ ₹1,774 crore with a working source link
2. A private competitor with no coverage shows Unknown

## If it goes wrong
Manual entry with a source URL.

## When finished
1. Make sure everything above is deployed (frontend, backend, database) and the done-check passes on the public URL.
2. Set `"status": "done"` for B14f in `docs/build-plan/plan.json`, then run `python C:\Users\Niranjan Iyer\.claude\skills\synced\4388f05c-eb72-4dd8-a66b-700dfbb34581_a5c3319d-ef87-457c-8cc8-fe986ddce72a\prototype-build-planner\scripts\build_plan.py render docs/build-plan/plan.json`.
3. Commit as `B14f: Competitors' revenue and funding, cited`.
4. Report what changed and the done-check result, then stop. Don't start the next step without being asked.


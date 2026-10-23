# B14e — Money dashboard from uploads and manual entry

Build step B14e of **RivalLens (working name)** (Prototype). Paste this into Claude Code / Codex / Cursor at the repo root. Do only this step.

## Read first
- `docs/build-plan/BUILD-PLAN.md` (section B14e) and `docs/build-plan/plan.json`
- `AGENTS.md`, `SKILL-PLAYBOOK.md`, `SKILLS.md`
- `hacknova26-competitor-intel-feature-scope.md` (Feature scope: only if the step touches scope or cut list; grep the heading)
- `hacknova26-competitor-intel-user-journeys.md` (User journeys: grep only the screens (S-xx) and use cases (UC-xx) this step lists)
- `hacknova26-competitor-intel-architecture.md` (Architecture: grep only the ADRs/components (C-xx) this step lists)
- `hacknova26-competitor-intel-specs.md` (Specs: grep only the sections this step cites (e.g. '### C-08', '## 2. API contracts' endpoint names))
- `fixtures/README.md` (Fixtures README: only for parser/test steps; never open raw HTML fixtures)

## The goal (the only goal of this step)
On Money, a user uploads a CSV or Excel export (or adds entries by hand) and sees revenue, profit margin against the Indian industry benchmark, product prices, the transaction log and runway.

**Why now:** Money is the second input to the product decisions.

## Slice
- Use cases: UC-17
- Screens: S-24
- Components: C-30
- Stack: frontend: Next.js 15 App Router + TS + Tailwind + shadcn/ui on Vercel (root: web/); backend: FastAPI + SQLAlchemy 2 + psycopg 3 on Render Free, Singapore (root: api/); data: Supabase Free: Postgres (session pooler), Auth (email + anonymous), Storage bucket 'snapshots'; ai: Gemini free (primary) + Groq free (fallback) via LLM gateway with Postgres cache; integrations: Tavily search, Resend email, Internet Archive CDX

## In scope
- transactions table (date, product, qty, amount, type sale|expense|funding, source file)
- CSV/XLSX upload with column mapping preview (openpyxl)
- Manual entry form
- Metrics: monthly revenue, gross margin, burn, runway, funding total, price per product
- Benchmark: Damodaran 'Margins by industry, India' (Jan 2026), credited
- Sample file built from UCI Online Retail II (CC BY 4.0)

## Out of scope for this step
- Bank, Razorpay, Shopify, Tally live sync (future scope)

## Suggested tasks
- Migration 0011_money
- parser + metrics with tests
- S-24

## Skills — use in this order
1. **tdd** — column mapping, ₹ parsing, margin and runway on fixtures
2. **fastapi** — upload endpoint
3. **frontend-design** — S-24 with the dataviz rules

Always-on rules for every step: **ponytail**.

## Done when (check on the deployed app, not locally)
1. On <FRONTEND_URL> upload the sample XLSX → mapping preview → revenue chart, margin vs benchmark, runway
2. Add one expense by hand → margin and runway update
3. Transaction log shows both, with the source file

## If it goes wrong
CSV only if XLSX parsing breaks.

## When finished
1. Make sure everything above is deployed (frontend, backend, database) and the done-check passes on the public URL.
2. Set `"status": "done"` for B14e in `docs/build-plan/plan.json`, then run `python C:\Users\Niranjan Iyer\.claude\skills\synced\4388f05c-eb72-4dd8-a66b-700dfbb34581_a5c3319d-ef87-457c-8cc8-fe986ddce72a\prototype-build-planner\scripts\build_plan.py render docs/build-plan/plan.json`.
3. Commit as `B14e: Money dashboard from uploads and manual entry`.
4. Report what changed and the done-check result, then stop. Don't start the next step without being asked.


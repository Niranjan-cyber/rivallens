# B14e — Per-product comparison and inspiration

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
On a product, a company compares it with products in the same market category on price, revenue, features and add-ons, and sees inspiration products from other categories.

**Why now:** Uses the products, revenue facts and existing comparison engine; lowest risk, so it goes last.

## Slice
- Use cases: UC-20, UC-06
- Screens: S-23, S-13
- Components: C-11
- Stack: frontend: Next.js 15 App Router + TS + Tailwind + shadcn/ui on Vercel (root: web/); backend: FastAPI + SQLAlchemy 2 + psycopg 3 on Render Free, Singapore (root: api/); data: Supabase Free: Postgres (session pooler), Auth (email + anonymous), Storage bucket 'snapshots'; ai: Gemini free (primary) + Groq free (fallback) via LLM gateway with Postgres cache; integrations: Tavily search, Resend email, Internet Archive CDX

## In scope
- Comparison filtered to competitors in the product's category
- Revenue column from funding_facts (cited) or Unknown
- Add-ons row
- Inspiration tab

## Out of scope for this step
- New scoring formula

## Suggested tasks
- comparison?product=
- S-23

## Skills — use in this order
1. **fastapi** — product-scoped comparison
2. **frontend-design** — S-23

Always-on rules for every step: **ponytail**.

## Done when (check on the deployed app, not locally)
1. On <FRONTEND_URL> open a product → its category comparison shows price, revenue (cited or Unknown), features and add-ons
2. Inspiration tab shows a different set

## If it goes wrong
Link the product to the existing profile comparison filtered by category.

## When finished
1. Make sure everything above is deployed (frontend, backend) and the done-check passes on the public URL.
2. Set `"status": "done"` for B14e in `docs/build-plan/plan.json`, then run `python C:\Users\Niranjan Iyer\.claude\skills\synced\4388f05c-eb72-4dd8-a66b-700dfbb34581_a5c3319d-ef87-457c-8cc8-fe986ddce72a\prototype-build-planner\scripts\build_plan.py render docs/build-plan/plan.json`.
3. Commit as `B14e: Per-product comparison and inspiration`.
4. Report what changed and the done-check result, then stop. Don't start the next step without being asked.


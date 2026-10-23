# B14c — Products in exact market categories

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
On Product, a user sees Existing and New products, adds one, and gets its exact category from the Google product taxonomy (a football lands in Soccer Balls, a chair in Chairs).

**Why now:** Category drives every comparison; wrong categories make everything after this meaningless.

## Slice
- Use cases: UC-16
- Screens: S-22
- Components: C-29
- Stack: frontend: Next.js 15 App Router + TS + Tailwind + shadcn/ui on Vercel (root: web/); backend: FastAPI + SQLAlchemy 2 + psycopg 3 on Render Free, Singapore (root: api/); data: Supabase Free: Postgres (session pooler), Auth (email + anonymous), Storage bucket 'snapshots'; ai: Gemini free (primary) + Groq free (fallback) via LLM gateway with Postgres cache; integrations: Tavily search, Resend email, Internet Archive CDX

## In scope
- products table (profile, name, stage existing|new, taxonomy id + path, price, unit, cost, features, add_ons, url)
- Google product taxonomy (~5,500 paths) stored in Postgres
- Classifier: keyword prefilter to 20 candidate paths → LLM picks one (cached, replay fixture); user can change it
- Product from a URL reads schema.org Product JSON-LD (name, price, brand) when present

## Out of scope for this step
- Comparison (B14d)

## Suggested tasks
- Migration 0010_products + taxonomy load
- classify task + tests on 10 hand-labelled products
- S-22 Existing / New tabs, Add product

## Skills — use in this order
1. **supabase-postgres-best-practices** — products + taxonomy tables and indexes
2. **tdd** — taxonomy prefilter and JSON-LD product parsing on fixtures
3. **fastapi** — products CRUD + classify
4. **frontend-design** — S-22

Always-on rules for every step: **ponytail**.

## Done when (check on the deployed app, not locally)
1. On <FRONTEND_URL> add 'Size 5 training football' → category ends in Soccer Balls; 'Ergonomic office chair' → Office Chairs
2. Add a product from a real product URL → name and price filled from the page
3. Change the category by hand → it sticks

## If it goes wrong
If the LLM is down, the top prefilter match is preselected and the user confirms.

## When finished
1. Make sure everything above is deployed (frontend, backend, database) and the done-check passes on the public URL.
2. Set `"status": "done"` for B14c in `docs/build-plan/plan.json`, then run `python C:\Users\Niranjan Iyer\.claude\skills\synced\4388f05c-eb72-4dd8-a66b-700dfbb34581_a5c3319d-ef87-457c-8cc8-fe986ddce72a\prototype-build-planner\scripts\build_plan.py render docs/build-plan/plan.json`.
3. Commit as `B14c: Products in exact market categories`.
4. Report what changed and the done-check result, then stop. Don't start the next step without being asked.


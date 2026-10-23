# B14d — Like-for-like product comparison and inspirations

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
Opening a product shows it against products in the same category on price, features and add-ons, each value with its source and date, plus premium inspirations from the top of the category.

**Why now:** The user's core ask for the Product layer; reuses the comparison engine.

## Slice
- Use cases: UC-20, UC-06
- Screens: S-23
- Components: C-11, C-29
- Stack: frontend: Next.js 15 App Router + TS + Tailwind + shadcn/ui on Vercel (root: web/); backend: FastAPI + SQLAlchemy 2 + psycopg 3 on Render Free, Singapore (root: api/); data: Supabase Free: Postgres (session pooler), Auth (email + anonymous), Storage bucket 'snapshots'; ai: Gemini free (primary) + Groq free (fallback) via LLM gateway with Postgres cache; integrations: Tavily search, Resend email, Internet Archive CDX

## In scope
- Category comparables from (1) competitors' product pages read via JSON-LD, robots respected and (2) Flipkart products dataset (CC BY-SA, dated) as a price benchmark
- Price position: your price vs category median and range
- Inspiration = top-price-quartile products in the same category
- Unknown stays Unknown

## Out of scope for this step
- Revenue column (B14f fills it)

## Suggested tasks
- Dataset import script (HF mirror, attribution file)
- comparison?product=
- S-23 product detail

## Skills — use in this order
1. **tdd** — category median and quartile on a fixture set
2. **fastapi** — product comparison endpoint
3. **frontend-design** — S-23

Always-on rules for every step: **ponytail**.

## Done when (check on the deployed app, not locally)
1. On <FRONTEND_URL> open a running shoe → only running shoes listed, each with source and date
2. Price position says e.g. '18% above category median (n=…)'
3. Inspirations tab lists premium running shoes

## If it goes wrong
Dataset benchmark only, if live product pages yield too little.

## When finished
1. Make sure everything above is deployed (frontend, backend, database) and the done-check passes on the public URL.
2. Set `"status": "done"` for B14d in `docs/build-plan/plan.json`, then run `python C:\Users\Niranjan Iyer\.claude\skills\synced\4388f05c-eb72-4dd8-a66b-700dfbb34581_a5c3319d-ef87-457c-8cc8-fe986ddce72a\prototype-build-planner\scripts\build_plan.py render docs/build-plan/plan.json`.
3. Commit as `B14d: Like-for-like product comparison and inspirations`.
4. Report what changed and the done-check result, then stop. Don't start the next step without being asked.


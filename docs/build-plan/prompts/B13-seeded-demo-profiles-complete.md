# B13 — Seeded demo profiles complete

Build step B13 of **RivalLens (working name)** (Prototype). Paste this into Claude Code / Codex / Cursor at the repo root. Do only this step.

## Read first
- `docs/build-plan/BUILD-PLAN.md` (section B13) and `docs/build-plan/plan.json`
- `AGENTS.md`, `SKILL-PLAYBOOK.md`, `SKILLS.md`
- `hacknova26-competitor-intel-feature-scope.md` (Feature scope: only if the step touches scope or cut list; grep the heading)
- `hacknova26-competitor-intel-user-journeys.md` (User journeys: grep only the screens (S-xx) and use cases (UC-xx) this step lists)
- `hacknova26-competitor-intel-architecture.md` (Architecture: grep only the ADRs/components (C-xx) this step lists)
- `hacknova26-competitor-intel-specs.md` (Specs: grep only the sections this step cites (e.g. '### C-08', '## 2. API contracts' endpoint names))
- `fixtures/README.md` (Fixtures README: only for parser/test steps; never open raw HTML fixtures)

## The goal (the only goal of this step)
A demo guest sees the quick-commerce, Stride & Co. and quantum-idea profiles fully populated with competitors, history, comparison and simulator data, all labelled demo data.

**Why now:** Your multi-profile demo story; must be data, not code, so it comes after every feature exists.

## Slice
- Use cases: UC-13, UC-14
- Screens: S-03, S-09, S-13, S-14
- Components: C-13, C-15
- Stack: frontend: Next.js 15 App Router + TS + Tailwind + shadcn/ui on Vercel (root: web/); backend: FastAPI + SQLAlchemy 2 + psycopg 3 on Render Free, Singapore (root: api/); data: Supabase Free: Postgres (session pooler), Auth (email + anonymous), Storage bucket 'snapshots'; ai: Gemini free (primary) + Groq free (fallback) via LLM gateway with Postgres cache; integrations: Tavily search, Resend email, Internet Archive CDX

## In scope
- seed.py: run discovery (record mode) + baseline for the cloud profile on real pages; product-type Stride & Co. with official brand pages or seeded observations; quick-commerce profile; quantum Idea Card with assumptions that trigger flags
- All seeded rows is_demo_data=true; dates real (observation time) for real pages
- Re-run guest clone to verify

## Out of scope for this step
- Marketplace scraping (cut list)
- New features

## Suggested tasks
- Extend seed.py
- Run against live DB
- Check each profile's screens

## Skills — use in this order
1. **diagnosing-bugs** — only if the seeded data exposes a pipeline bug

Always-on rules for every step: **ponytail**.

## Done when (check on the deployed app, not locally)
1. On <FRONTEND_URL> new private window → Try demo account → each of the 4 profiles opens with non-empty dashboard, comparison and simulator
2. Quantum idea → S-14 shows viability flags
3. Every seeded card shows a demo-data badge

## If it goes wrong
Cut order item 3: keep cloud + quantum, drop quick-commerce and shoes.

## When finished
1. Make sure everything above is deployed (backend, database) and the done-check passes on the public URL.
2. Set `"status": "done"` for B13 in `docs/build-plan/plan.json`, then run `python C:\Users\Niranjan Iyer\.claude\skills\synced\4388f05c-eb72-4dd8-a66b-700dfbb34581_a5c3319d-ef87-457c-8cc8-fe986ddce72a\prototype-build-planner\scripts\build_plan.py render docs/build-plan/plan.json`.
3. Commit as `B13: Seeded demo profiles complete`.
4. Report what changed and the done-check result, then stop. Don't start the next step without being asked.

## Notes
Freeze at 20:15 regardless of this step's state.


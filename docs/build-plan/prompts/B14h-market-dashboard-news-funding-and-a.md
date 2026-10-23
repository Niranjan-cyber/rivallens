# B14h — Market dashboard: news, funding and a simulated competitor move

Build step B14h of **RivalLens (working name)** (Prototype). Paste this into Claude Code / Codex / Cursor at the repo root. Do only this step.

## Read first
- `docs/build-plan/BUILD-PLAN.md` (section B14h) and `docs/build-plan/plan.json`
- `AGENTS.md`, `SKILL-PLAYBOOK.md`, `SKILLS.md`
- `hacknova26-competitor-intel-feature-scope.md` (Feature scope: only if the step touches scope or cut list; grep the heading)
- `hacknova26-competitor-intel-user-journeys.md` (User journeys: grep only the screens (S-xx) and use cases (UC-xx) this step lists)
- `hacknova26-competitor-intel-architecture.md` (Architecture: grep only the ADRs/components (C-xx) this step lists)
- `hacknova26-competitor-intel-specs.md` (Specs: grep only the sections this step cites (e.g. '### C-08', '## 2. API contracts' endpoint names))
- `fixtures/README.md` (Fixtures README: only for parser/test steps; never open raw HTML fixtures)

## The goal (the only goal of this step)
Market shows competitor changes, category news and funding with links, the category price trend, and a 'Simulate a competitor move' control that replaces Demo Lab.

**Why now:** Keeps the required simulated-change demo inside a clean product.

## Slice
- Use cases: UC-04, UC-10, UC-11
- Screens: S-25, S-10
- Components: C-03, C-19
- Stack: frontend: Next.js 15 App Router + TS + Tailwind + shadcn/ui on Vercel (root: web/); backend: FastAPI + SQLAlchemy 2 + psycopg 3 on Render Free, Singapore (root: api/); data: Supabase Free: Postgres (session pooler), Auth (email + anonymous), Storage bucket 'snapshots'; ai: Gemini free (primary) + Groq free (fallback) via LLM gateway with Postgres cache; integrations: Tavily search, Resend email, Internet Archive CDX

## In scope
- Market overview: latest receipts, alerts, category news + funding (Tavily, cited)
- Category price trend from our own observations
- Simulate control only on demo accounts, labelled 'changes a fictional competitor's website'
- Demo Lab route removed from nav

## Out of scope for this step
- New detection logic

## Suggested tasks
- S-25
- news task
- simulate control

## Skills — use in this order
1. **frontend-design** — S-25
2. **fastapi** — news endpoint

Always-on rules for every step: **ponytail**.

## Done when (check on the deployed app, not locally)
1. On <FRONTEND_URL> Market → Simulate a competitor move → Check competitors now → 1 change, 4 ignored, receipt, alert
2. Category news shows dated items with links

## If it goes wrong
Keep Demo Lab reachable by URL.

## When finished
1. Make sure everything above is deployed (frontend, backend) and the done-check passes on the public URL.
2. Set `"status": "done"` for B14h in `docs/build-plan/plan.json`, then run `python C:\Users\Niranjan Iyer\.claude\skills\synced\4388f05c-eb72-4dd8-a66b-700dfbb34581_a5c3319d-ef87-457c-8cc8-fe986ddce72a\prototype-build-planner\scripts\build_plan.py render docs/build-plan/plan.json`.
3. Commit as `B14h: Market dashboard: news, funding and a simulated competitor move`.
4. Report what changed and the done-check result, then stop. Don't start the next step without being asked.

## Notes
 Category price trend over time cut (needs repeat observations); the page shows each category's prices now with the date seen.


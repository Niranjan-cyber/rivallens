# B10 — Launch simulator that re-plans on receipts

Build step B10 of **RivalLens (working name)** (Prototype). Paste this into Claude Code / Codex / Cursor at the repo root. Do only this step.

## Read first
- `docs/build-plan/BUILD-PLAN.md` (section B10) and `docs/build-plan/plan.json`
- `AGENTS.md`, `SKILL-PLAYBOOK.md`, `SKILLS.md`
- `hacknova26-competitor-intel-feature-scope.md` (Feature scope: only if the step touches scope or cut list; grep the heading)
- `hacknova26-competitor-intel-user-journeys.md` (User journeys: grep only the screens (S-xx) and use cases (UC-xx) this step lists)
- `hacknova26-competitor-intel-architecture.md` (Architecture: grep only the ADRs/components (C-xx) this step lists)
- `hacknova26-competitor-intel-specs.md` (Specs: grep only the sections this step cites (e.g. '### C-08', '## 2. API contracts' endpoint names))
- `fixtures/README.md` (Fixtures README: only for parser/test steps; never open raw HTML fixtures)

## The goal (the only goal of this step)
After a competitor price-cut run, S-14 shows a re-planned launch recommendation from options A/B/C whose best/expected/worst outcomes cite editable assumptions.

**Why now:** Completes the winning feature (change → decision) and your launch-simulator requirement.

## Slice
- Use cases: UC-07, UC-14
- Screens: S-09, S-11, S-14
- Components: C-03, C-08, C-11, C-15
- Stack: frontend: Next.js 15 App Router + TS + Tailwind + shadcn/ui on Vercel (root: web/); backend: FastAPI + SQLAlchemy 2 + psycopg 3 on Render Free, Singapore (root: api/); data: Supabase Free: Postgres (session pooler), Auth (email + anonymous), Storage bucket 'snapshots'; ai: Gemini free (primary) + Groq free (fallback) via LLM gateway with Postgres cache; integrations: Tavily search, Resend email, Internet Archive CDX

## In scope
- simulations table; deterministic model exactly per specs §4.4 (options, conversion, ramp, break-even, recommendation)
- Re-plan trigger from price/plan/feature receipts of comparable competitors; S-11 'simulation impact' line
- Viability flags rules (no_verified_india_competitors, crowded_segment, no_breakeven_36m, capital_intensive, incumbent_heavy)
- GET simulation, PUT assumptions, POST option; S-14 UI + S-09 summary card; 'Scenario model, not a forecast' label

## Out of scope for this step
- Launch-window suggestions (Could, cut)

## Suggested tasks
- tdd the formula with hand-computed cases
- Endpoints + S-14 UI
- Seed quantum idea assumptions (high upfront cost) so flags fire

## Skills — use in this order
1. **tdd** — conversion, break-even, recommendation tie-break, each viability flag
2. **code-review** — checkpoint 2: built-in /code-review low on the diff since B04

Always-on rules for every step: **ponytail**.

## Done when (check on the deployed app, not locally)
1. On <FRONTEND_URL> StackNest → Simulator: 3 options with best/expected/worst; each assumption shows 'from evidence' with a receipt link or 'your assumption'
2. Demo Lab price cut → Run monitor → S-14 shows 'Re-planned: recommended ₹X → ₹Y because NimbusDeploy (demo) Pro −40%'
3. Edit elasticity → results update
4. Quantum idea profile → viability flags shown with citations; 'no break-even within 36 months under these assumptions'

## If it goes wrong
If re-plan wiring slips, show a 'Recompute' button on S-14 after a receipt (manual re-plan) and keep the banner.

## When finished
1. Make sure everything above is deployed (frontend, backend, database) and the done-check passes on the public URL.
2. Set `"status": "done"` for B10 in `docs/build-plan/plan.json`, then run `python C:\Users\Niranjan Iyer\.claude\skills\synced\4388f05c-eb72-4dd8-a66b-700dfbb34581_a5c3319d-ef87-457c-8cc8-fe986ddce72a\prototype-build-planner\scripts\build_plan.py render docs/build-plan/plan.json`.
3. Commit as `B10: Launch simulator that re-plans on receipts`.
4. Report what changed and the done-check result, then stop. Don't start the next step without being asked.

## Notes
Cut order item 4: viability flags (keep simulator).


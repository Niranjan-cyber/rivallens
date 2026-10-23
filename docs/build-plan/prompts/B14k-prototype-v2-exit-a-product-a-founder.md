# B14k — Prototype v2 exit: a product a founder can use

Build step B14k of **RivalLens (working name)** (Prototype — 🏁 prototype exit). Paste this into Claude Code / Codex / Cursor at the repo root. Do only this step.

## Read first
- `docs/build-plan/BUILD-PLAN.md` (section B14k) and `docs/build-plan/plan.json`
- `AGENTS.md`, `SKILL-PLAYBOOK.md`, `SKILLS.md`
- `hacknova26-competitor-intel-feature-scope.md` (Feature scope: only if the step touches scope or cut list; grep the heading)
- `hacknova26-competitor-intel-user-journeys.md` (User journeys: grep only the screens (S-xx) and use cases (UC-xx) this step lists)
- `hacknova26-competitor-intel-architecture.md` (Architecture: grep only the ADRs/components (C-xx) this step lists)
- `hacknova26-competitor-intel-specs.md` (Specs: grep only the sections this step cites (e.g. '### C-08', '## 2. API contracts' endpoint names))
- `fixtures/README.md` (Fixtures README: only for parser/test steps; never open raw HTML fixtures)

## The goal (the only goal of this step)
A judge signs in as Stride & Co., walks main dashboard → Product → Market (simulated move) → back to Product → report, then switches to the bakery, twice without errors; README, PPT and the public repo are ready by 08:00.

**Why now:** Freeze 07:00, submit by 08:00.

## Slice
- Use cases: UC-16, UC-17, UC-18, UC-19, UC-20, UC-21, UC-22
- Screens: S-21, S-22, S-23, S-24, S-25, S-26
- Components: —
- Stack: frontend: Next.js 15 App Router + TS + Tailwind + shadcn/ui on Vercel (root: web/); backend: FastAPI + SQLAlchemy 2 + psycopg 3 on Render Free, Singapore (root: api/); data: Supabase Free: Postgres (session pooler), Auth (email + anonymous), Storage bucket 'snapshots'; ai: Gemini free (primary) + Groq free (fallback) via LLM gateway with Postgres cache; integrations: Tavily search, Resend email, Internet Archive CDX

## In scope
- Golden path v2 x2
- PPT slides 3, 7, 8 updated with real screenshots
- README rewritten for the product
- Smoke extended

## Out of scope for this step
- New features after 07:00

## Suggested tasks
- Walk
- Screenshots
- README + PPT content
- Smoke

## Skills — use in this order
1. **code-review** — low review before the final deploy
2. **hackathon-demo-submission** — deliverables checklist

Always-on rules for every step: **ponytail**.

## Done when (check on the deployed app, not locally)
1. Golden path v2 twice on <FRONTEND_URL> with no errors
2. Smoke passes
3. Repo public, PPT updated, links submitted

## If it goes wrong
Submit with the B14 golden path if v2 breaks.

## When finished
1. Make sure everything above is deployed (frontend, backend) and the done-check passes on the public URL.
2. Set `"status": "done"` for B14k in `docs/build-plan/plan.json`, then run `python C:\Users\Niranjan Iyer\.claude\skills\synced\4388f05c-eb72-4dd8-a66b-700dfbb34581_a5c3319d-ef87-457c-8cc8-fe986ddce72a\prototype-build-planner\scripts\build_plan.py render docs/build-plan/plan.json`.
3. Commit as `B14k: Prototype v2 exit: a product a founder can use`.
4. Report what changed and the done-check result, then stop. Don't start the next step without being asked.


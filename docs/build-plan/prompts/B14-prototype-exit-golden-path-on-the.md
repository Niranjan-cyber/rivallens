# B14 — Prototype exit: golden path on the public URL

Build step B14 of **RivalLens (working name)** (Prototype — 🏁 prototype exit). Paste this into Claude Code / Codex / Cursor at the repo root. Do only this step.

## Read first
- `docs/build-plan/BUILD-PLAN.md` (section B14) and `docs/build-plan/plan.json`
- `AGENTS.md`, `SKILL-PLAYBOOK.md`, `SKILLS.md`
- `hacknova26-competitor-intel-feature-scope.md` (Feature scope: only if the step touches scope or cut list; grep the heading)
- `hacknova26-competitor-intel-user-journeys.md` (User journeys: grep only the screens (S-xx) and use cases (UC-xx) this step lists)
- `hacknova26-competitor-intel-architecture.md` (Architecture: grep only the ADRs/components (C-xx) this step lists)
- `hacknova26-competitor-intel-specs.md` (Specs: grep only the sections this step cites (e.g. '### C-08', '## 2. API contracts' endpoint names))
- `fixtures/README.md` (Fixtures README: only for parser/test steps; never open raw HTML fixtures)

## The goal (the only goal of this step)
A judge walks the full journeys §9 golden path on the public URL twice in a row without errors, with README + PPT ready to submit.

**Why now:** Freeze at 20:15: harden the demo, then the deliverables (repo, PPT, deployed URL are required).

## Slice
- Use cases: UC-01, UC-02, UC-03, UC-04, UC-05, UC-06, UC-07, UC-08, UC-09, UC-10, UC-11, UC-12, UC-13, UC-14
- Screens: S-01, S-02, S-03, S-04, S-05, S-06, S-07, S-08, S-09, S-10, S-11, S-13, S-14, S-15, S-16, S-18
- Components: C-01, C-03, C-25
- Stack: frontend: Next.js 15 App Router + TS + Tailwind + shadcn/ui on Vercel (root: web/); backend: FastAPI + SQLAlchemy 2 + psycopg 3 on Render Free, Singapore (root: api/); data: Supabase Free: Postgres (session pooler), Auth (email + anonymous), Storage bucket 'snapshots'; ai: Gemini free (primary) + Groq free (fallback) via LLM gateway with Postgres cache; integrations: Tavily search, Resend email, Internet Archive CDX

## In scope
- Playwright MCP walkthrough of the golden path on the deployed app; fix breaks only
- Error/empty states on demo inputs (LLM unavailable, discovery limit, no changes)
- C-25 keep-warm pinger (cron-job.org or GitHub Actions) on /healthz every 10 min
- README (setup, data sources, detection method, noise rules, evidence model, demo-data labelling, provider limits) = the technical write-up
- PPT: problem, golden-path screenshots, architecture diagram, detection methodology, simulator assumptions, roadmap (MVP/Production)
- Rehearse with LLM responses cached (record once, replay)

## Out of scope for this step
- Any new feature after 20:15
- Refactors

## Suggested tasks
- Golden path run ×2
- Fix blockers
- Pinger on
- README
- PPT
- Final push + smoke

## Skills — use in this order
1. **diagnosing-bugs** — for each break found in the walkthrough
2. **render-debug** — only on Render 5xx/OOM/cold-start issues
3. **hackathon-demo-submission** — README for judges, demo script, judge Q&A
4. **pptx** — build the PPT from the demo script and architecture

Always-on rules for every step: **ponytail**.

## Done when (check on the deployed app, not locally)
1. Walk journeys §9 steps 1–8 on <FRONTEND_URL> twice, no errors, no 'Sample data' badges left on golden-path screens (demo-data badges on seeded/mock content stay)
2. curl <BACKEND_URL>/healthz responds in < 2 s after 15 idle minutes (pinger working)
3. README renders on GitHub with live URL + architecture link; PPT file exported
4. bash scripts/smoke.sh passes

## If it goes wrong
If a golden-path step is broken at 20:40, demo it from the seeded StackNest profile (precomputed) and say so.

## When finished
1. Make sure everything above is deployed (frontend, backend, infra) and the done-check passes on the public URL.
2. Set `"status": "done"` for B14 in `docs/build-plan/plan.json`, then run `python C:\Users\Niranjan Iyer\.claude\skills\synced\4388f05c-eb72-4dd8-a66b-700dfbb34581_a5c3319d-ef87-457c-8cc8-fe986ddce72a\prototype-build-planner\scripts\build_plan.py render docs/build-plan/plan.json`.
3. Commit as `B14: Prototype exit: golden path on the public URL`.
4. Report what changed and the done-check result, then stop. Don't start the next step without being asked.

## Notes
Submission-time unknown: confirm with organizers and shift the freeze if earlier.


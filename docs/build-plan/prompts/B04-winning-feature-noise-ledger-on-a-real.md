# B04 — Winning feature: noise ledger on a real monitoring run

Build step B04 of **RivalLens (working name)** (Prototype). Paste this into Claude Code / Codex / Cursor at the repo root. Do only this step.

## Read first
- `docs/build-plan/BUILD-PLAN.md` (section B04) and `docs/build-plan/plan.json`
- `AGENTS.md`, `SKILL-PLAYBOOK.md`, `SKILLS.md`
- `hacknova26-competitor-intel-feature-scope.md` (Feature scope: only if the step touches scope or cut list; grep the heading)
- `hacknova26-competitor-intel-user-journeys.md` (User journeys: grep only the screens (S-xx) and use cases (UC-xx) this step lists)
- `hacknova26-competitor-intel-architecture.md` (Architecture: grep only the ADRs/components (C-xx) this step lists)
- `hacknova26-competitor-intel-specs.md` (Specs: grep only the sections this step cites (e.g. '### C-08', '## 2. API contracts' endpoint names))
- `fixtures/README.md` (Fixtures README: only for parser/test steps; never open raw HTML fixtures)

## The goal (the only goal of this step)
In the Demo Lab, a user applies 'cosmetic' then 'price cut' to NimbusDeploy (demo) and Run monitor on S-10 shows 0 meaningful changes the first time and the Pro price drop as meaningful the second time, with every ignored diff listed with its reason.

**Why now:** Riskiest unknown and the winning feature; it scores change detection, data accuracy and history. Built rules-only on mock pages so it doesn't depend on the LLM.

## Slice
- Use cases: UC-04, UC-10
- Screens: S-09, S-10, S-18, S-19
- Components: C-02, C-03, C-06, C-07, C-08, C-13, C-15, C-16
- Stack: frontend: Next.js 15 App Router + TS + Tailwind + shadcn/ui on Vercel (root: web/); backend: FastAPI + SQLAlchemy 2 + psycopg 3 on Render Free, Singapore (root: api/); data: Supabase Free: Postgres (session pooler), Auth (email + anonymous), Storage bucket 'snapshots'; ai: Gemini free (primary) + Groq free (fallback) via LLM gateway with Postgres cache; integrations: Tavily search, Resend email, Internet Archive CDX

## In scope
- C-02 mock site route /mock/[instance]/[slug] (no-store) reading mock_pages_public; realistic page structure + scenario versions (specs §1 C-02)
- S-18 Demo Lab: scenario buttons + reset + View mock page (POST /demo/mocks/{slug}/scenario, /demo/mocks/reset)
- Migration 0002_monitoring.sql: runs, snapshots, observations, ledger_entries, change_events, jobs
- C-06 collector with robots check, per-host rate limit, SSRF guard, gzip snapshot to Storage + sectioned text
- C-07 rules extraction (scoped price regex + plausibility, plan headings, feature lists); section-hash reuse
- C-08 field diff + noise rules + suspicious checks → ledger_entries / change_events
- Jobs: POST /profiles/{id}/runs (202 + job), GET /jobs/{id}, GET /runs/{id}; S-09 'Run monitor' button with progress; S-10 run result page
- Seed: StackNest gets the mock competitors' sources; baseline run in seed.py

## Out of scope for this step
- Receipt detail page (B05)
- Alerts and priority (B06)
- LLM extraction (B07)
- Real competitor pages (B08)

## Suggested tasks
- Write tests first (tdd) for: section splitter, price regex on fixtures, noise rules (cosmetic variant → 0 meaningful), diff (price_cut_40 → 1 price_decrease)
- Implement collector/extractor/changes modules to pass them
- Wire job runner (BackgroundTasks + jobs table + stale detection)
- Demo Lab UI + S-10 UI using the B01 design tokens

## Skills — use in this order
1. **tdd** — red → green on splitter, price rules, noise rules and diff using fixtures/ and mock HTML variants
2. **fastapi** — only if not loaded this session: 202 job endpoints + BackgroundTasks
3. **vercel-react-best-practices** — open only the caching/dynamic rendering rule for the no-store mock route
4. **code-review** — checkpoint 1: built-in /code-review low on the diff since B01

Always-on rules for every step: **ponytail**.

## Done when (check on the deployed app, not locally)
1. Open <FRONTEND_URL> as demo guest → Demo Lab → Reset → Cosmetic-only → StackNest dashboard → Run monitor
2. S-10 shows '0 meaningful' and ≥ 4 ledger entries with reasons (navigation_or_footer, promo_banner, formatting_only…)
3. Demo Lab → Cut Pro price 40% → Run monitor → S-10 lists NimbusDeploy (demo) Pro ₹1,499 → ₹899 (−40%) as meaningful within 30 s
4. View mock page shows the 'Demo data: fictional company' ribbon

## If it goes wrong
If the noise rules misfire, narrow monitoring to the pricing section only (contentSelector) and log the rest as ignored 'outside_pricing'.

## When finished
1. Make sure everything above is deployed (frontend, backend, database) and the done-check passes on the public URL.
2. Set `"status": "done"` for B04 in `docs/build-plan/plan.json`, then run `python C:\Users\Niranjan Iyer\.claude\skills\synced\4388f05c-eb72-4dd8-a66b-700dfbb34581_a5c3319d-ef87-457c-8cc8-fe986ddce72a\prototype-build-planner\scripts\build_plan.py render docs/build-plan/plan.json`.
3. Commit as `B04: Winning feature: noise ledger on a real monitoring run`.
4. Report what changed and the done-check result, then stop. Don't start the next step without being asked.

## Notes
This is the demo's core; polish S-10 copy (it's the judge's 'aha').


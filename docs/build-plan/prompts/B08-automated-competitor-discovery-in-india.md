# B08 — Automated competitor discovery in India

Build step B08 of **RivalLens (working name)** (Prototype). Paste this into Claude Code / Codex / Cursor at the repo root. Do only this step.

## Read first
- `docs/build-plan/BUILD-PLAN.md` (section B08) and `docs/build-plan/plan.json`
- `AGENTS.md`, `SKILL-PLAYBOOK.md`, `SKILLS.md`
- `hacknova26-competitor-intel-feature-scope.md` (Feature scope: only if the step touches scope or cut list; grep the heading)
- `hacknova26-competitor-intel-user-journeys.md` (User journeys: grep only the screens (S-xx) and use cases (UC-xx) this step lists)
- `hacknova26-competitor-intel-architecture.md` (Architecture: grep only the ADRs/components (C-xx) this step lists)
- `hacknova26-competitor-intel-specs.md` (Specs: grep only the sections this step cites (e.g. '### C-08', '## 2. API contracts' endpoint names))
- `fixtures/README.md` (Fixtures README: only for parser/test steps; never open raw HTML fixtures)

## The goal (the only goal of this step)
After saving a card, S-08 lists India-verified competitors found automatically (plus the user-added NimbusDeploy (demo) URL), ready to monitor.

**Why now:** Your hard requirement (no manual competitor entry) and the second-riskiest unknown; needs the B07 gateway.

## Slice
- Use cases: UC-03
- Screens: S-06, S-07, S-08, S-17
- Components: C-03, C-05, C-06, C-07, C-14, C-15, C-18, C-23
- Stack: frontend: Next.js 15 App Router + TS + Tailwind + shadcn/ui on Vercel (root: web/); backend: FastAPI + SQLAlchemy 2 + psycopg 3 on Render Free, Singapore (root: api/); data: Supabase Free: Postgres (session pooler), Auth (email + anonymous), Storage bucket 'snapshots'; ai: Gemini free (primary) + Groq free (fallback) via LLM gateway with Postgres cache; integrations: Tavily search, Resend email, Internet Archive CDX

## In scope
- C-05 pipeline (specs §1 C-05): discovery_candidates task, 3 Tavily basic searches, merge/dedupe/blocklist, verify (robots, 200, India signals), TF-IDF similarity, pricing page finder, classify_competitors task
- discovery_candidates table (0005_discovery.sql); guest limit 2/day, global 20/day
- POST /profiles/{id}/discovery, GET candidates, GET/POST competitors, PATCH competitor, POST monitoring/start (baseline)
- LLM extract_pricing on changed/new pricing sections (≤2,500 tokens), merged with rules
- S-07 live step list + candidate log; S-08 tabs, checkboxes, India signals, similarity, Add competitor URL; S-17 lists sources
- Seed: precompute StackNest discovery + baseline in record mode so guest clones are instant

## Out of scope for this step
- Comparison matrix (B09)
- Wayback backfill (B12)

## Suggested tasks
- tdd India signals + blocklist + similarity threshold on fixtures
- Pipeline + endpoints
- S-07/S-08 UI
- TAVILY_API_KEY on Render

## Skills — use in this order
1. **tdd** — India-signal scoring and domain blocklist on fixtures/pricing-pages and robots files
2. **fastapi** — only if not loaded this session

Always-on rules for every step: **ponytail**.

## Done when (check on the deployed app, not locally)
1. On <FRONTEND_URL> with the B07 profile: Find competitors → S-07 shows each step's count within 90 s
2. S-08 lists ≥ 3 verified competitors serving India (e.g. Indian or India-serving deployment providers) with signals; rejected candidates show reasons
3. Add competitor URL = the NimbusDeploy (demo) mock URL from Demo Lab → appears as 'Added by you' → Start monitoring → S-09 shows the baseline run done
4. Guest account: a 3rd discovery in a day returns the friendly limit message

## If it goes wrong
Seeded profiles use their stored discovery run; on Tavily failure, LLM candidates + verification only (step marked skipped).

## When finished
1. Make sure everything above is deployed (frontend, backend, database) and the done-check passes on the public URL.
2. Set `"status": "done"` for B08 in `docs/build-plan/plan.json`, then run `python C:\Users\Niranjan Iyer\.claude\skills\synced\4388f05c-eb72-4dd8-a66b-700dfbb34581_a5c3319d-ef87-457c-8cc8-fe986ddce72a\prototype-build-planner\scripts\build_plan.py render docs/build-plan/plan.json`.
3. Commit as `B08: Automated competitor discovery in India`.
4. Report what changed and the done-check result, then stop. Don't start the next step without being asked.

## Notes
Checkpoint 2 after B10: /code-review low.


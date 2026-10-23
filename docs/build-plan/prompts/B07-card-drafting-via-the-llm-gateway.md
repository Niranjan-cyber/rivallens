# B07 — Card drafting via the LLM gateway

Build step B07 of **RivalLens (working name)** (Prototype). Paste this into Claude Code / Codex / Cursor at the repo root. Do only this step.

## Read first
- `docs/build-plan/BUILD-PLAN.md` (section B07) and `docs/build-plan/plan.json`
- `AGENTS.md`, `SKILL-PLAYBOOK.md`, `SKILLS.md`
- `hacknova26-competitor-intel-feature-scope.md` (Feature scope: only if the step touches scope or cut list; grep the heading)
- `hacknova26-competitor-intel-user-journeys.md` (User journeys: grep only the screens (S-xx) and use cases (UC-xx) this step lists)
- `hacknova26-competitor-intel-architecture.md` (Architecture: grep only the ADRs/components (C-xx) this step lists)
- `hacknova26-competitor-intel-specs.md` (Specs: grep only the sections this step cites (e.g. '### C-08', '## 2. API contracts' endpoint names))
- `fixtures/README.md` (Fixtures README: only for parser/test steps; never open raw HTML fixtures)

## The goal (the only goal of this step)
A signed-in user types one line about their business on S-04 and gets a pre-filled S-05 wizard with AI-drafted badges, then saves the profile and sees its card on S-06.

**Why now:** First live LLM call: proves the gateway (Gemini → Groq fallback, cache, rate limits, replay mode) before discovery and extraction depend on it.

## Slice
- Use cases: UC-02
- Screens: S-04, S-05, S-06
- Components: C-01, C-03, C-04, C-14, C-15, C-19, C-20
- Stack: frontend: Next.js 15 App Router + TS + Tailwind + shadcn/ui on Vercel (root: web/); backend: FastAPI + SQLAlchemy 2 + psycopg 3 on Render Free, Singapore (root: api/); data: Supabase Free: Postgres (session pooler), Auth (email + anonymous), Storage bucket 'snapshots'; ai: Gemini free (primary) + Groq free (fallback) via LLM gateway with Postgres cache; integrations: Tavily search, Resend email, Internet Archive CDX

## In scope
- C-14 gateway: complete_json(task, schema, vars), llm_cache table (0004_llm.sql), token buckets from env, Gemini primary → Groq fallback on 429/5xx/timeout, LLM_MODE live|replay|record
- Task draft_card (specs §4.2) from description or homepage text (collector + robots)
- POST /profiles/draft (job), POST/PATCH/DELETE /profiles; default criteria_configs + alert_rules on create
- S-04 path choice + quick start; S-05 3-step wizard (product vs service, idea path fields); S-06 card preview with field origins
- Record first live responses into fixtures/llm/ (record mode) for tests

## Out of scope for this step
- Discovery (B08)
- LLM extraction of competitor pages (B08)

## Suggested tasks
- Check the Gemini free limits in AI Studio; set GEMINI_RPM/RPD; create GROQ key
- Gateway + cache + tests in replay mode
- Draft endpoint + wizard UI

## Skills — use in this order
1. **tdd** — gateway fallback + cache hit + schema-repair behaviour with recorded responses (LLM_MODE=replay)
2. **frontend-design** — no reload: wizard and card preview with B01 tokens

Always-on rules for every step: **ponytail**.

## Done when (check on the deployed app, not locally)
1. On <FRONTEND_URL> as an email user: S-04 → 'Pune startup, managed app deployment for Indian developers, Pro ₹999/mo' → Draft my card
2. Within 15 s S-05 is pre-filled (service, cloud deployment, ₹999/month) with AI-drafted badges → Finish → S-06 shows the card
3. Repeat the same draft → served from llm_cache (log shows cache hit, no provider call)
4. With GEMINI_API_KEY temporarily invalid on Render, drafting still works via Groq

## If it goes wrong
If both providers fail, 'Drafting unavailable, fill manually' opens the empty wizard.

## When finished
1. Make sure everything above is deployed (frontend, backend, database) and the done-check passes on the public URL.
2. Set `"status": "done"` for B07 in `docs/build-plan/plan.json`, then run `python C:\Users\Niranjan Iyer\.claude\skills\synced\4388f05c-eb72-4dd8-a66b-700dfbb34581_a5c3319d-ef87-457c-8cc8-fe986ddce72a\prototype-build-planner\scripts\build_plan.py render docs/build-plan/plan.json`.
3. Commit as `B07: Card drafting via the LLM gateway`.
4. Report what changed and the done-check result, then stop. Don't start the next step without being asked.

## Notes
Provider budget flags 1–2 (specs §4a): tests never use live keys.


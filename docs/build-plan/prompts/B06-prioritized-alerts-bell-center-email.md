# B06 — Prioritized alerts: bell, center, email, rules

Build step B06 of **RivalLens (working name)** (Prototype). Paste this into Claude Code / Codex / Cursor at the repo root. Do only this step.

## Read first
- `docs/build-plan/BUILD-PLAN.md` (section B06) and `docs/build-plan/plan.json`
- `AGENTS.md`, `SKILL-PLAYBOOK.md`, `SKILLS.md`
- `hacknova26-competitor-intel-feature-scope.md` (Feature scope: only if the step touches scope or cut list; grep the heading)
- `hacknova26-competitor-intel-user-journeys.md` (User journeys: grep only the screens (S-xx) and use cases (UC-xx) this step lists)
- `hacknova26-competitor-intel-architecture.md` (Architecture: grep only the ADRs/components (C-xx) this step lists)
- `hacknova26-competitor-intel-specs.md` (Specs: grep only the sections this step cites (e.g. '### C-08', '## 2. API contracts' endpoint names))
- `fixtures/README.md` (Fixtures README: only for parser/test steps; never open raw HTML fixtures)

## The goal (the only goal of this step)
After a price-cut run, a high-priority alert linking to the receipt appears in the bell (an email copy goes to the owner address).

**Why now:** Completes the detection → notification loop the PS demands; reuses B05 receipts.

## Slice
- Use cases: UC-08, UC-12
- Screens: S-11, S-16, S-17
- Components: C-01, C-03, C-09, C-15, C-21
- Stack: frontend: Next.js 15 App Router + TS + Tailwind + shadcn/ui on Vercel (root: web/); backend: FastAPI + SQLAlchemy 2 + psycopg 3 on Render Free, Singapore (root: api/); data: Supabase Free: Postgres (session pooler), Auth (email + anonymous), Storage bucket 'snapshots'; ai: Gemini free (primary) + Groq free (fallback) via LLM gateway with Postgres cache; integrations: Tavily search, Resend email, Internet Archive CDX

## In scope
- Migration 0003_alerts.sql: alerts, alert_rules (+ defaults on profile create/clone)
- C-09 priority score with stored breakdown, fingerprint dedupe ('seen again'), template alert text
- Resend email for score ≥ 70 to ALERT_EMAIL_OVERRIDE; never to anonymous users' addresses; email_status recorded
- GET /alerts, /alerts/unread-count, PATCH /alerts/{id}; GET/PUT alert-rules
- Bell dropdown (15 s poll), S-16 alert center with filters, S-17 rules toggles + min priority; S-11 shows the priority breakdown

## Out of scope for this step
- Sources management on S-17 beyond listing (B08)
- Verified email domain (MVP)

## Suggested tasks
- tdd the priority score + dedupe
- Endpoints
- Bell + S-16 + S-17 UI
- RESEND_API_KEY + ALERT_EMAIL_OVERRIDE on Render

## Skills — use in this order
1. **tdd** — priority score buckets (undercut bonus, needs_review) and fingerprint dedupe
2. **fastapi** — only if not loaded this session

Always-on rules for every step: **ponytail**.

## Done when (check on the deployed app, not locally)
1. On <FRONTEND_URL>: Demo Lab reset → price cut → Run monitor → bell badge shows 1 High alert → click → S-11
2. Run monitor again with no change → no new alert (S-16 shows 'seen again' unchanged or incremented, no duplicate)
3. Owner inbox receives the alert email with prev → curr and a working receipt link
4. S-17: raise min priority to 95 → repeat the cut → no alert created

## If it goes wrong
If Resend fails, email_status=failed is shown and the in-app alert path still demos.

## When finished
1. Make sure everything above is deployed (frontend, backend, database) and the done-check passes on the public URL.
2. Set `"status": "done"` for B06 in `docs/build-plan/plan.json`, then run `python C:\Users\Niranjan Iyer\.claude\skills\synced\4388f05c-eb72-4dd8-a66b-700dfbb34581_a5c3319d-ef87-457c-8cc8-fe986ddce72a\prototype-build-planner\scripts\build_plan.py render docs/build-plan/plan.json`.
3. Commit as `B06: Prioritized alerts: bell, center, email, rules`.
4. Report what changed and the done-check result, then stop. Don't start the next step without being asked.

## Notes
Cut order item 2: drop email if behind (keep bell + center).


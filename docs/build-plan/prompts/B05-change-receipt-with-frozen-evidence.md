# B05 — Change Receipt with frozen evidence

Build step B05 of **RivalLens (working name)** (Prototype). Paste this into Claude Code / Codex / Cursor at the repo root. Do only this step.

## Read first
- `docs/build-plan/BUILD-PLAN.md` (section B05) and `docs/build-plan/plan.json`
- `AGENTS.md`, `SKILL-PLAYBOOK.md`, `SKILLS.md`
- `hacknova26-competitor-intel-feature-scope.md` (Feature scope: only if the step touches scope or cut list; grep the heading)
- `hacknova26-competitor-intel-user-journeys.md` (User journeys: grep only the screens (S-xx) and use cases (UC-xx) this step lists)
- `hacknova26-competitor-intel-architecture.md` (Architecture: grep only the ADRs/components (C-xx) this step lists)
- `hacknova26-competitor-intel-specs.md` (Specs: grep only the sections this step cites (e.g. '### C-08', '## 2. API contracts' endpoint names))
- `fixtures/README.md` (Fixtures README: only for parser/test steps; never open raw HTML fixtures)

## The goal (the only goal of this step)
Clicking the meaningful change on S-10 opens S-11, which shows prev → curr, delta, observed-at and the before/after snapshot text with the price highlighted.

**Why now:** Second half of the winning moment; scores evidence accuracy and historical reliability.

## Slice
- Use cases: UC-05
- Screens: S-10, S-11
- Components: C-03, C-08, C-15, C-16, C-22
- Stack: frontend: Next.js 15 App Router + TS + Tailwind + shadcn/ui on Vercel (root: web/); backend: FastAPI + SQLAlchemy 2 + psycopg 3 on Render Free, Singapore (root: api/); data: Supabase Free: Postgres (session pooler), Auth (email + anonymous), Storage bucket 'snapshots'; ai: Gemini free (primary) + Groq free (fallback) via LLM gateway with Postgres cache; integrations: Tavily search, Resend email, Internet Archive CDX

## In scope
- Excerpt offsets stored on change_events (specs §1 C-08)
- GET /receipts/{id}, GET /receipts/{id}/evidence (text windows + highlight), GET /snapshots/{id}/html (signed URL)
- S-11 UI: values, dates (observed-at; published-at or 'happened between X and Y'), side-by-side highlighted text, 'View original' in a sandboxed iframe, Wayback link when present (null for mocks)
- POST /receipts/{id}/feedback 'Not relevant' (mutes field path)

## Out of scope for this step
- Priority breakdown display (B06)
- Simulator impact line (B10)

## Suggested tasks
- Offsets in diff output
- Receipt + evidence endpoints
- S-11 page; mobile-readable layout

## Skills — use in this order
1. **supabase** — only if not loaded this session: Storage signed URLs from the API
2. **frontend-design** — no reload: apply B01 tokens to S-11, the most screenshot-worthy screen

Always-on rules for every step: **ponytail**.

## Done when (check on the deployed app, not locally)
1. On <FRONTEND_URL> after the B04 price-cut run → click the change on S-10 → S-11 shows ₹1,499 → ₹899, −40%, observed-at timestamp
2. Before/after text panes highlight the price line; 'View original' opens a sandboxed iframe (no scripts run)
3. S-11 is readable on a phone-width window

## If it goes wrong
If signed URLs fail, hide 'View original' and keep the text evidence (the core proof).

## When finished
1. Make sure everything above is deployed (frontend, backend) and the done-check passes on the public URL.
2. Set `"status": "done"` for B05 in `docs/build-plan/plan.json`, then run `python C:\Users\Niranjan Iyer\.claude\skills\synced\4388f05c-eb72-4dd8-a66b-700dfbb34581_a5c3319d-ef87-457c-8cc8-fe986ddce72a\prototype-build-planner\scripts\build_plan.py render docs/build-plan/plan.json`.
3. Commit as `B05: Change Receipt with frozen evidence`.
4. Report what changed and the done-check result, then stop. Don't start the next step without being asked.

## Notes
Never inject scraped HTML into the app DOM.


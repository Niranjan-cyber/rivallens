# B14a — Real accounts: email and password

Build step B14a of **RivalLens (working name)** (Prototype). Paste this into Claude Code / Codex / Cursor at the repo root. Do only this step.

## Read first
- `docs/build-plan/BUILD-PLAN.md` (section B14a) and `docs/build-plan/plan.json`
- `AGENTS.md`, `SKILL-PLAYBOOK.md`, `SKILLS.md`
- `hacknova26-competitor-intel-feature-scope.md` (Feature scope: only if the step touches scope or cut list; grep the heading)
- `hacknova26-competitor-intel-user-journeys.md` (User journeys: grep only the screens (S-xx) and use cases (UC-xx) this step lists)
- `hacknova26-competitor-intel-architecture.md` (Architecture: grep only the ADRs/components (C-xx) this step lists)
- `hacknova26-competitor-intel-specs.md` (Specs: grep only the sections this step cites (e.g. '### C-08', '## 2. API contracts' endpoint names))
- `fixtures/README.md` (Fixtures README: only for parser/test steps; never open raw HTML fixtures)

## The goal (the only goal of this step)
A new user creates an account with email and password and is signed in straight away; each demo business has its own sign-in.

**Why now:** Everything after this belongs to a real account; the user asked for real sign-up first.

## Slice
- Use cases: UC-21, UC-01, UC-13
- Screens: S-02
- Components: C-01, C-02
- Stack: frontend: Next.js 15 App Router + TS + Tailwind + shadcn/ui on Vercel (root: web/); backend: FastAPI + SQLAlchemy 2 + psycopg 3 on Render Free, Singapore (root: api/); data: Supabase Free: Postgres (session pooler), Auth (email + anonymous), Storage bucket 'snapshots'; ai: Gemini free (primary) + Groq free (fallback) via LLM gateway with Postgres cache; integrations: Tavily search, Resend email, Internet Archive CDX

## In scope
- POST /api/v1/accounts creates the Supabase user already confirmed with the server key (no confirmation email)
- Sign-in page: email and password; 'Try demo account' guest stays

## Out of scope for this step
- Email confirmation, Gmail SMTP (dropped, D-83)
- Google sign-in (dropped, D-82)
- Phone OTP (paid, future scope)

## Suggested tasks
- accounts endpoint
- login page signs in after creating the account

## Skills — use in this order
1. **vercel-react-best-practices** — auth callback route + session refresh
2. **frontend-design** — sign-in and check-your-inbox screens
3. **supabase** — admin user creation with the server key

Always-on rules for every step: **ponytail**.

## Done when (check on the deployed app, not locally)
1. On <FRONTEND_URL> Create account with a new email and password → signed in and on onboarding at once
2. Log out, log in with the same email and password → back to the business
3. Same email again → 'already has an account'

## If it goes wrong
Supabase dashboard: turn off 'Confirm email' and use the normal sign-up call.

## When finished
1. Make sure everything above is deployed (frontend, infra) and the done-check passes on the public URL.
2. Set `"status": "done"` for B14a in `docs/build-plan/plan.json`, then run `python C:\Users\Niranjan Iyer\.claude\skills\synced\4388f05c-eb72-4dd8-a66b-700dfbb34581_a5c3319d-ef87-457c-8cc8-fe986ddce72a\prototype-build-planner\scripts\build_plan.py render docs/build-plan/plan.json`.
3. Commit as `B14a: Real accounts: email and password`.
4. Report what changed and the done-check result, then stop. Don't start the next step without being asked.


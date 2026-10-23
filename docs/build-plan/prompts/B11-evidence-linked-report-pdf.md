# B11 — Evidence-linked report + PDF

Build step B11 of **RivalLens (working name)** (Prototype). Paste this into Claude Code / Codex / Cursor at the repo root. Do only this step.

## Read first
- `docs/build-plan/BUILD-PLAN.md` (section B11) and `docs/build-plan/plan.json`
- `AGENTS.md`, `SKILL-PLAYBOOK.md`, `SKILLS.md`
- `hacknova26-competitor-intel-feature-scope.md` (Feature scope: only if the step touches scope or cut list; grep the heading)
- `hacknova26-competitor-intel-user-journeys.md` (User journeys: grep only the screens (S-xx) and use cases (UC-xx) this step lists)
- `hacknova26-competitor-intel-architecture.md` (Architecture: grep only the ADRs/components (C-xx) this step lists)
- `hacknova26-competitor-intel-specs.md` (Specs: grep only the sections this step cites (e.g. '### C-08', '## 2. API contracts' endpoint names))
- `fixtures/README.md` (Fixtures README: only for parser/test steps; never open raw HTML fixtures)

## The goal (the only goal of this step)
A user downloads a PDF report from S-15 in which every claim links to a receipt with its observed date (AI suggestions labelled separately).

**Why now:** PS deliverable ('sourced comparison report showing the change'); all evidence exists by now.

## Slice
- Use cases: UC-09
- Screens: S-15, S-11
- Components: C-03, C-12, C-14, C-15
- Stack: frontend: Next.js 15 App Router + TS + Tailwind + shadcn/ui on Vercel (root: web/); backend: FastAPI + SQLAlchemy 2 + psycopg 3 on Render Free, Singapore (root: api/); data: Supabase Free: Postgres (session pooler), Auth (email + anonymous), Storage bucket 'snapshots'; ai: Gemini free (primary) + Groq free (fallback) via LLM gateway with Postgres cache; integrations: Tavily search, Resend email, Internet Archive CDX

## In scope
- reports table; claims builder (receipts, comparison highlights, simulator recommendation), drop unevidenced claims → limitations
- report_summary LLM task (summary + suggestions citing claim ids), summary_unavailable fallback
- POST /profiles/{id}/reports (job), GET /reports/{id}; S-15 preview + print stylesheet + window.print()

## Out of scope for this step
- Emailing PDFs (MVP)
- Shareable link (not planned)

## Suggested tasks
- Claims builder
- Summary task
- S-15 UI + print CSS

## Skills — use in this order
1. **frontend-design** — no reload: print-friendly report layout with B01 tokens

Always-on rules for every step: **ponytail**.

## Done when (check on the deployed app, not locally)
1. On <FRONTEND_URL> StackNest → Reports → Generate → every claim has a receipt link + date; the AI suggestions block is labelled
2. Click a claim → S-11 for that receipt
3. Download PDF → the saved PDF keeps links and dates

## If it goes wrong
If the LLM summary fails, the structured report renders with 'summary unavailable'.

## When finished
1. Make sure everything above is deployed (frontend, backend, database) and the done-check passes on the public URL.
2. Set `"status": "done"` for B11 in `docs/build-plan/plan.json`, then run `python C:\Users\Niranjan Iyer\.claude\skills\synced\4388f05c-eb72-4dd8-a66b-700dfbb34581_a5c3319d-ef87-457c-8cc8-fe986ddce72a\prototype-build-planner\scripts\build_plan.py render docs/build-plan/plan.json`.
3. Commit as `B11: Evidence-linked report + PDF`.
4. Report what changed and the done-check result, then stop. Don't start the next step without being asked.


# B01 — Frontend shell live on Vercel

Build step B01 of **RivalLens (working name)** (Prototype). Paste this into Claude Code / Codex / Cursor at the repo root. Do only this step.

## Read first
- `docs/build-plan/BUILD-PLAN.md` (section B01) and `docs/build-plan/plan.json`
- `AGENTS.md`, `SKILL-PLAYBOOK.md`, `SKILLS.md`
- `hacknova26-competitor-intel-feature-scope.md` (Feature scope: only if the step touches scope or cut list; grep the heading)
- `hacknova26-competitor-intel-user-journeys.md` (User journeys: grep only the screens (S-xx) and use cases (UC-xx) this step lists)
- `hacknova26-competitor-intel-architecture.md` (Architecture: grep only the ADRs/components (C-xx) this step lists)
- `hacknova26-competitor-intel-specs.md` (Specs: grep only the sections this step cites (e.g. '### C-08', '## 2. API contracts' endpoint names))
- `fixtures/README.md` (Fixtures README: only for parser/test steps; never open raw HTML fixtures)

## The goal (the only goal of this step)
Anyone can open the public URL and click from the S-01 landing through stub screens S-03 to S-18 labelled sample data.

**Why now:** Forces the GitHub → Vercel deploy path to exist first and gives every later step a place to show its result.

## Slice
- Use cases: UC-13
- Screens: S-01, S-03, S-09, S-10, S-11, S-13, S-14, S-15, S-16, S-18
- Components: C-01, C-24
- Stack: frontend: Next.js 15 App Router + TS + Tailwind + shadcn/ui on Vercel (root: web/); backend: FastAPI + SQLAlchemy 2 + psycopg 3 on Render Free, Singapore (root: api/); data: Supabase Free: Postgres (session pooler), Auth (email + anonymous), Storage bucket 'snapshots'; ai: Gemini free (primary) + Groq free (fallback) via LLM gateway with Postgres cache; integrations: Tavily search, Resend email, Internet Archive CDX

## In scope
- Create GitHub repo (private ok), push current docs; Next.js 15 app in web/
- Visual direction set ONCE with frontend-design: tokens (colors, type, spacing) in web/app/globals.css + a short web/DESIGN.md
- S-01 landing with headline, 3-step strip, example noise ledger + receipt (static, labelled example)
- App shell: top bar (profile switcher stub, alert bell stub, Demo Lab link) + left nav (Dashboard, Competitors, Comparison, Simulator, Reports, Alerts, Settings) with stub pages showing a 'Sample data' badge
- Vercel project rooted at web/, Git auto-deploy on push to main

## Out of scope for this step
- Auth (B03)
- Any API call (B02)
- Real data on any screen

## Suggested tasks
- gh repo create + first push
- npx create-next-app web (TS, Tailwind, App Router); add shadcn/ui
- frontend-design pass → tokens + DESIGN.md
- Shell layout + stub routes /app/[profileId]/{dashboard,competitors,comparison,simulator,reports,alerts,settings} and /demo-lab
- Connect Vercel to the repo (Vercel MCP or dashboard), root directory web/
- Smoke script scripts/smoke.sh: curl <FRONTEND_URL> and grep the product name

## Skills — use in this order
1. **frontend-design** — pick the visual direction once (tokens, type scale, layout) for S-01 and the shell; later steps reuse it
2. **vercel-react-best-practices** — App Router layout and route structure only (skim SKILL.md, no rules files)

Always-on rules for every step: **ponytail**.

## Done when (check on the deployed app, not locally)
1. Open <FRONTEND_URL> → S-01 renders the headline and example receipt
2. Click into the app shell → every nav item opens a stub with a 'Sample data' badge, no 404s
3. bash scripts/smoke.sh passes against <FRONTEND_URL>

## If it goes wrong
If Vercel Git integration stalls, deploy with the Vercel MCP or `vercel --prod` from web/.

## When finished
1. Make sure everything above is deployed (frontend) and the done-check passes on the public URL.
2. Set `"status": "done"` for B01 in `docs/build-plan/plan.json`, then run `python C:\Users\Niranjan Iyer\.claude\skills\synced\4388f05c-eb72-4dd8-a66b-700dfbb34581_a5c3319d-ef87-457c-8cc8-fe986ddce72a\prototype-build-planner\scripts\build_plan.py render docs/build-plan/plan.json`.
3. Commit as `B01: Frontend shell live on Vercel`.
4. Report what changed and the done-check result, then stop. Don't start the next step without being asked.

## Notes
Keep stubs as one shared <StubPage> component; don't build real screens here.


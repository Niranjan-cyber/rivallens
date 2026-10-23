# RivalLens (working name): HackNova'26 competitor intelligence platform

Next.js (Vercel) web app + FastAPI (Render, Singapore) API + Supabase (Postgres, Auth incl. anonymous, Storage). Free LLM tiers only: Gemini primary, Groq fallback, cached in Postgres. Solo hackathon build; must be deployed by ~21:00 on 2026-10-23.

Source of truth. **Read by section, not whole:** grep the heading you need, e.g. `### C-08` or `## 2. API contracts`.
- Scope and winning feature: `hacknova26-competitor-intel-feature-scope.md`
- Screens S-01–S-19 and use cases UC-01–UC-15: `hacknova26-competitor-intel-user-journeys.md`
- Components C-01–C-27, ADRs, risks: `hacknova26-competitor-intel-architecture.md`
- API contracts, schema, LLM tasks, simulator formula, env vars: `hacknova26-competitor-intel-specs.md`
- Real page samples for parsers and tests: `fixtures/` (see `fixtures/README.md`). Never open the raw HTML in `fixtures/pricing-pages/` (up to 1.2 MB, single-line); grep it or load it from code.

**Decision log:** append every decision (D-xx) and learning (L-xx) to `LEARNINGS-AND-DECISIONS.md` as it happens: options considered, why, evidence, where it shows. Judges will ask "why"; this file is the answer.

Design: follow `web/DESIGN.md` (tokens in `web/app/globals.css`). Never use Mastercard's name, logo or brand colours.

Hard rules:
- Simulated or seeded data is always labelled demo data. Mock competitors are fictional.
- Respect robots.txt.
- Never render scraped HTML in the app DOM.
- Tests run with `LLM_MODE=replay` and never use live LLM keys.

## Build plan
- Plan: `docs/build-plan/BUILD-PLAN.md` (generated from `docs/build-plan/plan.json`; timeline in `timeline.html`).
- Work one step at a time using `docs/build-plan/prompts/<ID>-*.md`. Read only that step's section of BUILD-PLAN.md.
- In `plan.json`, only edit the step's `status`; don't read the whole file. Re-render after changing it.
- **Current step: B05** (change receipt with frozen evidence). B04 done: noise ledger live; re-seed with `MOCK_BASE_URL=https://rivallens-eight.vercel.app/mock` (seed fetches the deployed mock pages for the baseline). B03: Supabase project `isedhcbvuuglghcriicd` (Mumbai); DB via session pooler; seed/migrate with `cd api && .venv/Scripts/python -m scripts.setup_db --migrate --seed`.
- Live: web https://rivallens-eight.vercel.app (Vercel, root `web/`, Git auto-deploy) · API https://rivallens-api.onrender.com (Render `srv-dbdk8n6i0phs73a3k6mg`, Singapore, Free, Git auto-deploy, `cd api` build/start). Smoke: `FRONTEND_URL=… BACKEND_URL=… bash scripts/smoke.sh`. Freeze at 20:15; the cut order is in BUILD-PLAN.md open questions.

<!-- skill-stack-setup:start -->
## Agent skills

This repo ships agent skills (see SKILLS.md for details and reasons). Use them; don't reinvent their workflows.

Workflow: build in thin deployed slices → load the stack skill for the layer you touch → `tdd` (Matt Pocock plugin) for pipeline logic → `diagnosing-bugs` when something breaks → `code-review` before each checkpoint deploy.

| Skill | Use when |
|---|---|
| `supabase` | Anything touching Supabase Auth (incl. anonymous sign-in), `@supabase/ssr`, JWT verification, Storage signed URLs, RLS, Supabase errors |
| `supabase-postgres-best-practices` | Writing or changing tables, migrations, indexes, views, or slow queries |
| `fastapi` | Writing FastAPI routes, dependencies (auth), Pydantic models, background jobs |
| `vercel-react-best-practices` | Writing Next.js/React components, data fetching, caching (mock pages must be `no-store`) |
| `render-deploy` | Creating or changing the Render service, `render.yaml`, build/start commands |
| `render-debug` | A Render deploy fails, the service won't start, OOM or port errors, missing env vars |
| `frontend-design` | Designing or restyling any screen, especially S-01, S-10, S-11, S-14 |
| `ponytail` | Always on for code: smallest change that fully solves the task |

Precedence: `frontend-design` leads visual and UI decisions. `ponytail`'s minimal-change rule governs code structure, dependencies and abstractions. Specs in `hacknova26-competitor-intel-specs.md` win over generic skill advice when they conflict (e.g. sync SQLAlchemy + psycopg, no SQLModel).
<!-- skill-stack-setup:end -->

<!-- skill-conductor:start -->
## Skill routing

Before each task, pick the route below, say `Skills: <chain> (task: …; phase …)`, then load each skill and follow it. In Claude Code, invoke it; other agents read `.agents/skills/<name>/SKILL.md`. Full playbook: SKILL-PLAYBOOK.md.

**Mode:** Sprint, token-minimizing. **Current phase:** 1 · Plan (then 2 · Build loop).

| Task | Route |
|---|---|
| Build step | step prompt from BUILD-PLAN.md → stack skill for the layer → `tdd` only for pipeline logic → deploy → tick step |
| UI | `frontend-design` (set tokens once, reuse) |
| FastAPI | `fastapi` |
| Schema / migration | `supabase-postgres-best-practices` |
| Auth / storage / Supabase errors | `supabase` |
| React caching or data fetching | `vercel-react-best-practices` (matching `rules/` file only) |
| Bug / failing test | `mattpocock-skills:diagnosing-bugs` |
| Render failure | `render-debug` + Render MCP |
| Deploy | Render MCP (`render-deploy` first time only) · Vercel Git auto-deploy |
| Checkpoint | `/code-review low` |
| Deliverables | `hackathon-demo-submission` → `pptx` |
| Small edit ≤ 20 lines | no skill |

**Switch when:** error or failing test → `diagnosing-bugs` · Render 5xx/OOM → `render-debug` · 401/RLS → `supabase` · 20:15 → freeze, golden-path QA only · 20:30 → deliverables.

**Token rules:**
- One session per build step.
- Load each skill once, `SKILL.md` only; open its references only when needed.
- Read docs by section.
- No subagent or fan-out skills.

**Always on:** `ponytail`. **Precedence:** specs file > skill advice; `frontend-design` leads visuals. No matching skill → work normally.
<!-- skill-conductor:end -->

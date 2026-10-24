# RivalLens (working name): HackNova'26 competitor intelligence platform

Next.js (Vercel) web app + FastAPI (Render, Singapore) API + Supabase (Postgres, Auth with email + password, Storage). Free LLM tiers only: Gemini primary, Groq fallback, cached in Postgres. Started as a solo hackathon build (submitted 24 Oct 2026); now being improved live.

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
- **Branches: the submitted demo is frozen.** Tag `demo-v1` = the demo as submitted; `main` stays at that demo and is what Render (branch `main` only) and Vercel production deploy. All improvement work goes on branch `improve` (Vercel gives it preview URLs; Render ignores it). Merge to `main` only when the owner says so. The Supabase database is shared with the live demo: migrations must be additive (new nullable columns/tables only), and don't run `build_demo.py` or delete data without asking.
- **Now (from 24 Oct): improvement phase on the live product.** Build steps B01–B14k and workstreams WS1–WS5 are done; `finalVersion.md` is the current state (features, what's real, limits, architecture, major files). `docs/HANDOFF.md` is history up to B14k. Work in small deployed slices; each ends with tests, `scripts/check-all.sh` or the matching `scripts/e2e/*.cjs` on the live URL, a D-xx/L-xx row and a push.
- History: **Prototype v2 complete (B14a–B14k). Phase two: reliability, not new dashboards (workstreams 1–5 in LEARNINGS D-90). Milestone 1 "first useful insight" is live: `/app/{id}/setup`, `GET /profiles/{id}/setup`, scripts/e2e/first-insight.cjs.** Demo sign-ins are built by `api/scripts/build_demo.py` (README "Demo businesses"). **New session? Read `docs/HANDOFF.md` first.** B14a–B14k done (email+password accounts, onboarding, products in exact categories, like-for-like comparison, Money, cited competitor money, Customers, Market). Deadline 08:00 24 Oct: PPT content v2 by 23:10, build B14a–B14j 23:10–07:00, B14k exit 07:00–08:00. The product becomes sign-up → onboarding → main dashboard → Product, Money, Market, Customers; demo businesses are built from real datasets, never hand-written (D-73 to D-76). B14 done: Done: golden path x2, smoke, README, deck (https://claude.ai/artifact/VYg6tpzmKbn8L8FuVphQeP, sources in docs/deck). Open (owner actions): repo is private; export the deck to .pptx; GitHub cron keep-warm not yet firing, add cron-job.org on /healthz. B13 done: all 4 demo profiles populated. B12 done: S-12 history (Wayback backfill cut). B11 done: evidence report + print-to-PDF. B10 done: simulator re-plans on receipts. Deadline moved to 23:00: freeze 22:15, deliverables 22:30. B09 done: comparison matrix. B08 done: discovery verifies Indian providers live; keep-warm pinger = .github/workflows/keep-warm.yml (every 10 min). B07 done: LLM gateway live (Gemini `gemini-flash-lite-latest` → Groq `openai/gpt-oss-120b`, Postgres cache, replay fixtures in fixtures/llm/). B06: alerts + Resend email. B05 done: receipts + evidence live. B04: noise ledger live; re-seed with `MOCK_BASE_URL=https://rivallens-eight.vercel.app/mock` (seed fetches the deployed mock pages for the baseline). B03: Supabase project `isedhcbvuuglghcriicd` (Mumbai); DB via session pooler; seed/migrate with `cd api && .venv/Scripts/python -m scripts.setup_db --migrate --seed`.
- Live: web https://rivallens-eight.vercel.app (Vercel, root `web/`, Git auto-deploy) · API https://rivallens-api.onrender.com (Render `srv-dbdk8n6i0phs73a3k6mg`, Singapore, Free, Git auto-deploy, `cd api` build/start). Smoke: `FRONTEND_URL=… BACKEND_URL=… bash scripts/smoke.sh`.

<!-- skill-stack-setup:start -->
## Agent skills

This repo ships agent skills (see SKILLS.md for details and reasons). Use them; don't reinvent their workflows.

Workflow: thin deployed slices → load the stack skill for the layer you touch → `tdd` for pipeline logic → `diagnosing-bugs` when something breaks → `web-design-guidelines` after UI changes → `/code-review low` before a deploy that changes behaviour.

| Skill | Use when |
|---|---|
| `supabase` | Supabase Auth (email + password, admin-created users), `@supabase/ssr`, JWT verification, Storage signed URLs, RLS, Supabase errors |
| `supabase-postgres-best-practices` | Writing or changing tables, migrations, indexes, views, or slow queries |
| `fastapi` | Writing FastAPI routes, dependencies (auth), Pydantic models, background jobs |
| `vercel-react-best-practices` | Writing Next.js/React components, data fetching, caching (mock pages must be `no-store`) |
| `render-deploy` | Creating or changing the Render service, `render.yaml`, build/start commands |
| `render-debug` | A Render deploy fails, the service won't start, OOM or port errors, missing env vars |
| `frontend-design` | Designing or restyling any screen |
| `web-design-guidelines` | Auditing changed UI files: accessibility, focus, forms, loading/empty/error states, phone layout. Audit only; `frontend-design` decides the look |
| `writing-guidelines` | Reviewing on-screen copy, README, `finalVersion.md`, deck content for plain, short language. Skip rules that only apply to Vercel's docs site (MDX `meta.contentType`, Vercel model names in examples) |
| `tdd`, `diagnosing-bugs` | Matt Pocock skills: global plugin in Claude Code, copied to `.agents/skills` for Codex |
| `ponytail` | Always on for code: smallest change that fully solves the task |

Precedence: `frontend-design` leads visual and UI decisions. `ponytail`'s minimal-change rule governs code structure, dependencies and abstractions. Specs in `hacknova26-competitor-intel-specs.md` win over generic skill advice when they conflict (e.g. sync SQLAlchemy + psycopg, no SQLModel).
<!-- skill-stack-setup:end -->

<!-- skill-conductor:start -->
## Skill routing

Before each task, pick the route below, say `Skills: <chain> (task: …; phase …)`, then load each skill and follow it. In Claude Code, invoke it; other agents read `.agents/skills/<name>/SKILL.md`. Full playbook: SKILL-PLAYBOOK.md.

**Mode:** Improve (live product, quality over speed), token-minimizing. **Current phase:** 5 · Improve.

| Task | Route |
|---|---|
| Improvement slice | `finalVersion.md` section for the area → stack skill for the layer → `tdd` for pipeline logic → push → live check script → D-xx/L-xx |
| UI | `frontend-design` (tokens in `web/app/globals.css`, reuse) → `web-design-guidelines` on the changed files |
| Copy / docs / deck text | `writing-guidelines` |
| Data quality (comparables, prices, facts) | `tdd` with a fixture from the real failing case first, then the fix |
| FastAPI | `fastapi` |
| Schema / migration | `supabase-postgres-best-practices` |
| Auth / storage / Supabase errors | `supabase` |
| React caching or data fetching | `vercel-react-best-practices` (matching `rules/` file only) |
| Bug / failing test | `mattpocock-skills:diagnosing-bugs` |
| Render failure | `render-debug` + Render MCP |
| Deploy | Render MCP (`render-deploy` first time only) · Vercel Git auto-deploy |
| Before a behaviour-changing deploy | `/code-review low` · `scripts/check-all.sh` after |
| Deliverables | `pptx` (deck), `writing-guidelines` (text) |
| Small edit ≤ 20 lines | no skill |

**Switch when:** error or failing test → `diagnosing-bugs` · Render 5xx/OOM → `render-debug` · 401/RLS → `supabase` · UI change done → `web-design-guidelines`.

**Token rules:**
- One session per improvement slice.
- Load each skill once, `SKILL.md` only; open its references only when needed.
- Read docs by section.
- No subagent or fan-out skills.

**Always on:** `ponytail`. **Precedence:** specs file > skill advice; `frontend-design` leads visuals. No matching skill → work normally.
<!-- skill-conductor:end -->

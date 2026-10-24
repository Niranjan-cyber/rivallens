# Skill playbook

> Made by skill-conductor on 2026-10-23 (16:50); updated 2026-10-24 for **Phase 5: Improve** (live product: reliability, data quality, UI polish). Token-minimizing policy. Agents: Claude Code (primary), Codex.
> Phases 0–4 below are the finished hackathon build, kept as history.
> The routing summary lives in AGENTS.md; this file is the full version. Update both together.

## Project in one line
RivalLens (working name), a HackNova'26 competitor-intelligence prototype. The stack is Next.js on Vercel, FastAPI on Render and Supabase. The plan lives in `hacknova26-competitor-intel-{feature-scope,user-journeys,architecture,specs}.md`. The build steps will live in `BUILD-PLAN.md` (from prototype-build-planner).

## Token budget rules (apply to every task)
1. **Load only one stack skill per task, and only its `SKILL.md`.** Open a skill's `references/` or `rules/` file only when the task hits that exact topic. Never read `vercel-react-best-practices/AGENTS.md` (the full compiled rules), `supabase/CHANGELOG.md` or `render-deploy/assets/*`.
2. **Don't reload a skill that's already loaded in this session.**
3. **Read planning docs by section, not whole.** Grep the heading you need (e.g. `## 2. API contracts`, `### C-08`) in `hacknova26-competitor-intel-specs.md` and read only that section. The specs and architecture docs are ~50 KB each.
4. **Never open the raw HTML fixtures** in `fixtures/pricing-pages/` (220 KB–1.2 MB, often a single line). Use grep, or load them from code and tests. Reading them is denied in `.claude/settings.json`.
5. **One session per build step.** Start a fresh session (`/clear`) with that step's prompt from the build plan, and finish by ticking the step in `BUILD-PLAN.md`. Run `/compact` if a session runs long.
6. **No subagent fan-out.** Don't use `mattpocock-skills:code-review` (2 parallel subagents), `/code-review ultra`, workflows or `research` agents. Review uses `/code-review low`.
7. **Use MCP tools instead of skill prose for platform operations.** Use the Render MCP and Vercel MCP for deploys, env vars and logs. Load `render-deploy` once, for the first API deploy only.
8. **Short routing:** one `Skills:` line per task; small edits (≤ ~20 lines, no new behaviour) need no skill at all.
9. **Output stays terse**, per `ponytail`. Don't echo files back after editing them.

## Installed skills by role

Load cost is the approximate size of `SKILL.md` only.

| Role | Lead skill | Also installed (use for) | Load cost | Notes |
|---|---|---|---|---|
| clarify | none (decisions are already made in the docs) | `mattpocock-skills:grilling` (not used in Sprint) | — | Ask one question in chat if something is truly ambiguous |
| spec | none (`hacknova26-competitor-intel-specs.md` is the spec) | — | — | Don't write new specs; edit that file if a contract changes |
| plan | `prototype-build-planner` (once) | `build-hackathon` (not used; scope is already done) | — | Produces `BUILD-PLAN.md` + per-step prompts |
| build | stack skill for the layer touched (below) + `ponytail` | — | — | |
| ui | `frontend-design` | `vercel-react-best-practices` (only for data fetching or caching code); `web-design-guidelines` (audit changed files after) | ~2.4k tok | Set the visual direction **once** (tokens, type, layout) in the first UI step; later UI steps reuse it without reloading |
| backend: API | `fastapi` | — | ~2.8k tok | Specs win: sync SQLAlchemy 2 + psycopg 3, not SQLModel or uv |
| backend: Supabase | `supabase` | `supabase-postgres-best-practices` (schema and migration steps only) | ~3.6k / ~0.8k tok | Auth (anonymous), `@supabase/ssr`, JWT verification, Storage signed URLs |
| debug: app logic | `mattpocock-skills:diagnosing-bugs` | — | plugin | Reproduce → root cause → regression test |
| debug: Render | `render-debug` | Render MCP logs tools | ~2.2k tok | Deploy fails, won't start, OOM, port, env |
| debug: Supabase | `supabase` | — | (loaded) | Auth, RLS, permission or storage errors |
| test | `mattpocock-skills:tdd` | — | plugin | **Only** for pipeline logic: section splitter, price rules, noise rules, diff, priority score, simulator, SSRF guard |
| review | built-in `/code-review low` | `simplify` (only if a file clearly bloats) | — | At checkpoints only, not per slice |
| qa | `scripts/check-all.sh` and `scripts/e2e/*.cjs` (standalone playwright-core on the live URL) | Playwright MCP (often locked), `run` | — | No skill load |
| ui audit | `web-design-guidelines` | — | small (fetches rules from GitHub) | Accessibility, focus, forms, loading/empty/error states; output `file:line` |
| copy / docs | `writing-guidelines` | — | small (fetches rules from GitHub) | On-screen text, README, `finalVersion.md`, deck content |
| perf/security | none | — | — | Security rules are in specs §6 (SSRF guard, sandboxed evidence, JWT) |
| docs/deliverables | `anthropic-skills:pptx` | `writing-guidelines` | — | Deck from `docs/deck/PPT-CONTENT.md` |
| ship: API | `render-deploy` (first deploy only), then Render MCP | `render-debug` | ~4.2k tok | Render Free, Singapore |
| ship: web | Vercel MCP / Git auto-deploy | — | — | No skill needed |

**Gaps (no skill, work normally):** clarify and spec (docs already cover them), perf.

## Modifiers (always on)
- **`ponytail`:** all code. Smallest change that solves the task; standard library and existing deps first; no speculative abstractions; terse replies. It wins over any skill that suggests scaffolding, extra layers or new dependencies. It does **not** override `frontend-design` on visual choices.
- **Hard rules from AGENTS.md:** demo-data labelling, robots.txt, no scraped HTML in the DOM, `LLM_MODE=replay` in tests.

## Phases

### Phase 0: Setup (mostly done)
- **Goal:** skills installed, context trimmed, repo ready.
- **Exit check:** this session restarted so the project skills load; `.claude/settings.json` active (`band-peer` and `design` plugins off for this project).
- **Chain:** none.
- **Skip:** `/setup-matt-pocock-skills` (not needed for `tdd` or `diagnosing-bugs`).

### Phase 1: Plan (once, about 10 min)
- **Goal:** ordered, deploy-first steps.
- **Exit check:** `BUILD-PLAN.md` exists. Step 1 is a deployed skeleton (Vercel + Render + Supabase reachable). Each step has a ready-to-paste prompt.
- **Chain:** `prototype-build-planner` (reads the 4 docs + SKILLS.md + this playbook; produces `BUILD-PLAN.md`, `plan.json` and step prompts).
- **Skip:** `build-hackathon`, `grilling`, `to-spec`, `to-tickets`.

### Phase 2: Build loop (until ~20:00)
- **Goal:** each step deployed and demoable.
- **Exit check per step:** the step's acceptance check passes on the **public URL**; `BUILD-PLAN.md` step ticked.
- **Chain per step:** fresh session with the step prompt → stack skill(s) for the layer touched (load each once) → for pipeline logic, `tdd` against `fixtures/` (red → green) → push → Vercel/Render auto-deploy → smoke-check the URL → tick the step.
- **Checkpoint review** (after the core loop step and after the discovery and simulator step): `/code-review low` on the diff since the last checkpoint. Fix blockers only.
- **Switch triggers:** see the table below.
- **Skip:** TDD for UI and CRUD; per-slice review; writing new specs.

### Phase 3: Harden (~20:00–20:30)
- **Goal:** the golden path works end to end on the public URL.
- **Exit check:** the journeys doc §9 demo path passes twice in a row on the deployed app (guest clone → card → discovery → baseline → Demo Lab cosmetic run shows 0 meaningful → price cut shows 2 meaningful → receipt → re-plan → PDF → quantum flags).
- **Chain:** Playwright MCP walkthrough → for any break, `diagnosing-bugs` (or `render-debug` / `supabase`) → redeploy → re-run.
- **Skip:** new features (freeze at 20:15), refactors, review.

### Phase 4: Ship deliverables (~20:30–21:00)
- **Goal:** repo, README, PPT, demo script ready.
- **Exit check:** README with setup, data sources, detection method and demo-data labelling; PPT exported; the public URL warmed (keep-warm pinger on).
- **Chain:** `hackathon-demo-submission` (README, demo script, judge Q&A) → `pptx` (PPT from those).
- **Skip:** a demo video unless the organizers require one.

### Phase 5: Improve (current, from 24 Oct)
- **Goal:** a more reliable, more accurate, easier product on the same stack. No new dashboards unless asked.
- **Exit check per slice:** `LLM_MODE=replay` tests pass; the matching live check (`scripts/check-all.sh` or one `scripts/e2e/*.cjs`) passes on the public URL after `/healthz` shows the new sha; a D-xx/L-xx row; `finalVersion.md` updated if behaviour or limits changed.
- **Chain per slice:** read the `finalVersion.md` section for the area → stack skill for the layer → `tdd` (start from the real failing case as a fixture) → push → live check → log.
- **UI slices:** `frontend-design` for the look → `web-design-guidelines` on the changed files → fix findings that matter.
- **Text slices:** `writing-guidelines`.
- **Review:** `/code-review low` before a deploy that changes behaviour.

## Routing table

| Task type | Route |
|---|---|
| vague request / new feature idea | ask one question in chat; check it against the scope doc's cut list; no skill |
| new feature with clear idea | add it to `BUILD-PLAN.md` as a step only if it's in the Must or Should tiers; else refuse politely (cut list) |
| implement a build step | step prompt → stack skill for the layer → `tdd` if pipeline logic → deploy → tick |
| UI / visual work | `frontend-design` (first UI step loads it; later steps reuse its tokens) |
| FastAPI routes, jobs | `fastapi` |
| schema, migrations | `supabase-postgres-best-practices` (+ `supabase` if RLS, views or Storage) |
| auth, sessions, storage | `supabase` |
| React data fetching / caching | `vercel-react-best-practices` (open only the matching `rules/` file) |
| bug in app logic / failing test | `mattpocock-skills:diagnosing-bugs` |
| Render deploy or runtime failure | `render-debug` + Render MCP logs |
| Supabase error | `supabase` |
| step finished | deploy + smoke-check; review only at checkpoints |
| improvement slice | Phase 5 chain |
| UI change finished | `web-design-guidelines` on the changed files |
| copy, README, deck text | `writing-guidelines` |
| checkpoint | `/code-review low` |
| before demo | Playwright MCP golden path → debug route for breaks |
| deploy | API: Render MCP (`render-deploy` only for the first deploy); web: Vercel Git auto-deploy |
| docs / deliverables | `hackathon-demo-submission` → `pptx` |
| small edit (≤ ~20 lines, no new behaviour) | no skill |

## Switch triggers

| Event | Switch to |
|---|---|
| Unintended failing test, stack trace, "doesn't work" | `diagnosing-bugs`, then back to the step |
| Render build/start failure, 502, OOM | `render-debug` |
| 401/403, RLS, JWT or storage errors | `supabase` |
| Pipeline logic (noise rules, diff, priority, simulator) starts inside a UI step | `tdd` for that function only |
| Visual work inside a backend step | `frontend-design` tokens already set → no reload; just follow them |
| Checkpoint reached | `/code-review low` |
| UI change finished | `web-design-guidelines` |
| LLM 429s in rehearsal | not a skill: set `LLM_MODE=replay` / record per specs §4a |

## Precedence
- The specs file beats generic skill advice (stack versions, ORM, contracts). Change the spec first if you deviate.
- `frontend-design` leads visuals; `vercel-react-best-practices` only for code-level React or Next.js patterns.
- `ponytail` governs code size and dependencies across all skills.
- Built-in `/code-review low` is the only reviewer. `mattpocock-skills:code-review` and `simplify` aren't run on the same diff.
- `prototype-build-planner` leads planning; `build-hackathon` is unused.

## First-run dependencies
- Project skills load only after this session restarts (pending).
- `.claude/settings.json` (project) disables the `band-peer@jam` and `design@knowledge-work-plugins` plugins for this repo; it takes effect next session (pending restart).
- `/setup-matt-pocock-skills`: not required for the routes used here (skipped).

## Changes log
- 2026-10-23 16:50: initial Sprint-mode playbook with token budget rules; disabled 2 unused plugins at project level; denied Read on raw HTML fixtures.
- 2026-10-24: Phase 5 (Improve). Added `web-design-guidelines` and `writing-guidelines` (Claude Code + Codex), `tdd` and `diagnosing-bugs` copied for Codex only; QA route moved to `scripts/check-all.sh` and e2e scripts; freeze triggers removed; WebFetch allowed for raw.githubusercontent.com.

# Agent skills in this repo

> Set up by skill-stack-setup on 2026-10-23. Agents: Claude Code, Codex. Scope: project (copied files, committed).
> Reproduce with `bash scripts/install-skills.sh`. Exact content hashes are in `skills-lock.json`.

## Project needs profile
This is a solo hackathon prototype (HackNova'26) that must be deployed by about 21:00 with a GitHub repo, PPT and live URL. The stack is:
- Next.js 15 on Vercel
- FastAPI on Render Free
- Supabase: Auth with anonymous guests, Postgres, private Storage for snapshots

Judges score data accuracy, change detection, history, evidence and usability, so the UI needs polish while the code has to stay small.

## Installed skills

| Skill | Source | Why for this project | Invoke | Phase |
|---|---|---|---|---|
| `supabase` | supabase/agent-skills @ `c9be0e931b79` (official) | Guest "Try demo account" uses anonymous sign-in; `@supabase/ssr` sessions in Next.js; FastAPI verifies Supabase JWTs; snapshots in a private bucket via signed URLs | Auto-triggers on any Supabase task | build |
| `supabase-postgres-best-practices` | supabase/agent-skills @ `c9be0e931b79` (official) | 18 tables + `mock_pages_public` view + indexes from the specs; RLS enabled with a public read view | Auto-triggers on schema/migration/query work | build |
| `fastapi` | fastapi/fastapi @ `69ddc2badf9d` (official, shipped in the FastAPI repo) | The whole API (C-03) is FastAPI: `Annotated` auth dependencies, background jobs, Pydantic response models | Auto-triggers on FastAPI code | build |
| `vercel-react-best-practices` | vercel-labs/agent-skills @ `063bee94c3f4` | The 18 Next.js App Router screens; mock pages (C-02) need correct no-cache rendering | Auto-triggers on React/Next.js work | build, review |
| `render-deploy` | render-oss/skills @ `8675173fe302` (official Render, MIT) | Deploying the FastAPI service (Singapore, Free); `render.yaml`; pairs with the connected Render MCP | Auto-triggers on "deploy to Render" | ship |
| `render-debug` | render-oss/skills @ `8675173fe302` (official Render, MIT) | Free-tier failure modes: port binding, 512 MB OOM, missing env vars, cold starts | Auto-triggers when a Render deploy or service fails | debug, ship |
| `frontend-design` | anthropics/skills @ `dbd4588f9e10` | Judges remember the noise ledger (S-10), Change Receipt (S-11) and simulator (S-14) screens; avoids a generic AI look | Auto-triggers on UI design work | build |
| `ponytail` | DietrichGebert/ponytail @ `09c434ab73ca` | 13 MVP use cases + auth in about 4.5 h solo: smallest change that works, standard library first, no speculative abstractions | Always on for code; "ponytail lite/full/ultra" changes the level | always |

**Already available globally (not copied into the repo):**
- **Matt Pocock skills plugin:** `tdd`, `diagnosing-bugs`, `prototype`, `code-review`, `grilling` and others. This is the process backbone.
- **anthropic-skills:** `prototype-build-planner`, `skill-conductor`, `build-hackathon`, `hackathon-demo-submission`, `pptx` (for the required PPT).

Codex does not see these Claude Code plugins.

## How to work with this stack
> Day-to-day routing and token rules: see `SKILL-PLAYBOOK.md` (it supersedes the review step below: `/code-review low` at checkpoints only).

1. Plan: run `prototype-build-planner` to turn the architecture and specs into deploy-first steps.
2. Each step: load the stack skill for the layer you touch (`supabase`, `fastapi`, `vercel-react-best-practices`). `ponytail` keeps the change minimal.
3. Pipeline logic (noise rules, diff, priority score, simulator): write it test-first with `tdd` against `fixtures/`.
4. UI screens: `frontend-design` sets the visual direction once (tokens, type, layout), then reuse it.
5. Something broken: `diagnosing-bugs`, or `render-debug` for Render deploy and runtime failures.
6. Before each checkpoint deploy: `code-review` (Matt Pocock) on the diff.
7. Ship: `render-deploy` for the API, Vercel MCP or Git deploy for the web app.
8. End: `hackathon-demo-submission` + `pptx` for the video script, README and PPT.

## Precedence rules
- `frontend-design` leads visual decisions. `ponytail` governs code structure, dependencies and abstractions.
- The project specs (`hacknova26-competitor-intel-specs.md`) win over generic skill advice. For example, the `fastapi` skill suggests SQLModel and uv, but the specs fix SQLAlchemy 2 + psycopg 3. Follow the specs unless you deliberately change them (then update the specs).
- Matt Pocock `code-review` is the reviewer; don't also run `ponytail-review` (not installed) on the same diff.

## First-run steps (do these once)
- [ ] Optional: `/setup-matt-pocock-skills` in Claude Code if you plan to use its issue-tracker-based skills (`to-tickets`, `triage`). It isn't needed for `tdd`, `diagnosing-bugs` or `code-review`.
- [ ] Restart the Claude Code / Codex session in this folder so the new project skills load.
- [ ] Commit `.claude/skills/`, `.agents/skills/`, `skills-lock.json`, `AGENTS.md`, `CLAUDE.md`, `SKILLS.md`, `scripts/install-skills.sh`.

## Where things live
- Claude Code: `.claude/skills/`
- Codex and others: `.agents/skills/`
- Shared instructions: `AGENTS.md` (Claude Code imports it via `CLAUDE.md`)
- Lockfile with source paths and hashes: `skills-lock.json`

## Updating and removing
- Update: `npx skills update -p -y`
- Remove one: `npx skills remove <skill> --agent '*'`
- Plugins: `claude plugin update <name>` / `claude plugin uninstall <name>`

## Considered but not installed

| Candidate | Source | Reason |
|---|---|---|
| Superpowers | obra/superpowers | A second full backbone; its mandatory brainstorm → plan cycle costs hours; conflicts with the Matt Pocock plugin |
| gstack | garrytan/gstack | Heavy, needs Bun (not installed), large context footprint |
| Addy Osmani agent-skills | addyosmani/agent-skills | Overlaps the Matt Pocock backbone |
| UI UX Pro Max | nextlevelbuilder/ui-ux-pro-max-skill | Overlaps `frontend-design`; plugin + Python scripts |
| webapp-testing | anthropics/skills | Playwright MCP already connected for the e2e smoke test |
| fastapi-templates, fastapi-python, fastapi-expert | wshobson/agents, mindrally/skills, jeffallan/claude-skills | The official FastAPI skill exists |
| deploy-to-vercel, vercel-cli-with-tokens | vercel-labs/agent-skills | Vercel MCP is connected; Git auto-deploy is enough |
| render-env-vars, render-cron-jobs, render-background-workers | render-oss/skills | Covered by render-deploy references; cron and workers are P2/P3 only |
| Matt Pocock project copies | mattpocock/skills | Already installed as a global Claude Code plugin; duplicates would double-trigger |

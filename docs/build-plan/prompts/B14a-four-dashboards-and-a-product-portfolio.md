# B14a — Four dashboards and a product portfolio

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
A company sees four dashboards (Product, Market intelligence, Economics, Customers) and, on Product, lists its existing products and adds a new one with a market category.

**Why now:** Every later dashboard and the per-product simulator hang off products; the nav restructure is visible immediately.

## Slice
- Use cases: UC-16
- Screens: S-20, S-09
- Components: C-28
- Stack: frontend: Next.js 15 App Router + TS + Tailwind + shadcn/ui on Vercel (root: web/); backend: FastAPI + SQLAlchemy 2 + psycopg 3 on Render Free, Singapore (root: api/); data: Supabase Free: Postgres (session pooler), Auth (email + anonymous), Storage bucket 'snapshots'; ai: Gemini free (primary) + Groq free (fallback) via LLM gateway with Postgres cache; integrations: Tavily search, Resend email, Internet Archive CDX

## In scope
- products table (profile_id, name, stage existing|new, category, price, unit, features, add_ons, url, is_demo_data)
- LLM drafts category + features from a URL or description (cached, replay fixture)
- App nav grouped into the four dashboards; current screens move under Market intelligence
- Demo products for the 4 seeded profiles and guest clones, labelled demo data

## Out of scope for this step
- Per-product comparison (B14e)
- Economics/Customers data (B14b, B14c)

## Suggested tasks
- Migration 0010_products
- products router
- S-20 Product dashboard: Existing / New tabs, Add product
- Nav regroup
- Seed + guest-clone products

## Skills — use in this order
1. **supabase-postgres-best-practices** — products table + index
2. **fastapi** — products CRUD + draft endpoint
3. **frontend-design** — four-dashboard nav and S-20

Always-on rules for every step: **ponytail**.

## Done when (check on the deployed app, not locally)
1. Try demo account on <FRONTEND_URL> → StackNest shows the four dashboards
2. Product dashboard lists StackNest's existing products with a market category
3. Add product (New) from a one-line description → saved with a category and features

## If it goes wrong
If the LLM draft fails, category is a dropdown the user picks.

## When finished
1. Make sure everything above is deployed (frontend, backend, database) and the done-check passes on the public URL.
2. Set `"status": "done"` for B14a in `docs/build-plan/plan.json`, then run `python C:\Users\Niranjan Iyer\.claude\skills\synced\4388f05c-eb72-4dd8-a66b-700dfbb34581_a5c3319d-ef87-457c-8cc8-fe986ddce72a\prototype-build-planner\scripts\build_plan.py render docs/build-plan/plan.json`.
3. Commit as `B14a: Four dashboards and a product portfolio`.
4. Report what changed and the done-check result, then stop. Don't start the next step without being asked.


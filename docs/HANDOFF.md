# Handoff: continue the RivalLens build (24 Oct 2026, 01:00 IST)

Read this first in a new session. Then read `AGENTS.md`, which loads automatically, and only the section of `docs/build-plan/BUILD-PLAN.md` for the step you're on.

## 1. Deadline and what to deliver

- **Final deadline: 08:00 IST, Sat 24 Oct 2026** (HackNova'26 at Pulzion, PICT Pune).
- **Deliverables:** the PPT (official template, max 10 slides), the deployed app, and a public GitHub repo.
- **Timeline:**
  - 01:00–04:00: build B14i and B14j
  - 04:00–05:00: polish and buffer
  - 05:00–07:00: B14k exit (walk-throughs, README, deck)
  - 07:00–08:00: freeze and submit
- **Owner actions:**
  - Make https://github.com/Niranjan-cyber/rivallens **public** before submitting (it's private now).
  - Build the final PPT from `docs/deck/PPT-CONTENT.md` in another chat.
- The owner is a solo founder-developer. Keep replies short and plain, end each step with a short status table, and wait for "continue" between steps.

## 2. Live system

| What | Where |
|---|---|
| Web (Next.js 16, Vercel, root `web/`, auto-deploy on push) | https://rivallens-eight.vercel.app |
| API (FastAPI, Render Free Singapore, `srv-dbdk8n6i0phs73a3k6mg`, auto-deploy on push) | https://rivallens-api.onrender.com (`/healthz` returns `{"version": "<git sha>"}`, so wait for the new sha after a push) |
| Render workspace for MCP logs | `tea-db89nv3ncjis73f54io0` |
| Database, auth, storage | Supabase project `isedhcbvuuglghcriicd` (Mumbai), session pooler |
| Migrations | `supabase/migrations/0001…0016`; apply with `cd api && .venv/Scripts/python -m scripts.setup_db --migrate` (re-runnable) |
| Tests | `cd api && LLM_MODE=replay .venv/Scripts/python -m pytest -q` (59 pass; never use live LLM keys in tests) |
| Web checks | `cd web && npx eslint <files> && npx tsc --noEmit -p .` (if `.next/types` complains about a deleted route: `rm -rf .next/types && npm run build`) |
| Keys | `api/.env` (Supabase, Gemini, Groq, Tavily, Resend) and the same on Render. **Secrets never go through chat** (D-40). |

## 3. Process rules (from AGENTS.md; follow them)

- **Work one step at a time.** For each step:
  - Say `Skills: <chain>` first.
  - Use TDD for pipeline logic.
  - Push, then verify every done-check **on the live URL** with a browser script.
  - Mark the step `done` in `docs/build-plan/plan.json` (only edit `status`, plus notes when re-planning). Re-render with `python "C:/Users/Niranjan Iyer/.claude/skills/synced/4388f05c-eb72-4dd8-a66b-700dfbb34581_a5c3319d-ef87-457c-8cc8-fe986ddce72a/prototype-build-planner/scripts/build_plan.py" render docs/build-plan/plan.json`.
  - Append a D-xx or L-xx row to `LEARNINGS-AND-DECISIONS.md`. The latest are **D-84** and **L-20**; rows go just before `## Learnings`.
  - Commit as `B14x: <title>` and push to `main`.
- **Hard rules:**
  - Demo or seeded data is always labelled. Mock competitors are fictional.
  - Respect robots.txt.
  - Never render scraped HTML in the app.
  - Never use Mastercard's name, logo or colours.
  - Use the smallest change that works ("ponytail").
- **The owner's rule: real data only, nothing intelligent hand-written (D-75).** Every number on screen is either entered or uploaded by the business, or comes from a public source with a link and date. Anything else is "Unknown". Demo businesses are built by **running the same pipeline** on licensed datasets and public pages.
- **Free tools only.** Anything paid goes to future scope: X API, Instagram/Facebook Graph, Razorpay/Shopify sync, phone OTP, verified email domain, always-on hosting, Crunchbase/Tracxn.
- **Keep the deck in step.** After each step, update `docs/deck/PPT-CONTENT.md` (move items to ✅ Built in slide 7 and fix slide 5's markers) and copy a screenshot into `docs/screenshots/`.

## 4. The product now

**Flow:** sign up with email and password, then onboarding (2 steps), business card, **Overview**, then four dashboards in the side nav: **Product · Money · Market · Customers**.

| Step | Status | What it does | Code |
|---|---|---|---|
| B01–B14 | done | Original competitor-monitoring prototype: collector, noise ledger, receipts, alerts, discovery, comparison, simulator, report, history, demo profiles | `api/app/modules/{collector,extractor,changes,alerts,discovery,comparison,simulator,reports,demo}` |
| B14a | done | Email and password only, **no confirmation email, no Google**. `POST /api/v1/accounts` creates a confirmed Supabase user with the server key, then the page signs in (D-82, D-83). "Try demo account" (anonymous guest with 4 cloned demo profiles) still exists | `api/app/modules/profiles/accounts.py`, `web/app/login/page.tsx` |
| B14b | done | Onboarding form → AI-drafted card → Overview (S-21). Grouped nav: `lib/screens.ts` (`groups`, `groupOf`), `components/side-nav.tsx` | `web/app/app/new/page.tsx`, `web/components/overview.tsx` |
| B14c | done | Products (existing/new) in an exact **Google product taxonomy** id plus a niche. Keyword shortlist, then the LLM picks an id from the list; Indian English handled ("football" means a soccer ball). Products listed at onboarding are classified in one batched LLM call on a thread. A product can be added from its page via schema.org JSON-LD | `api/app/modules/products/{taxonomy,classify,pages,router}.py`, `api/app/data/google-product-taxonomy.txt`, `web/components/products.tsx` |
| B14d | done | Product detail (S-23, `/app/<id>/product-detail?id=<product>`). Comparables come from brand stores' public product pages (JSON-LD), found through the business's competitors and Tavily, kept only if they're in the same taxonomy id; stored in `market_products` (shared). Shows price position against the median, premium inspirations (top quartile) and brand ranges with cited revenue. Users can paste a rival's product page | `api/app/modules/products/market.py`, `web/components/product-detail.tsx` |
| B14e | done | Money (S-24). CSV/XLSX upload with a column-mapping preview, manual entries, revenue, operating margin against **Damodaran India margins (Jan 2026)**, burn, runway (last 3 complete months), transaction log. Bank settlements aren't double-counted with order exports | `api/app/modules/money/{service,router}.py`, `api/app/data/damodaran-india-margins-2026.csv`, `web/components/money.tsx` |
| B14f | done | Competitors' revenue, profit and funding from news and filings. Kept only if the quote is word for word in the source, the amount matches, it isn't a comparison figure, and results state a period (D-80). Shown on Money and on product Brands | `api/app/modules/money/facts.py`, `web/components/rival-money.tsx` |
| B14g | done | Customers (S-26). Uploads (reviews, comments, social insight exports), own-page JSON-LD reviews, web mentions (brand word + customer voice; no social or company-database sites). LLM sentiment plus up to 8 themes (request, complaint, praise), each citing mention ids that exist | `api/app/modules/customers/{service,router}.py`, `web/components/customers.tsx` |
| B14h | done | Market (S-09, slug `dashboard`). "Simulate a competitor move" (demo accounts with mock instances; replaces Demo Lab in the header), "Check competitors now", category prices now, Indian market news (Tavily news, Indian business domains, at least 2 market words) | `web/components/market-extras.tsx`, `api/app/modules/products/news.py` |
| **B14i** | **next** | Customer segment plus a per-product simulator fed by every dashboard | see §5 |
| B14j | todo | Four demo businesses built from real data | see §5 |
| B14k | todo | Exit: golden path v2 twice, README, deck, public repo | see §5 |

**Shared helpers to reuse:**
- `card_value(card, key)` in `api/app/modules/discovery/pipeline.py`. Card fields can be `{value, origin}` or plain strings, so always use it.
- `money_summary(conn, profile_id, card)` in `api/app/modules/money/router.py`
- `customer_summary(conn, profile_id)` in `api/app/modules/customers/router.py`
- `price_position()` in `products/market.py`
- `inr()` in `web/components/money.tsx`
- `rupees()` in `web/components/products.tsx`

## 5. Remaining steps in detail

### B14i: Customer segment and a simulator fed by every dashboard (about 1 h)

**Goal:** each product shows a suggested customer segment and its own simulator. Inputs come from Market (category prices, receipts), Money (unit cost, margin, runway) and Customers (sentiment, requested features), and each input links to its dashboard.

**Existing simulator:** `api/app/modules/simulator/{service,router}.py`.
- It works per profile, using the spec formula from §4.4 (`propose_options`, `conversion`, `break_even_month`, `recommend`, `viability_flags`).
- It has versioned `simulations` rows and re-plans on receipts (`replan()` is called from `changes/runs.py`).
- **Don't change the core formula.**

**Suggested minimal design:**
1. Migration: add a nullable `product_id` to `simulations`.
2. `GET /api/v1/products/{id}/simulation` builds the market price M from the product's category comparables (the `market_products` median for the same taxonomy id, or the existing profile comparables if empty). Then it overrides inputs:
   - unit cost and margin from `money_summary`
   - a runway flag when an option's break-even month is later than runway
   - sentiment shifting conversion, bounded ±20% and labelled "from Customers"
   - requested features (request themes) raising feature coverage
   - each input with `{source: "money" | "customers" | "market" | "default", link}`
3. Segment: one LLM task (cached, with a replay fixture) over price position, request/complaint themes, onboarding `target_customer` and the city. It returns `{segment, why[], evidence_ids[]}`, and a rule drops any segment whose evidence ids don't exist. Show it on S-23 above the simulator.
4. UI on S-23: a segment card plus simulator options table with input chips linking to `/money`, `/customers` and `/dashboard`.
5. Tests: hand-computed input mapping and bounds (TDD).

**Done-check (live):**
- Lower cash on Money → the product's simulator shows a runway flag.
- Upload negative reviews → expected conversion drops and the chip links to Customers.
- The simulated price cut on Market still re-plans.

### B14j: Four demo businesses built from real data (about 1.5 h)

**Goal:** four **separate sign-ins** (D-76), each opening with all four dashboards filled by **calling the same endpoints a user hits** from a builder script (`api/scripts/build_demo.py`), with no hand-written results. List the credentials in the README. Label each with `is_demo_data` and the text "Demo business, modelled on …".

| Business | Its own data (files exist unless noted) | Real market data |
|---|---|---|
| **Stride & Co.** (footwear D2C, Pune). Flagship | `fixtures/demo/stride/orders-oct2025-sep2026.xlsx` (UCI Online Retail II order rhythm, CC BY 4.0) and `bank-statement-oct2025-sep2026.csv` (costs from Campus Activewear FY26 gross margin 53.5%), regenerated by `api/scripts/demo_data.py`; cash ≈ ₹27,16,169 (closing balance). Reviews: no licensed shoe reviews (the HF sets have no licence), so use Customers "Collect" and leave the rest empty | Competitors: Nivia (niviasports.com, readable, also sells an ISL football at ₹3,499), Neemans (neemans.com), Campus (campusshoes.com product pages readable), Brooks India, Puma India. Products: Stride Runner ₹1,999, Stride Trail ₹2,499, socks ₹299. Money facts: "Campus Activewear" (Q1 FY26 revenue ₹343.3 cr, from its press release) |
| **Pune bakery** (local business) | Reviews: `fixtures/demo/bakery/reviews-amazon-fine-food-baked-goods.csv` (60 real reviews, Amazon Fine Food Reviews, SNAP/CC0; HF mirror `PJ2005/amazon-fine-food-reviews`, Apache-2.0). Transactions: **to build** from The Bread Basket (CC0, OpenML id 43422, Kaggle `mittalvasu95/the-bread-basket`), priced in ₹ from real Pune bakery menu pages where robots.txt allows | Theobroma works for web mentions (Reddit, Trustpilot) and cake/brownie categories |
| **StackNest** (cloud SaaS) | The existing seeded profile: monitored real competitors (Render, Railway, E2E Networks) plus fictional mocks for the simulate demo | Money: a public SaaS benchmark report (find one, free, cite it) or leave Money for upload |
| **QuickKart** (quick commerce) | Lightest; cut first if short of time | Eternal (Blinkit) and Swiggy (Instamart) revenue from filings via money facts |

**Notes:**
- Each demo sign-in needs **mock instances** (fictional competitors) for "Simulate a competitor move". See `api/app/modules/demo/router.py` (`guest-clone` creates `mock_instances` and sources) and `api/scripts/setup_db.py`.
- The old hand-seeded histories (`api/app/modules/demo/history.py`, D-72) should stop being used for these accounts. The owner judged seeded intelligence "garbage".
- **If time runs short, cut in this order:**
  1. QuickKart's depth
  2. The bakery's competitors
  3. Web mentions

  Stride & Co. and StackNest must be complete.

### B14k: Exit (05:00–07:00)

1. **Golden path v2, walked twice on the live URL** (write it into README §demo):
   1. Sign in as Stride & Co.
   2. Overview
   3. Product → Stride Runner: running shoes only, price position, premium, segment
   4. Money: runway, margin vs Shoe 8.3%, Campus revenue with its quote
   5. Customers: themes with quotes
   6. Market: simulate a price cut → Check competitors now → 1 change, 4 ignored → receipt
   7. Back to Product: the simulator re-plans, citing the receipt, runway and requests
   8. Report PDF
   9. Switch to the bakery
2. **README:** rewrite for the four-dashboard product. Cover data sources and licences, demo sign-ins, free-tier limits, and what isn't built.
3. **Deck and repo:** final `PPT-CONTENT.md` with real screenshots, make the repo public, run `/code-review low` before the final deploy, and extend `scripts/smoke.sh`.

## 6. Live browser checks

Scripts are in `scripts/e2e/*.cjs` and use standalone playwright-core (the Playwright MCP is often locked by another session):

```bash
cd api && set -a && . ./.env && set +a   # SUPABASE_URL / SUPABASE_SERVICE_ROLE_KEY for test users
PW="C:/Users/Niranjan Iyer/AppData/Local/npm-cache/_npx/9833c18b2d85bc59/node_modules/playwright-core"
EXE=$(ls "/c/Users/Niranjan Iyer/AppData/Local/ms-playwright/chromium_headless_shell-1243/"*/chrome-headless-shell.exe | head -1)
node ../scripts/e2e/new-account-onboarding.cjs "$PW" "<out-dir>" "$EXE"
```

- **How the scripts work:** `new-account-onboarding.cjs` creates a confirmed test user with the admin API, walks onboarding, and deletes the user at the end (cascade). The other scripts reuse that flow and add one dashboard each.
- **Waiting for a deploy:**
  - **API:** loop until `curl -s https://rivallens-api.onrender.com/healthz` contains the new short sha.
  - **Web:** Vercel takes about 1–2 minutes.
  - Never use a bare `sleep` in a foreground command; use an `until` loop.

## 7. Gotchas already paid for (don't repeat them)

- **Writing Python from bash heredocs:** `\b` and `\s` inside non-raw Python strings turn into control characters or lose the backslash. Use the Write or Edit tools for regexes, and check with `grep -c $'\x08' file`.
- **FastAPI 0.161:** `BackgroundTasks` run **before** the request's `yield` database dependency commits (L-19).
  - Work that needs the request's new rows runs on its own `engine.begin()` transaction or a thread.
  - Jobs that use their own connections are fine.
  - `conn.commit()` inside `engine.begin()` raises.
- **Next.js 16:** page state survives navigation (the login form kept its tab after logout), so reset forms after success.
- **Next.js 16 with `cacheComponents`:** client components that use URL hooks need `<Suspense>` (the section page already wraps).
- **The Gemini free tier is rate-limited** to about 12 s between calls (`GEMINI_RPM=5`), so batch LLM work (`classify_many`) and cache everything. Empty answers are never cached.
- **Big brand sites:** Asics and Bata time out or need JavaScript. Puma, Brooks, Campus, Nivia and Neemans give JSON-LD.
- **Decimals:** Postgres numerics arrive as Decimal or string in JSON; cast to `float` in API responses.
- **Test selectors:** Next's route announcer also has `role=alert`, so use `p[role=alert]`. The header's business switcher is a `<details><summary>`.

## 8. Where things are written down

- Plan and prompts: `docs/build-plan/` (`BUILD-PLAN.md`, `plan.json`, `prompts/B14i-…md`, `timeline.html`)
- Decisions and learnings: `LEARNINGS-AND-DECISIONS.md` (D-73…D-84 cover this redesign)
- Use cases and screens for the redesign: `hacknova26-competitor-intel-user-journeys.md` §11 (UC-16–UC-22, S-20–S-26)
- Deck content for the official 10-slide template: `docs/deck/PPT-CONTENT.md`; screenshots in `docs/screenshots/`
- Earlier pitch deck (Slides artifact): https://claude.ai/artifact/VYg6tpzmKbn8L8FuVphQeP

## 9. First message to send in the new chat

> Read `docs/HANDOFF.md`, then continue the build with B14i using `docs/build-plan/prompts/B14i-*.md`. Same rules as before: one step at a time, verify on the live URL, update plan.json, the decision log and PPT-CONTENT.md, commit and push, then wait for "continue".

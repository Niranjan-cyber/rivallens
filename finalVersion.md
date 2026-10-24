# RivalLens: final working version

*State as of 24 Oct 2026, commit `e54c792` and later. Live, tested and documented.*

- **Live app:** https://rivallens-eight.vercel.app
- **API:** https://rivallens-api.onrender.com (`/healthz` shows the deployed commit)
- **Repository:** https://github.com/Niranjan-cyber/rivallens (private until the owner makes it public)
- **Deck content:** `docs/deck/PPT-CONTENT.md` · **Decision log:** `LEARNINGS-AND-DECISIONS.md` · **Setup and run:** `README.md`

---

## Part 1: The product, in plain words

### What it is
RivalLens is a market-intelligence web app for small Indian businesses: startups, D2C brands, local shops, service businesses and SaaS teams. A founder signs up, describes the business, and the app:

1. finds real competitors in India and checks each one is real and reachable,
2. finds products that are genuinely comparable to theirs and shows where their price sits,
3. watches competitors' pricing pages and proves every real change with a before-and-after receipt,
4. reads the founder's own sales, costs and reviews,
5. and turns all of it into findings with evidence and **one concrete next step**.

If the data isn't good enough to conclude something, it says so and explains what's missing instead of guessing.

### Who it is for and the problem it solves
India has over 2.2 lakh recognised startups and 7.8 crore registered enterprises, and almost none has a market-research team. Today they check competitor websites by hand, use page-watchers that alert on every banner change, or ask an AI that compares the wrong products and can't show its sources. RivalLens replaces all three with one place that ignores noise, compares like for like, and ties price decisions to cash and runway.

### How to use it

**Try a demo (1 minute)**
1. Open the app. On the login page, click **Stride & Co.** (running shoes) or **Kesar Bakehouse** (bakery café).
2. **Overview:** read the next step and the findings, e.g. *"Stride Runner at ₹1,999 is 34% below the median ₹3,024 of 9 like-for-like products"*, labelled **Observed**, with a link to the evidence.
3. **Product → Stride Runner:** open *Assumptions*, change *Price sensitivity* to 1.6 and click **Set**; the recommended price and the runway change. Click **Save this scenario** to keep a dated record of what changed and why.
4. **Market → Simulate a competitor move → Cut a price 40% → Check competitors now:** one real change appears with its **receipt** (the page before and after, the price highlighted, the date seen). *Redesign only* produces zero alerts, with every ignored difference listed.

**Your own business (10–15 minutes)**
1. **Create account**, then describe the business in two short steps (name, type, city, what you do, products, customers). Check the AI-drafted business card and click **Finish**.
2. You land on **Getting started**. Follow **Your next step** each time; each is done on the page:
   1. enter each product's price,
   2. **Find competitors** (1–2 minutes; each candidate is checked live),
   3. **Find products like yours**,
   4. **Start watching** (saves today's version of each competitor's pricing page).
3. Optional, but much better results: upload sales and costs on **Finance**, and reviews or comments on **Customers** (CSV or Excel).
4. Come back any time: the **Overview** shows what changed since your last visit, and competitors are re-checked weekly automatically.

### What you see on each screen
| Screen | What it shows |
|---|---|
| **Getting started** | Each setup step with its status (Done, To do, Working, Blocked, Optional), the one next step, findings, and data coverage per area (Covered, Missing, Check failed, Out of date) |
| **Overview** | The next step, the top 3 findings with evidence ("Show more" for the rest), "Since your last visit", and a status pill on each dashboard tile |
| **Product** | Products in exact categories; per product: price position against like-for-like products, the products compared (each linked and dated, excluded ones with the reason), premium examples, brand ranges, a suggested customer segment, and the price simulator |
| **Finance** | Revenue, expenses, margin against Damodaran's India industry margin, burn, runway, the transaction log; competitors' revenue and funding quoted from filings and news |
| **Market** | Competitors watched, recent checks, receipts, the noise ledger, alerts, category prices, Indian market news, and (demo businesses only) "Simulate a competitor move" |
| **Customers** | Sentiment, themes (requests, complaints, praise), each opening the quotes it comes from |
| **Reports** | A printable report where every claim links to its receipt |

---

## Part 2: What's real, and what isn't

| Real | Not real, and labelled |
|---|---|
| Competitors found by discovery: real Indian sites, each verified live (reachable, robots.txt allows it, India signals) | **Demo businesses** (Stride & Co., Kesar Bakehouse, StackNest, QuickKart) are fictional, labelled *"Demo business, modelled on …"* |
| Comparable products and prices: read from real store catalogues and product pages, with link and date | **Demo sales data** comes from public datasets (UCI Online Retail II, The Bread Basket), rescaled and re-dated, with attribution in `fixtures/demo/ATTRIBUTION.md` |
| Competitor revenue and funding: verbatim quotes from filings and news, with links | **Fictional competitor sites** (Monsoon Miles, ZephyrPace, NimbusDeploy, KiteHost, Orbitly) are hosted by the app at `/mock/…`, labelled *"Demo data: fictional company"* |
| Receipts: the actual saved pages before and after | **Simulator results** are a scenario model, labelled *"Scenario model, not a forecast"* |
| Industry margins: Damodaran (NYU Stern), India, Jan 2026 | **Default assumptions** (price sensitivity 1.2, conversion 3%) are labelled *Default* |
| Your Finance and Customers numbers: your own uploads | **Unit cost**, unless you enter yours, is estimated from the industry margin and labelled *Estimate* |

Every number on screen carries one of three labels: **Observed** (read from a public page), **Your data** (uploaded or entered), or **Estimate** (benchmark or model). AI-written text is labelled, and AI suggestions are dropped unless they cite evidence. Nothing intelligent is hand-written; the demo businesses are built by a script that uses the live app like a real founder.

---

## Part 3: Strengths, limits and shortcomings

### Strengths
- **Evidence for every claim.** Findings link to their source; receipts prove changes with saved pages; no conclusion without enough data.
- **Like-for-like or nothing.** Filter coffee powder is compared only with filter coffee powder (not cappuccinos, French presses or protein powder). A median needs at least 3 such prices. Prices at ₹0, in another currency or more than 5× from the median are listed with the reason but not counted. A gap over 60% is flagged as a likely size or pack mismatch.
- **No false alarms.** Redesigns produce zero alerts, and every ignored difference is listed with the rule that ignored it.
- **Decisions tied to cash.** The simulator follows unit cost → gross profit → runway. An existing product is calibrated to its real sales, and the runway at today's price equals the Finance dashboard's runway.
- **Honest about gaps.** Stale data (checks over 14 days, prices over 30 or 90 days), failed checks and missing inputs are shown as such.
- **Guided.** A new founder reaches a useful next step without understanding the dashboards first; services businesses get their own path.
- **Built for India and free to run.** Rupee prices, India signals, Indian stores and benchmarks, all on free tiers.
- **Tested.** 92 automated tests, an account-isolation sweep over 54 API routes, live smoke tests, and live walk-throughs with 5 brand-new real-market businesses.

### Limitations
- **Password reset emails** reach only Supabase project team members until a free SMTP sender is configured in Supabase Auth. Changing your password while signed in works.
- **Price sensitivity is a default (1.2).** At that value raising prices usually wins; the sensitivity check shows how much the best price depends on it.
- **Services fit poorly into product categories** (Google's taxonomy covers goods), so gyms, photographers and SaaS get no product comparisons; they're compared through competitors' pricing pages.
- **Some sites can't be read:** JavaScript-only pages and sites that block automated reading (Blinkit, Zepto, Swiggy Instamart and similar). Rule-based price extraction leaves some values Unknown on complex pages.
- **Comparisons depend on how stores publish:** Shopify catalogues work well, others give fewer results. Pack size isn't normalised.
- **Free-tier ceilings:** the API sleeps after 15 idle minutes (about 50 s to wake); roughly 10 web-search-backed discoveries a day across all users (then AI-only, still verified); alert emails go only to the owner's inbox.
- **Web mentions** only work for real brands with distinctive names.
- **Demo businesses are shared;** anyone can change them (a script rebuilds them).
- **No history backfill;** monitoring starts from the first check.

### Shortcomings (what a commercial product still needs)
- Billing and plans, team workspaces and roles.
- Live integrations (Shopify, Razorpay, Tally) instead of file uploads.
- A verified email domain and SMTP for alerts and password resets.
- Pack-size and unit normalisation; estimating price sensitivity from real price changes.
- A headless browser for JavaScript-heavy pages; AI help for pricing extraction.
- Error tracking, uptime monitoring and usage analytics.
- Usability testing with real founders (the "understand your business in a minute" test needs people).

---

## Part 4: Architecture

```
Browser (Next.js 16 on Vercel)
   │  Supabase Auth: email + password → JWT on every API call
   ▼
FastAPI modular monolith (Render, Singapore, free)
   ├─ setup        plan: steps · coverage · findings · one next step   (reads everything below)
   ├─ products     taxonomy · classify · catalogue search · like-for-like · price screening
   ├─ simulator    gross profit · runway · calibration · sensitivity · scenarios
   ├─ money        uploads · metrics · benchmark · competitors' facts
   ├─ customers    uploads · sentiment · themes
   ├─ market       collector → extractor → changes (noise ledger, receipts) → alerts · discovery · comparison · reports
   ├─ jobs         jobs table + background tasks; cron/checks (scheduled)
   └─ LLM gateway  Gemini → Groq, cached in Postgres, replayed in tests
   ▼
Supabase (Mumbai): Postgres (18 migrations) · Auth · Storage (gzipped page snapshots)

Outside: public pages and Shopify catalogues (robots.txt, 1 req/s) · Tavily search · Google taxonomy · Damodaran India
Schedulers: GitHub Actions — scheduled-checks (daily) and keep-warm
```

**Key design decisions** (each recorded with options and evidence in `LEARNINGS-AND-DECISIONS.md`):
- **Rules decide, AI assists.** Change detection and comparability are rules; AI drafts the business card, classifies products, suggests competitors and segments, and summarises reviews, always with evidence or a label.
- **One plan, computed, not stored.** `GET /profiles/{id}/setup` derives steps, coverage, findings and the next step from saved data by a pure, tested function. No wizard state, so it survives refresh and logout (D-90).
- **Jobs are table rows.** Long work (discovery, comparables, checks, reports) runs as background tasks with a `jobs` row, so progress is visible and a restart marks unfinished work stale instead of losing it.
- **Isolation by query.** Every query is scoped to the signed-in user; another user's id behaves exactly like a missing one (404).
- **Scraped HTML never runs in the app.** Snapshots are stored privately; "View original" opens a sandboxed iframe via a 5-minute signed link.
- **No secrets through chat (D-40).** The scheduled-check endpoint needs no secret because it can only start checks that are already due.

### Request flow examples
- **A founder clicks "Find competitors":** `POST /profiles/{id}/discovery` → a job: the AI suggests candidates, web search adds more, each is verified (robots.txt, reachable, India signals) and ranked → competitors saved → the setup plan moves to the next step.
- **A competitor cuts a price:** a scheduled or manual check fetches each page → sections are diffed → the noise rules filter redesigns → a meaningful change becomes a receipt and an alert → it appears in "Since your last visit" and as a simulator input.
- **A founder changes an assumption:** `PUT /products/{id}/assumptions` → the simulator recomputes options, gross profit, runway at each price and sensitivity → **Save this scenario** stores it and lists what changed since the last save.

---

## Part 5: Tech stack

| Layer | Technology | Why |
|---|---|---|
| Web | Next.js 16 (App Router), React, Tailwind CSS v4 | Fast, Git auto-deploy on Vercel, print-to-PDF reports, phone layouts |
| API | Python FastAPI, SQLAlchemy 2 (sync) + psycopg 3, httpx, selectolax | Typed routes; a fast HTML parser that fits Render's 512 MB |
| Database, auth, files | Supabase Postgres, Auth, Storage | One free provider; Mumbai region |
| AI | Gemini `flash-lite` (primary), Groq `gpt-oss-120b` (fallback) | Free tiers; JSON-schema answers; cached; replayed in tests |
| Search | Tavily | Discovery, news and funding, each with a link |
| Hosting | Vercel (web), Render Free Singapore (API) | Free; auto-deploy on push to `main` |
| Scheduling | GitHub Actions | Daily competitor checks; keep-warm ping |
| Tests | pytest (92), Playwright scripts for live checks | Recorded AI answers (`LLM_MODE=replay`), never live keys |

**Free-tier handling:** AI answers cached and batched (8 per call); 3 web searches per discovery, 5 discoveries per account a day, AI-only discovery past the shared budget; reads retry while the API wakes; snapshots gzipped.

---

## Part 6: Major files and what they do

### Root
| File | What it is |
|---|---|
| `README.md` | Setup, golden path, how detection and evidence work, limits, how to run tests and checks |
| `finalVersion.md` | This document |
| `LEARNINGS-AND-DECISIONS.md` | Every decision (D-xx) and learning (L-xx) with options and evidence; the answer to "why" |
| `AGENTS.md` / `CLAUDE.md` | Instructions for coding agents working on the repo |
| `docs/deck/PPT-CONTENT.md` | Slide-by-slide content for the final deck |
| `docs/HANDOFF.md` | Session handoff notes and status |
| `docs/screenshots/` | Screenshots from the live app (m1-*, ws2-*, ws4-*, b14k-* are the latest) |
| `hacknova26-competitor-intel-*.md` | Original scope, user journeys, architecture and specs from the hackathon build |

### API (`api/`)
| File | What it does |
|---|---|
| `app/main.py` | Creates the FastAPI app and includes every module's router |
| `app/auth.py` | Verifies the Supabase JWT on each request (`UserDep`) |
| `app/db.py` | Database engine and per-request connection (`ConnDep`) |
| `app/config.py` | Environment variables (keys, URLs, email settings) |
| `app/jobs.py` | Background job runner: a `jobs` row with steps, result and error |
| `app/llm/gateway.py` | All AI calls: Gemini → Groq fallback, JSON-schema validation, Postgres cache, replay mode for tests |
| `app/modules/setup/service.py` | **The setup plan:** steps, coverage, findings (with the evidence thresholds) and the next step. Pure function |
| `app/modules/setup/router.py` | `GET /profiles/{id}/setup`: gathers products, competitors, checks, Finance and Customers; "since your last visit" |
| `app/modules/products/router.py` | Products CRUD, comparables search, like-for-like comparison and price position, market card, news |
| `app/modules/products/market.py` | Finding rivals' products (Shopify catalogue, product links), like-for-like matching, price screening |
| `app/modules/products/classify.py`, `taxonomy.py` | Exact Google-taxonomy category plus a niche, in batches of 8 |
| `app/modules/products/pages.py` | Reads a product's name, price, rating from a page's schema.org JSON-LD |
| `app/modules/simulator/service.py` | **The decision model:** conversion, gross-profit break-even, recommendation, calibration, runway, launch cash path, sensitivity, scenario differences |
| `app/modules/simulator/router.py` | Product simulator, editable assumptions, saved scenarios, segment suggestion |
| `app/modules/money/` | Finance uploads (preview, import), metrics, industry benchmark, competitors' revenue facts |
| `app/modules/customers/` | Review/comment uploads, sentiment, themes with quotes |
| `app/modules/collector/service.py` | Polite page fetching: robots.txt, 1 req/s per site, SSRF guard, size cap, one retry; snapshot storage |
| `app/modules/extractor/service.py` | Pulls plans, prices, features and headline from a page |
| `app/modules/changes/` | Monitoring runs, noise rules, receipts, evidence, scheduled checks (`POST /cron/checks`) |
| `app/modules/discovery/` | Competitor discovery: AI candidates + web search → verification → ranking |
| `app/modules/alerts/`, `comparison/`, `reports/` | Alerts and rules, the sourced comparison matrix, evidence-linked reports |
| `app/modules/profiles/` | Accounts (sign-up), business card drafting, profiles |
| `app/modules/demo/` | Demo-only: changing a fictional competitor's page ("Simulate a competitor move") |
| `scripts/setup_db.py` | Applies migrations (`--migrate`) and loads seed data |
| `scripts/build_demo.py` | Rebuilds the four demo businesses by calling the live API as each one |
| `scripts/isolation_check.py` | Account-isolation sweep over every API route |
| `tests/` | 92 tests; `test_setup.py`, `test_simulator.py`, `test_market.py` cover the phase-two logic |

### Web (`web/`)
| File | What it does |
|---|---|
| `app/login/page.tsx` | Log in, create account, forgot password, demo business buttons |
| `app/reset/page.tsx` | Set a new password (from the email link or "Change password") |
| `app/app/new/page.tsx` | Onboarding: two steps, AI-drafted card, then Getting started |
| `app/app/[profileId]/[section]/page.tsx` | Routes each section (`setup`, `home`, `product`, `finance`, `dashboard`, `customers`, …) to its component |
| `components/setup.tsx` | Getting started page, next-step control, findings, coverage, "since your last visit", add a product |
| `components/overview.tsx` | Overview: next step, findings, since last visit, dashboard tiles with status |
| `components/product-detail.tsx`, `product-plan.tsx` | Product page: comparison, who it's for, segment, simulator (assumptions, sensitivity, scenarios) |
| `components/money.tsx`, `customers.tsx`, `dashboard.tsx`, `market-extras.tsx` | Finance, Customers and Market dashboards |
| `components/receipt.tsx`, `run-result.tsx` | A change's receipt and a check's results with the noise ledger |
| `components/ui.tsx` | Shared pieces: logo, demo badge, error box with Try again |
| `lib/api.ts` | Calls the API with the user's token; retries reads while the API wakes |
| `lib/screens.ts` | The sections, their labels and which dashboard they belong to |
| `lib/mock-sites.ts` | The fictional competitor websites served at `/mock/…` |
| `DESIGN.md`, `app/globals.css` | Design system and colour tokens |

### Data and operations
| File | What it does |
|---|---|
| `supabase/migrations/0001–0018` | The database schema, in order (0017 product target customer, 0018 product assumptions and scenarios) |
| `fixtures/` | Real sample pages for parser tests, recorded AI answers, demo datasets with attribution |
| `scripts/smoke.sh` | Quick live check of pages, auth and demo sign-ins |
| `scripts/check-all.sh` | Before/after a deploy: tests, typecheck, smoke, isolation, live overview and simulator checks (`--full` adds a new-founder walk) |
| `scripts/e2e/*.cjs` | Live browser walks: `first-insight` (new founder, any business via `BIZ=`), `overview`, `simulator`, `golden-path-v2`, `demo-businesses` |
| `.github/workflows/scheduled-checks.yml` | Daily competitor checks |
| `.github/workflows/keep-warm.yml` | Pings the API so it sleeps less (GitHub runs it every 2–3 hours, not every 10 minutes) |

---

## Part 7: Important to know

**Running and checking**
- Tests: `cd api && LLM_MODE=replay .venv/Scripts/python -m pytest -q` (92 pass).
- Full live check: `PW=<playwright-core> CHROME=<chrome.exe> ISO_EMAIL=… ISO_PASSWORD=… bash scripts/check-all.sh`.
- A push to `main` redeploys both Vercel and Render. Render restarts kill running background jobs, so wait for `/healthz` to show the new commit before running live walks.
- New database columns must be migrated **before** the code that reads them deploys: `cd api && .venv/Scripts/python -m scripts.setup_db --migrate`.

**Accounts**
- Demo sign-ins: `stride@`, `bakery@`, `stacknest@`, `quickkart@rivallens.demo`, password `RivalLens-demo-2026` (also one click on the login page). They're shared; `python -m scripts.build_demo <keys>` rebuilds them.
- `founder-1792801994883@rivallens.test` is the isolation sweep's user A (its password is the one used by the e2e scripts); keep it.

**Rules the code follows**
- Demo data is always labelled; fictional competitors are fictional; robots.txt is respected; scraped HTML is never rendered; tests never use live AI keys; secrets never go through chat; free tools only.

**Owner actions still open**
1. Delete the leftover accounts (43 anonymous guests from the removed "Try demo account" feature, and old test founders) in the Supabase SQL editor:
   `delete from auth.users where is_anonymous;` and
   `delete from auth.users where email like '%@rivallens.test' and email <> 'founder-1792801994883@rivallens.test';`
2. Supabase Auth: add a free SMTP sender (e.g. Brevo) and the redirect URL `https://rivallens-eight.vercel.app/reset`, so password reset emails reach users.
3. Add cron-job.org pinging `/healthz` every 10 minutes (GitHub's schedule is too sparse to keep the API awake).
4. Make the repository public after checking its history for secrets; export the deck (retake screenshots that still say "Money").

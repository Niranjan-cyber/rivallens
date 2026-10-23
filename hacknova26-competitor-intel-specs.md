# RivalLens (working name) — Technical Specifications

Phase tags: **P1** Prototype (tonight), **P2** MVP, **P3** Production. Component IDs (C-xx), use cases (UC-xx) and screens (S-xx) match `hacknova26-competitor-intel-architecture.md` and `hacknova26-competitor-intel-user-journeys.md`.

## 1. Component specs

### C-01 Web app (P1)
- **Responsibility:** screens S-01–S-18; Supabase session (`@supabase/ssr`); attaches `Authorization: Bearer <access_token>` to every API call; polls `GET /jobs/{id}` (1.5 s) and `GET /alerts/unread-count` (15 s); print stylesheet for S-15.
- **Dependencies:** C-03, C-17.
- **Tech:** Next.js 15 App Router, TypeScript, Tailwind, shadcn/ui, Recharts, on Vercel Hobby. Pin exact versions in `package.json`.
- **Rendering rule:** scraped content is shown as **text with highlight spans** only. Original HTML opens in `<iframe sandbox="">` (no `allow-scripts`, no `allow-same-origin`) from a signed URL.
- **Config:** `NEXT_PUBLIC_SUPABASE_URL`, `NEXT_PUBLIC_SUPABASE_ANON_KEY`, `NEXT_PUBLIC_API_BASE_URL`.

### C-02 Mock competitor site (P1)
- **Responsibility:** serves `GET /mock/{instance_key}/{slug}` (S-19) and `GET /mock/{instance_key}/{slug}/robots.txt` is **not** needed. The host's `/robots.txt` must allow `/mock/`.
- **Rendering:** server component, `export const dynamic = "force-dynamic"`, response header `Cache-Control: no-store`. Reads `mock_instances` through a public read-only Supabase view `mock_pages_public` (instance_key, slug, version, overrides) with the anon key.
- **Page structure** (realistic, so extraction and noise rules are exercised for real):
  - `<nav>`
  - promo `<div class="banner">`
  - `<main><section id="pricing">` with 3 plan cards (`<h3>` plan name, price like `₹1,499 /month`, `<ul>` features)
  - `<section id="hero">` with an `<h1>` positioning line
  - `<footer>`
  - a permanent ribbon: "Demo data: fictional company"
- **Versions:**

  | Version | Content |
  |---|---|
  | `v1` | baseline |
  | `price_cut_40` | Pro ₹1,499 → ₹899 |
  | `add_feature` | adds "Mumbai region" to Pro |
  | `positioning` | new h1 |
  | `cosmetic` | nav order, banner text, CSS classes and a timestamp change only |

  Scenarios can stack.

### C-03 API service (P1)
- **Tech:**
  - Python 3.12, FastAPI, Uvicorn (1 worker)
  - Pydantic v2, SQLAlchemy 2 (sync) + psycopg 3
  - httpx, selectolax, scikit-learn (TF-IDF only)
  - `google-genai`, `groq`, `resend`, `tavily-python`, `PyJWT[crypto]`
- **Hosting:** Render Free web service in the Singapore region, `uvicorn app.main:app --host 0.0.0.0 --port $PORT`.
- **Code layout (modular monolith):**

  ```
  app/main.py
  app/auth.py
  app/db.py
  app/jobs.py
  app/modules/{profiles,discovery,collector,extractor,changes,alerts,comparison,simulator,reports,demo}/
  app/llm/
  ```

  Each module has `router.py`, `service.py` and `schemas.py`.
- **Jobs:** `jobs.start(kind, profile_id, fn)` inserts a `jobs` row and schedules `fn` via `BackgroundTasks`. `fn` calls `job.step(name, status, detail)`. On startup, jobs left `running` for over 10 min are set to `stale`.
- **Scaling:** single instance in P1–P2. In P3 the API is stateless and jobs move to C-26.
- **Config:** see §7.

### C-04 Profile & card drafting (P1)
- **Input:** URL or description. **Output:** `CardDraft` (§4.2) with `origin` per field (`ai_drafted` or `user`).
- URL path: C-06 fetches the homepage with a robots check, and the first 3,000 tokens of visible text go to the LLM task `draft_card`.

### C-05 Discovery engine (P1)
1. **Generate:** the LLM task `discovery_candidates` gets the card and returns ≤ 4 search queries and ≤ 10 candidates (`name`, `domain`, `why`), marked `ai_suggested`.
2. **Search:** Tavily `search(query, search_depth="basic", max_results=5)` for 3 of the queries. Keep result URLs whose domains are companies, and drop marketplaces, news sites, Wikipedia, G2 and Capterra using a blocklist.
3. **Merge:** dedupe by registrable domain and cap at 12. Remove the user's own domain.
4. **Verify each candidate:**
   - robots.txt allows `/`
   - the homepage returns 200 within 10 s
   - **India signals** are computed (see the table below)
   - `india_verified = score ≥ 1`
5. **Similarity:** TF-IDF cosine between the card text (category, attributes, description) and the homepage visible text. Drop candidates under 0.08 (tune on fixtures).
6. **Pricing page:** try `/pricing`, `/plans`, then `<a>` links whose text or href contains pricing, plans or price. Record `page_type`.
7. **Classify:** the LLM task `classify_competitors` labels each verified candidate `comparable` or `inspiration`, with a reason ≤ 20 words.
8. **Persist:** each candidate is stored with pass/fail reasons (shown on S-07). Verified candidates become competitors with `selected=true`.

| India signal | Weight |
|---|---|
| `₹`, `INR` or `Rs.` | +2 |
| `.in` TLD | +2 |
| "India" or an Indian city name | +1 |
| `+91` | +1 |
| GST or GSTIN | +1 |
| an India region such as Mumbai, Delhi, Hyderabad, Chennai or Bangalore | +1 |

### C-06 Collector (P1)
- **Fetch policy:**
  - `httpx.Client(timeout=15, follow_redirects=True, headers={"User-Agent": "RivalLensBot/0.1 (+<app url>/bot)"})`
  - robots.txt cached for 24 h per host via `urllib.robotparser`
  - per-host minimum interval of 1 s; max 3 MB body
  - only `text/html`
- **Statuses:** `ok`, `failed_http`, `failed_timeout`, `blocked_robots`, `needs_js` (visible text < 1 KB but HTML > 50 KB), `too_large`.
- **Output:**
  - raw HTML gzipped to Storage at `snapshots/{source_id}/{observed_at_iso}_{sha256[:12]}.html.gz`
  - visible text (scripts, styles, svg and noscript removed)
  - `sections`: a list of `{key, landmark, heading, text, hash}`
  - Section split order: landmark tags (`nav`, `header`, `footer`, `aside`, `main`), then `h1`–`h3` headings inside `main`, then elements whose id or class matches `pricing|plans|price`.
  - `key` = landmark plus a slug of the heading text; `hash` = sha256 of the normalized text (lowercased, whitespace collapsed, digits kept).

### C-07 Extractor (P1)
1. For each section, reuse the previous extraction when `hash` is unchanged (`method=reused`).
2. **Rules:** within pricing-like sections only, match prices with
   `(₹|Rs\.?|INR|\$|USD)\s?\d[\d,]*(\.\d+)?\s*(/|per)?\s*(mo|month|yr|year|hr|hour|user|seat)?`
   and bind each to the nearest preceding heading as the plan name. Plausibility bounds: 0 ≤ price ≤ 1,000,000; drop numbers in sentences with credits, revenue or customers.
3. **LLM:** for changed or new pricing and feature sections, call the task `extract_pricing` with input capped at 2,500 tokens. Merge it with the rules result; the LLM wins on plan names and features, the rules win on numeric price when both agree within 1%. If they disagree, mark `needs_review`.
4. **Output:** `ObservationFields` (§4.2) with `extraction_method` per field (`rules`, `llm`, `reused`, `manual_seed`).

### C-08 Change detector & receipts (P1)

**Diff:** compare the current and previous `ObservationFields` for the same source:
- `plans[]` matched by normalized name
- `price`, `currency`, `period`
- `features[]` as a set diff
- `headline`

**Noise rules** (each produces a `ledger_entries` row with this reason):

| Rule | Reason code |
|---|---|
| Section hash changed but `nav`, `header`, `footer` or `aside` landmark | `navigation_or_footer` |
| Section with class or id matching banner, promo, announcement or cookie | `promo_banner` |
| Raw HTML changed, visible text identical | `formatting_only` |
| Same multiset of lines, different order | `reordering` |
| Only dates, times, counters or numbers outside pricing sections changed | `dynamic_content` |
| Whitespace or case only | `whitespace` |

**Meaningful change types:** `price_increase`, `price_decrease`, `plan_added`, `plan_removed`, `feature_added`, `feature_removed`, `positioning_change` (headline token similarity < 0.8), `new_announcement` (P2).

**Suspicious** (status `needs_review`, no alert):
- a price disappeared while the page fetched OK
- |Δ| > 80%
- the currency changed
- rules and LLM disagree

**Receipt fields:**
- prev and curr values, `delta_pct`
- before and after `snapshot_id`
- `excerpt` with `{before:{start,end}, after:{start,end}}` character offsets into the snapshot text
- `observed_at` (current snapshot), `prev_observed_at`
- `published_at` (null unless the page shows a dated changelog entry)
- `wayback_url`: CDX lookup `closest` timestamp for the source URL (real sites only; null for mocks)

### C-09 Prioritizer & alerts (P1)

The score is explainable, and the breakdown is stored in `change_events.priority_breakdown`.
- **m (magnitude):** price `min(|Δ%|/50, 1)` · plan added/removed `0.7` · feature added/removed `0.6` · positioning `0.4`
- **r (relevance):**
  - comparable `1.0` · inspiration `0.5`
  - `+0.2` (capped at 1) if a comparable competitor's comparable-tier price crosses the user's planned price
- **s (source reliability):** official page `1.0` · Internet Archive `0.7` · mock `1.0` (labelled demo)
- **score** = `round(100 × (0.5·m + 0.35·r + 0.15·s))`
- **Buckets:** High ≥ 70 · Medium 40–69 · Low < 40
- **Rules:** an alert is created if the change type is enabled and score ≥ `min_priority` (default 40).
- **Dedupe:** `fingerprint = sha256(competitor_id | field_path | normalized curr_value)`. If one exists within 30 days, increment `seen_again` and create no new alert.
- **Email:** score ≥ 70 and `email_enabled`. The recipient is `ALERT_EMAIL_OVERRIDE` if set (P1: your Resend account email), otherwise the user's email (P2 only, after domain verification). The email is plain HTML with prev → curr, observed date and a receipt link. It is never sent to anonymous users.
- **Alert text** is template-based, not LLM: `"{competitor} {plan} {field} {prev} → {curr} ({delta}) · observed {date}{undercut_note}"`.

### C-10 Comparison engine (P1)

**Templates:**

| Template | Criteria |
|---|---|
| `service` | entry price (INR/month), mid-tier price, free tier (bool), India region (bool), support level, key features (set), positioning headline |
| `product` | price (INR), key specs (template from card attributes), variants count, rating (if a permitted source exists, else unknown), positioning |

- **Normalization:** amount × (`USD_INR_RATE` if USD) → INR. Period yearly ÷ 12 → monthly. Hourly prices aren't normalized; they show "per hour" and are excluded from monthly scores.
- **Score:** for each competitor, `Σ w_i·s_i / Σ w_i` over **known** cells only; `s_i` is min-max scaled per criterion (price is inverted). The `unknown_count` is reported per competitor and a competitor isn't ranked when known weight < 50%.

### C-11 Launch simulator (P1)
See §4.4 for the formula. Re-plan trigger: any `price_*`, `plan_*` or `feature_*` receipt for a comparable competitor. A new `simulations` version stores `replanned_from_version` and `trigger_change_event_id`.

### C-12 Report builder (P1)
- **Claims:** one per receipt in range (type, text, receipt_id, observed_at, source_url), plus comparison highlights (cell → receipt or observation id) and simulator recommendation (version id + cited receipts). Claims without an evidence id are dropped and listed in `limitations`.
- **LLM:** the task `report_summary` gets claims only and returns a summary (≤ 120 words) and suggestions, each citing `claim_ids`. Suggestions without valid claim ids are dropped.

### C-13 Demo Lab & seeds (P1)
- **Seed owner:** a fixed seed user id (`SEED_USER_ID`). The seeded profiles are:
  - StackNest (fictional; service, cloud deployment, Pune)
  - a quick-commerce profile (fictional brand)
  - Stride & Co. (fictional; product, shoes)
  - the quantum idea (Idea Card)
- Seeds include stored discovery candidates, competitors, sources, observations, receipts and a simulation; `is_demo_data=true` throughout.
- **Guest clone:** in one transaction, deep-copy the seed rows with new UUIDs and `user_id = caller`. Snapshots point to the same immutable storage paths; no copy is needed. A `mock_instances` row is created with `instance_key = random 10 chars`. Competitor sources pointing to mock pages are rewritten to the caller's instance URL.
- **Scenarios:** `price_cut_40`, `add_feature`, `positioning`, `cosmetic`, `reset`.

### C-14 LLM gateway (P1)
- **Interface:** `complete_json(task: str, schema: type[BaseModel], prompt_vars: dict, max_input_tokens: int) -> BaseModel`.
- **Cache:** key = sha256(task | prompt_version | provider-agnostic input text). Lookup happens before any provider call and is **global across users**, so identical competitor page sections are extracted once.
- **Routing:**
  - `LLM_PRIMARY=gemini`
  - on 429, 5xx, timeout (20 s) or schema failure after 1 repair → Groq
  - if both fail → raise `LLMUnavailable` (callers degrade; see §8)
- **Token bucket** per provider, from env: `GEMINI_RPM`, `GROQ_TPM`. The task waits up to 30 s for capacity, then falls back.
- **Modes:** `LLM_MODE=live|replay|record`. `replay` reads only the cache and `fixtures/llm/`, and raises on miss; tests use it. `record` writes responses to `fixtures/llm/`.
- **JSON:** Gemini via response JSON schema; Groq via JSON mode plus Pydantic validation.

### C-25 Keep-warm pinger (P1)
cron-job.org (or a GitHub Actions `schedule: */10 * * * *`) `GET {API}/healthz` from 30 min before judging until the end. Disable it afterwards to save Render hours.

## 2. API contracts

Base: `{API_BASE}/api/v1`, JSON, UTC ISO-8601 timestamps, UUID ids.

- **Auth (P1):** `Authorization: Bearer <Supabase access token>` on every endpoint except `/healthz`. The JWT is verified (§6). Every query is scoped to `user_id = sub`.
- **Errors:** `{ "error": { "code": "string", "message": "string", "detail": {} } }`.
- **Job response (202):** `{ "job_id": "uuid", "status": "queued" }`.
- **Rate limit (P1):** anonymous users get 2 discovery jobs/day and 20 runs/day. The global cap is 20 discovery jobs/day. Over the limit returns 429 `discovery_limit` or `run_limit`.

### Health
`GET /healthz` (P1, no auth) → `200 {"ok": true, "version": "git-sha"}`

### Demo / guest
`POST /demo/guest-clone` (P1). Auth: an anonymous user's JWT.
- Request: `{}`.
- **201:** `{ "profiles": [ProfileSummary] }`.
- **Errors:** `403 not_anonymous` · `409 already_cloned` · `500 clone_failed`.
- **Notes:** idempotent per user (the second call returns 409 with the existing profiles).

`GET /demo/mocks` (P1) → `200 { "instance_key": "string", "mocks": [{ "slug": "nimbusdeploy", "name": "NimbusDeploy (demo)", "version": ["v1"], "url": "https://<web>/mock/<key>/nimbusdeploy" }] }`

`POST /demo/mocks/{slug}/scenario` (P1)
- Request: `{ "scenario": "price_cut_40" | "add_feature" | "positioning" | "cosmetic" }`.
- **200:** `{ "slug": "string", "version": ["v1", "price_cut_40"] }`.
- **Errors:** `404 mock_not_found` · `422 bad_scenario`.

`POST /demo/mocks/reset` (P1) → `200 { "reset": 3 }`

### Profiles
`GET /profiles` (P1) → `200 [ProfileSummary]`. `ProfileSummary` = `{ id, name, kind: "business"|"idea", offering_type: "product"|"service", competitors_monitored:int, unread_alerts:int, last_run_at:ts|null, is_demo_data:bool }`.

`POST /profiles/draft` (P1, async)
- Request: `{ "kind": "business"|"idea", "url": "string?", "description": "string?" }`. At least one of `url` or `description` is required; `description` ≤ 500 chars.
- **202:** job. The job result is `CardDraft` (§4.2).
- **Errors (job):** `site_unreadable` · `blocked_robots` · `drafting_unavailable`.

`POST /profiles` (P1)
- Request: `{ "kind", "offering_type", "name", "card": Card }`.
- **201:** `Profile` `{ id, ...request, criteria_template, created_at }`. It also creates default `criteria_configs` and `alert_rules`.
- **Errors:** `422 validation_error` (field list).

`GET /profiles/{id}` · `PATCH /profiles/{id}` (card edits) · `DELETE /profiles/{id}` (P1) → `200 Profile` / `204`. Errors: `404 not_found`.

### Discovery & competitors
`POST /profiles/{id}/discovery` (P1, async)
- **202:** job.
- **Job steps:** `generate_candidates`, `search`, `verify`, `rank`, `find_pages`, `classify`. Each step is `{ name, status, count, detail }`.
- **Job result:** `{ "verified": int, "rejected": int }`.
- **Errors:** `429 discovery_limit`. Job error `no_verified_competitors`.

`GET /profiles/{id}/discovery-candidates` (P1) → `200 [{ id, name, domain, origin, status: "verified"|"rejected", reasons:[string], india_signals:{score:int, hits:[string]}, similarity:float }]`

`GET /profiles/{id}/competitors?relation=comparable|inspiration` (P1) → `200 [Competitor]`. `Competitor` = `{ id, name, domain, relation, origin: "ai_suggested"|"added_by_user"|"seed", selected:bool, monitorable:bool, india_signals, similarity, sources:[{id, url, page_type}] }`.

`POST /profiles/{id}/competitors` (P1, add own)
- Request: `{ "url": "https://..." }`.
- **201:** `Competitor` (origin `added_by_user`; India signals computed, and `india_verified=false` shown as "unverified").
- **Errors:** `422 invalid_url` · `422 blocked_robots` · `422 unreachable` · `409 duplicate`.

`PATCH /competitors/{id}` (P1)
- Request: `{ "selected": bool?, "relation": "comparable"|"inspiration"? }`.
- **200:** `Competitor`.

`POST /competitors/{id}/sources` (P1) · `DELETE /sources/{id}` (P1). Request: `{ "url", "page_type": "pricing"|"features"|"changelog"|"home" }`. Errors: as for adding a competitor.

### Monitoring
`POST /profiles/{id}/monitoring/start` (P1, async): baseline run over selected sources → **202** job with result `{ run_id }`.

`POST /profiles/{id}/runs` (P1, async) → **202** job with result `{ run_id }`. Errors: `409 run_in_progress` · `429 run_limit`.

`GET /runs/{id}` (P1) → `200`:
```json
{ "id": "uuid", "profile_id": "uuid", "status": "running|done|failed|stale",
  "started_at": "ts", "finished_at": "ts|null", "kind": "baseline|run",
  "counts": { "sources": 7, "diffs": 17, "ignored": 15, "meaningful": 2, "needs_review": 0, "failed": 0 },
  "changes": [ { "change_event_id": "uuid", "competitor": "NimbusDeploy (demo)", "change_type": "price_decrease",
                 "field": "plans.Pro.price", "prev": "₹1,499/month", "curr": "₹899/month", "delta_pct": -40.0,
                 "priority": 92, "bucket": "high" } ],
  "ledger": [ { "source_id": "uuid", "section_key": "nav", "reason": "navigation_or_footer", "summary": "Menu order changed" } ],
  "failures": [ { "source_id": "uuid", "status": "failed_timeout", "url": "string" } ] }
```

`GET /profiles/{id}/runs?limit=20` (P1) → `200 [RunSummary]`

### Receipts & snapshots
`GET /receipts/{id}` (P1) → `200`:
```json
{ "id": "uuid", "competitor": {"id":"uuid","name":"string"}, "source_url": "string",
  "change_type": "price_decrease", "field": "plans.Pro.price",
  "prev_value": {"amount":1499,"currency":"INR","period":"month"},
  "curr_value": {"amount":899,"currency":"INR","period":"month"},
  "delta_pct": -40.0, "status": "confirmed|needs_review",
  "observed_at": "ts", "prev_observed_at": "ts", "published_at": null,
  "wayback_url": "string|null", "is_demo_data": true,
  "priority": 92, "priority_breakdown": {"m":0.8,"r":1.0,"s":1.0,"undercut":true},
  "simulation_impact": {"version": 4, "recommended_before": 999, "recommended_after": 849} }
```

`GET /receipts/{id}/evidence` (P1) → `200 { "before": { "snapshot_id", "observed_at", "text_window": "string", "highlight": {"start":int,"end":int} }, "after": { ... }, "sha256": {"before":"hex","after":"hex"}, "evidence_missing": false }`. The `text_window` is ±600 chars around the excerpt.

`GET /snapshots/{id}/html` (P1) → `200 { "signed_url": "string", "expires_in": 300 }`

`POST /receipts/{id}/feedback` (P1)
- Request: `{ "relevant": false }`.
- **200:** `{ "muted_rule_id": "uuid" }` (mutes this field path for the competitor).

### Competitor history
`GET /competitors/{id}` (P1) → `200 { Competitor, "current_fields": ObservationFields, "timeline": [ { "type": "run|receipt|failure", "at": "ts", "ref_id": "uuid", "label": "string" } ], "price_series": [ { "plan": "Pro", "points": [ { "at": "ts", "amount_inr": 1499, "source": "observed|internet_archive" } ] } ] }`

`POST /competitors/{id}/archive-backfill` (P1 Should, async) → **202** job. The result is `{ "added_points": int }`. Job error: `no_archive_history`.

### Comparison
`GET /profiles/{id}/comparison?set=comparable|inspiration` (P1) → `200`:
```json
{ "template": "service", "criteria": [ {"key":"entry_price_inr_month","label":"Entry price","enabled":true,"weight":3,"direction":"lower_better"} ],
  "rows": [ { "subject": "you|competitor", "competitor_id": "uuid|null", "name": "string",
              "cells": { "entry_price_inr_month": { "value": 999, "display": "₹999/mo", "observed_at": "ts|null", "source_url": "string|null", "evidence_id": "uuid|null", "known": true } },
              "score": 0.62, "known_weight_pct": 83, "unknown_count": 1, "ranked": true } ],
  "assumptions": { "USD_INR_RATE": 84.0 } }
```

`PUT /profiles/{id}/criteria` (P1)
- Request: `{ "criteria": [ {"key","enabled","weight":0-5} ] }`.
- **200:** the comparison payload.

### Simulator
`GET /profiles/{id}/simulation` (P1) → `200`:
```json
{ "version": 4, "replanned": {"from_version": 3, "trigger_change_event_id": "uuid", "summary": "Recommended ₹999 → ₹849 because NimbusDeploy (demo) Pro −40%"},
  "label": "Scenario model, not a forecast",
  "assumptions": [ {"key":"segment_size","value":4000,"unit":"accounts","origin":"user|default|evidence","evidence_ids":[]} ],
  "market": { "median_price_inr": 1199, "n_priced": 5, "evidence_ids": ["uuid"] },
  "options": [ { "id":"A","price_inr":999,"origin":"proposed|user","feature_coverage":0.6,
                 "scenarios": { "best": {"conversion":0.041,"customers_m12":164,"revenue_12m_inr":1010000,"break_even_month":9},
                                "expected": {...}, "worst": {...} } } ],
  "recommended_option": "A", "reason": "string",
  "viability_flags": [ { "code":"no_breakeven_36m","severity":"high","text":"string","evidence_ids":[],"assumption_keys":[] } ] }
```
- **Errors:** `409 insufficient_price_data`.

`PUT /profiles/{id}/simulation/assumptions` (P1)
- Request: `{ "assumptions": { "key": number } }`.
- **200:** a new simulation version.

`POST /profiles/{id}/simulation/options` (P1)
- Request: `{ "price_inr": number, "features": [string]? }`.
- **200:** the simulation, with option `U`.

### Reports
`POST /profiles/{id}/reports` (P1, async)
- Request: `{ "from": "date", "to": "date", "competitor_ids": ["uuid"]? }`.
- **202:** job with result `{ report_id }`.

`GET /reports/{id}` (P1) → `200 { "id", "generated_at", "range", "summary": "string|null", "summary_unavailable": bool, "sections": [ { "title", "claims": [ { "id", "text", "evidence": { "type": "receipt|observation|simulation", "id", "observed_at", "source_url" } } ] } ], "suggestions": [ { "text", "claim_ids": [] , "label": "AI suggestion" } ], "limitations": [string] }`

### Alerts & rules
`GET /alerts?profile_id=&bucket=&type=&unread=` (P1) → `200 [ { "id", "profile_id", "change_event_id", "bucket", "priority", "text", "observed_at", "read": bool, "seen_again": int, "email_status": "not_sent|sent|failed|skipped" } ]`

`GET /alerts/unread-count` (P1) → `200 { "count": int, "top": [Alert ×5] }`

`PATCH /alerts/{id}` (P1)
- Request: `{ "read": bool?, "mute": "competitor"|"type"? }`.
- **200:** `Alert`.

`GET /profiles/{id}/alert-rules` · `PUT /profiles/{id}/alert-rules` (P1)
- Body: `{ "change_types": { "price": true, "feature": true, "plan": true, "positioning": true, "announcement": false }, "min_priority": 40, "email_enabled": true }`.

### Jobs
`GET /jobs/{id}` (P1) → `200 { "id", "kind": "draft|discovery|baseline|run|report|backfill", "status": "queued|running|done|failed|stale", "steps": [ { "name", "status", "count", "detail", "at" } ], "result": {}|null, "error": {"code","message"}|null }`

### Internal (P2)
`POST /internal/monitor-due`, header `X-Internal-Token`. Runs profiles whose cadence is due. Called by C-26 Render Cron.

## 3. Data schema (Postgres, Supabase)

All tables have `id uuid pk default gen_random_uuid()` and `created_at timestamptz default now()`. `user_id` references `auth.users(id)` with `on delete cascade`. **P1:** the backend connects as the DB owner and enforces `user_id` scoping in every query; RLS is enabled with no anon policies except `mock_pages_public`. **P3:** RLS policies for all tables.

| Table | Columns (type, constraints) | Indexes | Phase |
|---|---|---|---|
| `profiles` | user_id uuid not null; name text not null; kind text check in (business, idea); offering_type text check in (product, service); card jsonb not null (each field `{value, origin}`); is_demo_data bool default false; monitor_cadence text null (P2) | (user_id) | P1 |
| `discovery_candidates` | profile_id fk; job_id fk; name text; domain text; origin text; status text (verified/rejected); reasons text[]; india_signals jsonb; similarity real | (profile_id) | P1 |
| `competitors` | profile_id fk; name text; domain text; relation text (comparable/inspiration); origin text (ai_suggested/added_by_user/seed); selected bool default true; monitorable bool; india_signals jsonb; similarity real null; is_demo_data bool | unique(profile_id, domain) | P1 |
| `sources` | competitor_id fk; url text not null; page_type text; is_mock bool default false | unique(competitor_id, url) | P1 |
| `runs` | profile_id fk; job_id fk; kind text (baseline/run); status text; started_at, finished_at timestamptz; counts jsonb | (profile_id, started_at desc) | P1 |
| `snapshots` | source_id fk; run_id fk; observed_at timestamptz not null; status text; http_status int null; storage_path text null; sha256 text null; text text null; sections jsonb null (`[{key, landmark, heading, hash, start, end}]`); bytes int | (source_id, observed_at desc) | P1 |
| `observations` | snapshot_id fk unique; source_id fk; observed_at timestamptz; fields jsonb (ObservationFields); origin text (observed/internet_archive/seed) | (source_id, observed_at desc) | P1 |
| `ledger_entries` | run_id fk; source_id fk; section_key text; reason text; summary text | (run_id) | P1 |
| `change_events` | run_id fk; source_id fk; competitor_id fk; change_type text; field_path text; prev_value jsonb; curr_value jsonb; delta_pct real null; status text (confirmed/needs_review); before_snapshot_id fk; after_snapshot_id fk; excerpt jsonb; observed_at, prev_observed_at timestamptz; published_at timestamptz null; wayback_url text null; priority int; priority_breakdown jsonb; fingerprint text; is_demo_data bool | (competitor_id, observed_at desc); (fingerprint) | P1 |
| `alerts` | user_id; profile_id fk; change_event_id fk; bucket text; priority int; text text; read bool default false; seen_again int default 0; email_status text default 'not_sent' | (user_id, read, created_at desc) | P1 |
| `alert_rules` | profile_id fk unique; change_types jsonb; min_priority int default 40; email_enabled bool default true; muted jsonb default '[]' | — | P1 |
| `criteria_configs` | profile_id fk unique; template text; criteria jsonb | — | P1 |
| `simulations` | profile_id fk; version int; assumptions jsonb; options jsonb; recommended_option text; reason text; viability_flags jsonb; replanned_from_version int null; trigger_change_event_id fk null | unique(profile_id, version) | P1 |
| `reports` | profile_id fk; job_id fk; range jsonb; body jsonb | (profile_id) | P1 |
| `jobs` | user_id; profile_id fk null; kind text; status text; steps jsonb default '[]'; result jsonb; error jsonb; heartbeat_at timestamptz | (user_id, created_at desc) | P1 |
| `llm_cache` | key text pk; task text; provider text; model text; prompt_version text; response jsonb; input_tokens int; output_tokens int | (task) | P1 |
| `usage_counters` | scope text (user:uuid / global); day date; kind text; count int | pk(scope, day, kind) | P1 |
| `mock_instances` | user_id; instance_key text unique; slug text; version text[] default '{v1}'; overrides jsonb | unique(user_id, slug) | P1 |
| view `mock_pages_public` | select instance_key, slug, version, overrides from mock_instances | — | P1 |

**Object storage:** bucket `snapshots` (private). Path `snapshots/{source_id}/{observed_at}_{sha12}.html.gz`. Objects are immutable (never overwritten). Access only through 300 s signed URLs.

**JSON shapes:**
- `Card` = `{ name, website?, industry, india_markets:[string], offering_type, category, attributes:[string], price?:{amount, currency, period}, price_range?:{min, max}, problem?, target_customer?, planned_features?:[string], watch:[change_type], priorities:[criterion_key] }`. Each leaf is wrapped as `{value, origin: "user"|"ai_drafted"|"public_source"}`.
- `ObservationFields` = `{ plans:[{name, price:{amount:number|null, currency, period, raw}, features:[string], method}], headline:{text, method}|null, extraction_status: "ok"|"partial"|"failed" }`.

## 4. AI/ML pipeline specs

### 4.1 Models
| Role | Provider / model | Why | Fallback |
|---|---|---|---|
| Primary | Gemini API, a Flash or Flash-Lite class model available on your free tier (pick in AI Studio; set `GEMINI_MODEL`) | Native JSON-schema output; free | Groq |
| Fallback | Groq, Llama 3.3 70B class (`GROQ_MODEL`) | Fast; 1,000 RPD reported | Degrade (§8) |

Model IDs change often; set them in env vars and record the exact ID in `llm_cache.model`.

### 4.2 Tasks (prompt contracts)
| Task | Input | Output schema | Max input / output tokens | Used by |
|---|---|---|---|---|
| `draft_card` | kind, description and/or homepage text (≤3,000 tok) | `CardDraft` = Card with every field `origin=ai_drafted`, unknowns null | 3,000 / 700 | C-04 |
| `discovery_candidates` | card (≤800 tok) | `{queries:[string ≤4], candidates:[{name, domain, why}] ≤10}` | 800 / 900 | C-05 |
| `classify_competitors` | card + ≤12 `{name, domain, homepage_excerpt ≤150 tok}` | `[{domain, relation, reason ≤20 words}]` | 3,000 / 800 | C-05 |
| `extract_pricing` | section texts (≤2,500 tok), page URL | `ObservationFields` (null where absent; "never invent a price") | 2,500 / 700 | C-07 |
| `report_summary` | claims `[{id, text}]` (≤3,000 tok) | `{summary ≤120 words, suggestions:[{text, claim_ids}]}` | 3,000 / 600 | C-12 |

Prompt rules: system prompt says "use only the provided text; return null for unknown; do not infer prices or features". `prompt_version` constants live in `app/llm/prompts.py`.

### 4.3 Evaluation (P1 light, P2 real)
- **P1:** `tests/eval_extract.py` runs `extract_pricing` + rules over the 6 page fixtures (in replay or record mode) and asserts expected plan names and prices for 2 pages you label by hand.
- **P2:** 20 labelled pages; metrics are price exact-match rate, plan recall and false-change rate on cosmetic variants.

### 4.4 Launch simulator model (deterministic, P1)
- **Market:** `M` = median INR/month price of the comparable-tier plan across comparable competitors with known prices (needs n ≥ 2).
- **Proposed options:**
  - A = `round_99(0.85·M)` · B = `round_99(M)` · C = `round_99(1.15·M)`
  - plus the user's planned price as option P if it differs by more than 5%
  - plus user-added option U
- **Feature coverage:** `f` = |user features ∩ union of comparable features| / |union| (normalized names).
- **Assumptions:**

  | Assumption | Default | Notes |
  |---|---|---|
  | `segment_size` S | 4,000 accounts | |
  | `base_conversion` c0 | 3% at price = M, f = 0.5 | |
  | `elasticity` e | best 0.8 / expected 1.2 / worst 1.8 | |
  | `coverage_weight` k | 0.6 | |
  | `ramp_months` | 12 | |
  | `upfront_cost` U | ₹5,00,000 | |
  | `monthly_cost` F | ₹1,50,000 | |
  | `USD_INR_RATE` | 84 | |

  Ideas use user-entered values or labelled defaults.
- **Conversion:** `conv(p) = clamp(c0 · (p/M)^(−e) · (1 + k·(f − 0.5)), 0, 0.5)`
- **Customers at month m:** `S · conv · min(1, m/ramp_months)`
- **Revenue:** `rev_12 = Σ_{m=1..12} p · customers_m`
- **Break-even month:** first m ≤ 36 where cumulative revenue ≥ U + F·m, else `null` ("no break-even within 36 months under these assumptions").
- **Recommendation:** the option with the highest **expected** rev_12 among those whose worst-case break-even is not null. If none qualify, the highest expected rev_12, with a warning. Ties go to the lower price.
- **Viability flags (rules, each with evidence and assumption references):**

  | Code | Condition |
  |---|---|
  | `no_verified_india_competitors` | 0 India-verified comparables |
  | `crowded_segment` | ≥ 10 comparables |
  | `no_breakeven_36m` | null in all options × scenarios |
  | `capital_intensive` | U > 12 · expected monthly revenue at m = 12 |
  | `incumbent_heavy` | ≥ 3 inspiration competitors classified as large incumbents, with the reason from `classify_competitors` |

### 4.5 Cost per request
$0 on free tiers. Paid fallback (P2), assuming roughly $0.10–0.50 per 1M tokens for Flash-class models and about 40k tokens per golden-path run: under $0.02 per run. Verify current prices.

## 4a. Provider budget

Calls per golden-path run, from the sequence diagrams:
- draft 1 · discovery 2 · baseline extraction ≤ 8 (6 real sources + 1 mock + user site; global cache hits are likely because the seeded StackNest profile already extracted the same pages) · cosmetic run 0 · price-cut run 1 · report 1
- Total ≈ **13 LLM calls, about 30k input and 9k output tokens** worst case, with no cache hits.

| Provider / API | Tier | Limits | Calls per golden-path run | Typical in × out | Usage per demo run | Usage per test run | Usage per eval run | Shared quota with demo? | Headroom | Flag |
|---|---|---|---|---|---|---|---|---|---|---|
| Gemini (primary) | Free | **Unverified:** third-party reports range from 5–15 RPM and ~20–1,500 RPD; per Google Cloud project | 13 | 2.3k × 0.7k | 13 req | 0 (replay) / 13 if live | 6 (record) | **Yes** if the same project | Unknown; could be negative if RPD ≈ 20 | 🔴 **Flag 1** |
| Groq (fallback) | Free | ~30 RPM, ~1,000 RPD, ~12k TPM (Llama 3.3 70B; third-party) | 0–13 | 2.3k × 0.7k | ≤ 39k tokens | 0 (replay) | 0 | Yes (org-level) | RPD fine; **TPM: a burst of 8 extractions ≈ 24k tokens → ~2 min** | 🟠 **Flag 2** |
| Tavily | Free | 1,000 credits/month | 3 | — | 3 credits | 0 (mock) | 0 | Yes | ~330 discoveries/month | 🟢 |
| Resend | Free | 100/day, 3,000/month; owner address only without a domain | 1–2 | — | 2 | 0 (mock) | 0 | Yes | Fine | 🟡 **Flag 3** (recipient) |
| Wayback CDX | Free | Unpublished; be polite | 1 CDX + ≤ 12 fetches (backfill only) | — | ≤ 13 | 0 (fixtures) | 0 | — | Unknown | 🟢 (≤ 1 req/s) |
| Supabase | Free | 500 MB DB, 1 GB storage, pause after 7 days | — | ~200 KB gz per snapshot | ~2 MB | — | — | — | ~5,000 snapshots | 🟢 |
| Render | Free | 750 h/month, sleeps after 15 min | — | — | — | — | — | — | 1 always-on service fits | 🟠 **Flag 4** (cold start) |

**Mitigations:**
- **Flag 1:** check the limits page in AI Studio now and set `GEMINI_RPM` and `GEMINI_RPD`.
  - Tests and CI run `LLM_MODE=replay`, so they never use the live key.
  - Rehearsals use cached responses: run the golden path once in `record` mode, then everything replays from `llm_cache`.
  - If RPD < 100, use a **separate Google Cloud project/key for development**. Limits are per project, so a second key in the same project buys nothing.
  - Groq fallback is automatic.
- **Flag 2:**
  - section gating plus the 2,500-token cap
  - rules-first prices
  - token bucket (`GROQ_TPM=11000`)
  - seeded profiles precomputed
  - the global cache by section hash makes the live profile's real-page extractions cache hits
- **Flag 3:** set `ALERT_EMAIL_OVERRIDE` to your Resend account email for the demo; verify a domain in P2.
- **Flag 4:** C-25 keep-warm from 30 min before judging; open the URL 5 min before.

## 5. Integrations

| External system | Purpose | Auth | Rate limits | Failure handling | Fixtures | Phase |
|---|---|---|---|---|---|---|
| Competitor websites | Monitoring, discovery verification | none; robots.txt | self-imposed 1 req/s per host | status codes recorded; never a change | `fixtures/pricing-pages/`, `fixtures/robots/` | P1 |
| Tavily | Discovery search | API key | 1,000 credits/month | skip search step, LLM candidates only + note | doc-based, unverified (record into `fixtures/tavily/`) | P1 |
| Gemini | LLM primary | API key | see §4a | fallback to Groq | doc-based, unverified (`fixtures/llm/`) | P1 |
| Groq | LLM fallback | API key | see §4a | degrade (§8) | doc-based, unverified | P1 |
| Resend | Email | API key | 100/day | `email_status=failed`, in-app alert stays | doc-based, unverified | P1 |
| Internet Archive CDX | Permalinks, backfill | none | polite | null `wayback_url`; `no_archive_history` | `fixtures/wayback-cdx/` | P1 |
| Supabase Auth | JWT, anonymous users | anon key (client), JWKS (server) | — | 401 → re-login | doc-based | P1 |

## 5a. Doc vs reality

| Source | Field / behaviour | Docs or expectation | Real data shows | Impact on design |
|---|---|---|---|---|
| Real pricing pages (6) | Rendering | Concept doc assumes Playwright may be needed | All 6 contain prices in server-rendered HTML; visible text 12–24 KB, raw HTML 220 KB–1.2 MB | No headless browser in P1 (ADR-04); store raw in Storage, text in DB |
| E2E Networks (Indian provider) | Currency | Indian site → INR | Default fetch shows **USD** (`$7.99/hr`); `₹` appears only in a few places | Store currency as observed; INR conversion assumption (ADR-12); hourly prices not monthly-comparable |
| DigitalOcean, Railway | Numbers on pricing pages | Prices only | Non-plan numbers (`$829,000`, `$1,000–$10,000` credit tiers) | Section scoping + plausibility + context-word filter (C-07) |
| Wayback CDX (render.com/pricing) | Digest stability | Digest changes ≈ content changes | Digest differs on almost every capture in Jan 2025 | Never diff raw hashes; section text hashing + noise rules (ADR-05) |
| robots.txt (6 sites) | Pricing access | — | None disallow `/pricing`; they disallow app/auth paths (`/dashboard`, `/api/`, `/login`) | Monitoring pricing pages is allowed; robots check still runs on every fetch |
| Gemini free tier | Limits | — | Third-party sources conflict (20–1,500 RPD) | Flag 1 |

## 6. Auth and security

- **P1 auth model:**
  - Supabase email/password plus `signInAnonymously()` for guests
  - the access token is sent to FastAPI as a bearer token
  - FastAPI verifies with Supabase's JWKS (`{SUPABASE_URL}/auth/v1/.well-known/jwks.json`, RS256/ES256 signing keys)
  - **if the project still uses the legacy shared secret, verify HS256 with `SUPABASE_JWT_SECRET`** (check the project's JWT settings and implement whichever is active)
  - checks: `aud=authenticated`, `exp`; `sub` → `user_id`, `is_anonymous` claim → guest
- **Roles:** `user`, `guest` (anonymous: capped, no email, `guest-clone` allowed). No admin UI in P1; seeds are loaded by a script with the service role.
- **Authorization:** every repository function takes `user_id` and filters by it; `profile_id` ownership is checked before any child access, and violations return 404 (not 403) to avoid ID probing.
- **Secrets:** Render and Vercel env vars only; the service-role key and DB URL live **only** on Render; nothing secret is `NEXT_PUBLIC_*`.
- **Transport and CORS:** HTTPS everywhere; CORS allows only `WEB_ORIGIN` (+ Vercel preview pattern in P2).
- **Input validation:** Pydantic on all bodies. URLs must be `http(s)`. **SSRF guard on every fetch:** resolve DNS, reject private, loopback, link-local and metadata IPs, reject non-80/443 ports, re-check after redirects.
- **Scraped content safety:** never inject scraped HTML into the app DOM; text only. The original HTML is shown in a sandboxed iframe from a signed URL.
- **Abuse:** `usage_counters` caps (§2); a max of 12 competitors × 3 sources per profile.
- **Privacy:** store only email (Supabase) and business info. Guests are anonymous. A delete-profile cascade is included. P3: India DPDP Act review.

## 7. Configuration

| Env var | Component | Example | Secret? | Phase |
|---|---|---|---|---|
| `NEXT_PUBLIC_SUPABASE_URL` | C-01, C-02 | `https://xyz.supabase.co` | no | P1 |
| `NEXT_PUBLIC_SUPABASE_ANON_KEY` | C-01, C-02 | `eyJ...` | no (public) | P1 |
| `NEXT_PUBLIC_API_BASE_URL` | C-01 | `https://rivallens-api.onrender.com` | no | P1 |
| `SUPABASE_URL` | C-03 | `https://xyz.supabase.co` | no | P1 |
| `SUPABASE_SERVICE_ROLE_KEY` | C-03 (storage, seeds) | `eyJ...` | **yes** | P1 |
| `SUPABASE_JWT_SECRET` | C-03 (only if legacy HS256) | `...` | **yes** | P1 |
| `DATABASE_URL` | C-03 | session pooler URI `postgresql://postgres.<ref>:<pw>@aws-0-<region>.pooler.supabase.com:5432/postgres` | **yes** | P1 |
| `WEB_ORIGIN` | C-03 CORS, links | `https://rivallens.vercel.app` | no | P1 |
| `MOCK_BASE_URL` | C-13 | `https://rivallens.vercel.app/mock` | no | P1 |
| `GEMINI_API_KEY`, `GEMINI_MODEL`, `GEMINI_RPM`, `GEMINI_RPD` | C-14 | `…`, `<flash model id>`, `5`, `100` | key **yes** | P1 |
| `GROQ_API_KEY`, `GROQ_MODEL`, `GROQ_TPM` | C-14 | `…`, `<llama 70b id>`, `11000` | key **yes** | P1 |
| `LLM_PRIMARY`, `LLM_MODE` | C-14 | `gemini`, `live` | no | P1 |
| `TAVILY_API_KEY` | C-05 | `tvly-…` | **yes** | P1 |
| `RESEND_API_KEY`, `ALERT_FROM`, `ALERT_EMAIL_OVERRIDE` | C-09 | `re_…`, `onboarding@resend.dev`, `you@example.com` | key **yes** | P1 |
| `USD_INR_RATE` | C-10, C-11 | `84` | no | P1 |
| `SEED_USER_ID` | C-13 | uuid | no | P1 |
| `GUEST_DISCOVERY_PER_DAY`, `GLOBAL_DISCOVERY_PER_DAY` | C-03 | `2`, `20` | no | P1 |
| `INTERNAL_TOKEN` | C-03 internal endpoint | random | **yes** | P2 |
| `SENTRY_DSN` | C-01, C-03 | `https://…` | no | P2 |

## 8. Error handling and resilience

- **Timeouts:**

  | Call | Timeout | Retries |
  |---|---|---|
  | Fetch | 15 s | 1 retry on connect error |
  | LLM | 20 s | fallback once |
  | Tavily | 10 s | none |
  | Resend | 10 s | none |
  | CDX | 10 s | none |

- **Degrade paths:**

  | Failure | What happens |
  |---|---|
  | LLM down, card draft | `drafting_unavailable` → manual wizard |
  | LLM down, discovery | for seeded profiles, use the stored run; otherwise "discovery unavailable, add competitor URL" |
  | LLM down, extraction | rules-only, `extraction_status=partial` |
  | LLM down, report | structured report, `summary_unavailable=true` |
  | Tavily down | LLM candidates + verification only (job step `search` = skipped) |
  | Resend down | `email_status=failed` |

- **Never a false change:** failed, blocked, `needs_js` or `too_large` snapshots produce no observation and no diff. The next successful snapshot is compared with the last *successful* one.
- **Jobs:** heartbeat every step; `stale` after 10 min with no heartbeat; one active run per profile (409).
- **User-facing:** every error code maps to a plain sentence + next action in C-01 (`errors.ts` map).

## 9. Observability

- **P1:**
  - JSON logs (`job_id`, `user_id`, `profile_id`, `step`, `duration_ms`, `provider`, `tokens`) to Render logs
  - the `jobs.steps` timeline doubles as the user-visible log
  - `llm_cache` and `usage_counters` give LLM and API usage
  - `/healthz` returns the git SHA
- **P2:** Sentry (web + API), uptime monitor on `/healthz`, a daily usage summary log line.
- **P3:** dashboards for runs per day, failure rate per source, false-change rate (ledger "should have alerted" feedback), alert volume per user, and LLM tokens and spend; alerts on job failure rate > 20% and LLM fallback rate > 50%.

## 10. Testing strategy

| Level | What | Phase |
|---|---|---|
| Unit | Section splitter, price regex + plausibility, noise rules (cosmetic fixture → 0 meaningful), diff (price cut → 1 `price_decrease`), priority score, simulator formula, India signals, SSRF guard | P1 |
| Integration | Monitoring pipeline over mock page v1 → `price_cut_40` + `cosmetic` (expect ledger ≥ 5, meaningful = 2); runs with `LLM_MODE=replay` and fixture pages served locally | P1 |
| Extraction eval | 6 real fixtures, 2 hand-labelled (§4.3) | P1 light / P2 |
| End-to-end smoke | Deployed URL: guest clone → Demo Lab scenario → run → receipt visible (one Playwright script run from your laptop, not on Render) | P1 |
| Load | Not needed; P3: 50 concurrent runs on the worker | P3 |

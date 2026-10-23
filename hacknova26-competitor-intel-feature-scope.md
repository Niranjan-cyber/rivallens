# Competitor Intelligence & Market Monitoring Agent: Feature Scope

> **Partly superseded** (2026-10-23) by `hacknova26-competitor-intel-user-journeys.md` and `hacknova26-competitor-intel-architecture.md`. Changes: auth is now real sign-up/login plus a guest demo account (no longer a Won't/hardcoded user); the stack is fixed as Next.js on Vercel + FastAPI on Render + Supabase; the LLM is Gemini with a Groq fallback. Everything else in this scope still stands.

**Event:** HACKNOVA'26 (Pulzion) · **Deadline:** building until ~21:00, 2026-10-23 (official submission time not stated) · **Track:** Competitor Intelligence PS
**Prepared:** 2026-10-23, 15:46 · **Assumptions:** judging criteria are unweighted, so they're treated as equal. Solo builder with an AI coding agent. About 4.5 build hours remain after scoping and architecture.

---

## 1. Requirements snapshot

- **Problem statement (organizer):** monitor permitted public competitor sources. Detect meaningful changes in pricing, features, announcements and positioning, and keep a dated history. Compare competitors on configurable criteria, alert on significant developments, and generate concise reports in which every claim links to its source and observation date.
- **In one sentence:** a watcher that ignores page noise, catches real competitor moves, remembers when it saw them, and proves every claim it makes.
- **Judging criteria (unweighted, treated as equal):** data-collection accuracy · change-detection effectiveness · historical reliability · comparison quality · evidence and source-link accuracy · usefulness of alerts and reports · overall functionality and usability.
  - *Note:* six of the seven criteria score the **monitoring → evidence loop**. None scores discovery, launch simulation or viability prediction. Those extras can win "wow", but they can't replace a solid core loop.
- **Mandatory tech:** none. Wayback Machine, Common Crawl and Kaggle are optional resources.
- **Deliverables:**
  - a working platform with all of these components: monitoring, change detection, history, comparison, evidence-linked reporting, notifications and a dashboard
  - a **demo** in which monitored pages get a *simulated* price or feature change that is detected and appears in a sourced report
  - a brief technical write-up covering approach, data sources, detection method and key decisions
  - **confirmed by organizers: a GitHub repo, a PPT, and a deployed URL are all required**
- **Constraints:** permitted public sources only; respect ToS, robots.txt and rate limits; separate meaningful changes from cosmetic ones; minimize unnecessary alerts; handle missing or changing content; the project must be feasible in the hackathon window.
- **Gaps in the rules:** the official submission time and the demo length are still unstated. Check these with organizers. (Repo, PPT and deployed URL are confirmed as required.)

## 2. What we learned from you

- **Idea:** specific. It's the refined concept doc, plus a new **Product Launch & Market Simulation Engine** that compares price, feature and launch alternatives and gives best, expected and worst cases with stated assumptions.
- **Hard requirement:** **automated competitor discovery.** The user only enters their company, product, service or idea, and the system finds relevant competitors in the Indian market (including foreign companies serving India) using permitted sources. Nobody types in competitor names.
- **Scope decision:** build the core loop for real and keep the extras seeded, with discovery made real. The flow is profile → discovery → collection → extraction → change detection → history → comparison → reports → alerts. Review intelligence, inspiration companies, add-ons and advanced simulation stay lightweight.
- **Domain:** industry-agnostic, with criteria that adapt to **product vs service** offerings. The initial focus is businesses operating in India.
- **Demo:** several business profiles on one platform: a cloud deployment startup, a quick-commerce player, a shoe brand, and a quantum-computing startup idea that the platform should flag as high-risk.
- **Team, time and LLM:** one person plus an AI agent. There's an initial 3-hour block, then work continues until about 21:00. LLMs must be **free or local only**.
- **Labelling rule (yours, and correct):** any seeded or simulated data is visibly marked as demo data and never shown as live intelligence.

## 3. Landscape

### GitHub / open source (10 reviewed)

| Repo | Stars / active | What it does | Standout | Gaps / issues |
|---|---|---|---|---|
| [dgtlmoon/changedetection.io](https://github.com/dgtlmoon/changedetection.io) | 35.2k, pushed today, 402 open issues | Self-hosted web page change detection and alerts | Mature general-purpose diffing, filters and notifications; LiteLLM is a dependency | Not competitor-aware: no entity model, comparison or reports |
| [huginn/huginn](https://github.com/huginn/huginn) | 50.1k, active | General "agents that monitor and act" platform | Very flexible monitoring and actions | Generic, with no CI domain logic |
| [Keerthivasan-Venkitajalam/competitor-monitor](https://github.com/Keerthivasan-Venkitajalam/competitor-monitor) | 3, last push Feb 2026 | Playwright text extraction, embedding similarity, flags "strategic shifts" | Semantic diff with local models (sentence-transformers, optional Ollama) | Small personal project with no comparison or history UI evidence |
| [erenmyeager15/competitor-change-intelligence-monitor](https://github.com/erenmyeager15/competitor-change-intelligence-monitor) | 0, Oct 2026 | Authorized public-page monitoring with evidence, severity, confidence and digests (Apify actor) | Requires confirming you're authorized for each target; trusted baselines | Brand new, unproven |
| [Mastra "Competitor Monitor with Jev"](https://mastra.ai/templates/competitor-monitor-jev) | template | Watches pricing, changelog and docs pages; classifies changes; LLM explains | **Closest prior art:** before/after excerpts, source URLs, ignore selectors, ignore/record/review/alert policy, SQLite history | Up to 20 sites, English only, you supply URLs; no discovery, comparison matrix or India focus |
| [Union.ai competitive intelligence agent](https://www.union.ai/docs/v2/union/tutorials/agents/competitive-intelligence-agent/page.md) | tutorial | Fans out over competitors, pulls source-cited search results, extracts structured deltas (pricing, funding) | Structured delta extraction | Search-result based, not page history |
| vahabcore/competitor-intelligence-agent | *seen only via a mirror (unverified)* | LangGraph + FastAPI + React, researcher, analyst, strategist and critic nodes, Ollama-capable | Critic loop for report quality | One-shot research, no monitoring |
| [scrapegraphai/scrapehubai](https://github.com/scrapegraphai/scrapehubai) | not checked | LLM scraping plus LangGraph for sales and market research | LLM-driven extraction | CI is a minor use case |
| guia-matthieu/clawfu-skills `competitor-monitor` | not checked | requests + BS4 CLI with `watch`, `diff` and `pricing` commands against a cached baseline | Dead-simple baseline diff | CLI only |
| triposat/competitor-price-tracker ([MCP listing](https://glama.ai/mcp/servers/triposat/competitor-price-tracker)) | not checked | Matches products by SKU, alerts when a competitor newly undercuts and is in stock, keeps CSV snapshot history via GitHub Actions | Deduplicated "newly undercut" alert logic | E-commerce SKU only |

### Past winners (0 confirmed, 5 unverified)

No winning project on this PS or a close match could be confirmed on any page I opened. The pool is **thin**.

| Project | Event, prize | What it does | Demo moment | Why it matters (inference) |
|---|---|---|---|---|
| CompetAI ([Devpost](https://devpost.com/software/competeai)) | **unverified** (page returned 403; no prize seen) | Automated competitor research and AI SWOT (Next.js, GPT-4) | — | One-shot SWOT reports are the obvious hackathon build, so expect other teams to do it |
| MarketPulse (lablab.ai profile) | **unverified** (listed as a submission) | 4 agents: Scout finds competitors, Research collects, Synthesizer reports, Voice agent answers questions | — | Discovery plus reports is being built; monitoring and history are not |
| Lootle ([Linode story](https://www.linode.com/content/aashish-panthi-lootle/)) | **unverified**: the author won Hashnode × Linode's grand prize, but the snippet is unclear whether Lootle was the winning entry | Amazon/Flipkart price tracking with email alerts | Price drop → email | Price tracking with alerts is a familiar demo, so it alone won't stand out |
| Product Price Tracker ([HackQuest](https://hackquest.io/projects/Product-Price-Tracker)) | **unverified** | Scraping, price history, Telegram/email alerts, dashboard | — | Same: table stakes |
| price tracker ([Devpost](https://devpost.com/software/price-tracker-5xpd9q)) | **unverified** | Amazon link plus budget, email when the price drops | — | Same |

### Market products (10 reviewed)

| Product | For whom | Key features | Standout | Top complaints |
|---|---|---|---|---|
| Crayon | Enterprise PMM and sales | Intel feed, battlecards, newsletters | Battlecards | Weak reporting customization, CRM integration issues, no self-serve tier; ~$20-40K/yr per a [Vendr-citing blog](https://dupple.com/learn/best-ai-competitive-intelligence-tools) (figures conflict); a Gartner review says retrieval is "inefficient and slow" |
| Klue | Enterprise sales enablement | Thousands of sources → self-updating battlecards | Auto-updating battlecards | Feed items that "don't apply to our goals" ([G2](https://g2.com/products/klue/reviews_and_filters?page=9)); labour-intensive setup |
| Kompyte | Mid-market | AI monitoring, win/loss, battlecards | Cheaper entry (one blog lists ~$300/yr) | Limited data |
| [Visualping](https://www.g2.com/products/visualping) | Anyone tracking pages | Visual/text page diffs, AI "important change" filter, AI summaries | Accuracy and easy setup | **False alerts are the top G2 con (30 mentions)**: layout tweaks trigger alarms, and ignore-area filters are fiddly |
| Competely | Founders, PMs | Enter product URL → AI discovers competitors (accept/replace), compares marketing, product, pricing, audience, sentiment and SWOT, re-analyzes, **source URL per data point** | Discovery plus dynamic metrics in about 2 minutes, from ~$9/mo | Few independent reviews (0 on G2); depth depends on available public data |
| [Prisync](https://www.softwareadvice.com/bi/prisync-profile/) | E-commerce | Daily price and stock tracking, alerts, reports | Repricing focus | Slow setup; delayed or wrong price updates |
| DataWeave | Retail and CPG (Bengaluru R&D) | Digital-shelf KPIs, price monitoring, **dynamic pricing recommendations**, assortment gaps | Retail-scale product matching with human validation | Enterprise only |
| Apify actors (Competitor Change Intelligence Monitor, SiteWatch Pro) | Developers | Pay-per-run page diffs and webhooks | Cheap and scriptable | No UI or comparison |
| Competiflow | SaaS | Extracts plan names and prices and diffs **fields instead of raw text** | Avoids layout false positives | Little public info |
| ZenRows / PageCrawl guides | Developers | Scraping infrastructure and how-tos | — | — |

**Takeaways (inference, from 20 items plus 5 unverified projects):**

1. **Noise is the universal pain.** Visualping's top con is false alerts, Klue users triage irrelevant items, and the fixes are "AI importance filters" or field-level diffing. Nobody we saw *shows* the user what was ignored and why. A visible noise ledger is cheap to build and directly scores "change-detection effectiveness".
2. **Evidence links go stale.** Competely links each data point to a source URL, but a live URL shows *today's* page. A claim like "price was ₹999 on 1 Oct" linked to a page that now says ₹799 is unverifiable. **Frozen evidence** (a stored snapshot plus a Wayback permalink, with the excerpt highlighted) did not appear in any product we read about. This scores "evidence accuracy" and "historical reliability".
3. **Automated discovery is becoming table stakes** among AI CI tools (Competely, MarketPulse). It's required for your vision, but it won't wow judges by itself.
4. **Nobody connects "competitor changed" to "so what should I do".** Enterprise tools turn changes into sales battlecards, e-commerce tools into repricing, and DataWeave into pricing recommendations for retailers. For a founder planning a launch, the link from a detected change to a revised launch scenario is a **gap**.
5. **India is under-served at the founder/SMB tier.** The leaders are US-enterprise-priced. INR-aware extraction and "operates in India" filtering didn't appear in anything we reviewed.
6. **Few hackathon precedents** (0 confirmed winners). Judges likely haven't seen many monitoring-and-history builds. The expected competitor-team build is a one-shot SWOT report.

## 4. Feature landscape

| Feature | Seen in | Class | Judging criterion it serves |
|---|---|---|---|
| Page fetch + snapshot storage | all | Table stakes | Data accuracy |
| Text/visual diff | Visualping, changedetection.io | Table stakes | Change detection |
| Email/in-app alerts | all | Table stakes | Alerts |
| Price tracking + price history chart | Prisync, Lootle, trackers | Overdone (in hackathons) | History |
| One-shot AI SWOT / competitor report | CompetAI, Competely, many tutorials | Overdone | Reports |
| Battlecards | Crayon, Klue, Kompyte | Table stakes (enterprise) | Reports |
| Automated competitor discovery | Competely, MarketPulse | Table stakes (AI tools) | Usability |
| Structured field diff (plan, price, feature) | Competiflow, Union.ai, Mastra | Differentiator | Change detection, data accuracy |
| Ignore/record/review/alert policy | Mastra template | Differentiator | Alerts |
| Before/after excerpts in reports | Mastra template | Differentiator | Evidence |
| **Visible noise ledger** ("13 changes ignored, here's why") | not seen | **Gap** | Change detection, alerts |
| **Frozen evidence receipts** (snapshot + Wayback permalink + highlighted span) | not seen | **Gap** | Evidence, history |
| **Observed-at vs published-at distinction** | not seen | **Gap** | History |
| Wayback backfill of real history on day one | not seen in products | **Gap** | History, data accuracy |
| Product-vs-service adaptive comparison criteria | Competely ("dynamic metrics", partly) | Differentiator | Comparison |
| Missing-data-aware comparison (no penalty for unknowns) | not seen | Gap | Comparison |
| India market filter (INR, India presence signals) | not seen | Gap | Data accuracy, usability |
| **Change → launch-scenario re-plan** | not seen (DataWeave does retail repricing) | **Gap** | Alerts/reports usefulness |
| Launch simulator (price/feature scenarios) | not seen in CI tools | Gap (but unscored) | Usability, reports |
| Review sentiment / themes | Competely, DataWeave | Table stakes | Comparison |
| Inspiration companies / add-on suggestions | not seen | Gap (but unscored, needs data) | — |

## 5. The winning feature

**"Change Receipt → Launch Re-plan"**: one detection run turns a competitor move into verifiable proof and then into a revised plan for *your* launch.

- **What it is:** each monitoring run computes field-level diffs, writes most of them to a visible **noise ledger** (navigation, banners, formatting, reordering), and turns only the meaningful ones into **Change Receipts**. A receipt holds:
  - the previous and current value
  - the % change and its priority
  - the observed-at timestamp, and the published-at date if known
  - a frozen snapshot with the exact excerpt highlighted
  - a Wayback permalink where one is available

  Each receipt then **re-runs the user's launch simulator automatically**, so the alert says what changed, why it matters to you, and how your best, expected and worst-case scenarios moved. Every simulator assumption cites the receipt it came from.
- **60-second demo moment:**
  1. The cloud-startup profile shows auto-discovered competitors, with a "planned launch at ₹999/mo, expected case X" scenario.
  2. You flip the labelled **DEMO** toggle that cuts mock competitor *"NimbusDeploy (demo)"*'s Pro plan from ₹1,499 to ₹899 and adds a feature.
  3. You click **Run monitor**. The ledger shows *"17 page diffs: 15 ignored (nav, footer, banner, CSS-only), 2 meaningful"*.
  4. A high-priority alert appears: *"NimbusDeploy Pro −40% · now undercuts your planned price · your expected-case adoption ↓, recommended launch price ₹999 → ₹849"*.
  5. You click the claim in the report, and the frozen before/after snapshot opens with the price highlighted and both observation timestamps shown.
- **Why it wins:**
  - It hits **five of seven criteria** in one moment: change detection (the noise ledger), history (receipts with timestamps), evidence (frozen snapshots), alerts (prioritized and personal) and reports (cited claims).
  - The comparables lack it. Visualping's top complaint is false alerts ([G2](https://www.g2.com/products/visualping)). Competely links to live URLs, not frozen evidence. The Mastra template has excerpts but no discovery, comparison or decision link. No CI tool reviewed connects a change to a launch scenario.
  - It also makes your simulator idea *load-bearing* in the PS demo instead of a separate tab.
- **Sponsor tech use:** n/a. The free LLM (Groq or Gemini free tier, or local Ollama) handles feature and positioning extraction and the alert's one-line explanation. Every response is cached by input hash, so the demo replays deterministically and works offline.
- **One-hour feasibility test (do first):**
  1. Serve two versions of a mock pricing page (v1 and v2, where v2 changes the price, adds a feature, and also changes the nav, banner and CSS).
  2. Fetch v1, extract `{plan, price_inr, period, features[]}` with selectors plus a ₹ regex, and store the snapshot with its hash and timestamp.
  3. Fetch v2 and diff. **Pass:** only the price and feature changes are reported, the nav, banner and CSS changes land in the ledger, and the receipt links to the stored v1 and v2 snapshots with the span highlighted.
- **Runner-up candidate:** **Wayback backfill** (real 12-24-month price history for real companies on day one). It's strong on "historical reliability" and on real data, and I confirmed the [CDX API](https://web.archive.org/cdx/search/cdx?url=vercel.com/pricing&output=json&limit=5) works keylessly and shows real digest changes on vercel.com/pricing through 2024. It lost because it adds no live "detect a change now" moment, which is the PS's required demo. It's included as a **Should**.

## 6. Prototype feature priorities

Effort here is for one person plus an AI coding agent: **S** < 30 min, **M** 30-75 min, **L** > 75 min.

| Tier | Feature | Why this tier | Effort | Build real / thin / fake |
|---|---|---|---|---|
| **Must** | Business / Idea Card (product vs service toggle, category, target market, planned price) | Drives discovery, criteria and simulator | S | Real, thin form, hardcoded single user |
| **Must** | **Automated competitor discovery (India)** | Your hard requirement. Pipeline: free LLM proposes candidates from the card (labelled *AI-suggested*) → verify each (homepage reachable, robots.txt allows, India signals: ₹/INR, .in, "India" region or address) → rank by embedding similarity to the card → split into *comparable* vs *inspiration* → locate pricing and features pages (/pricing, sitemap) | M-L | Real, **plus a cached, dated discovery run per demo profile as fallback** |
| **Must** | Collector: robots check, polite rate limit, snapshot store (raw HTML, text, hash, `observed_at`, status) | PS core; failed fetch ≠ change | S | Real |
| **Must** | Structured extraction (prices via selectors and ₹/$ regex; features and positioning via free LLM, cached) | Data accuracy | M | Real |
| **Must** | Change detection + **noise ledger** (field diff for prices and plans; normalized-text diff for features; ignore rules for nav, footer, banner and CSS) | Winning feature | M | Real |
| **Must** | **Change Receipts** + timestamped history timeline (observed vs published dates) | Winning feature, history | S-M | Real |
| **Must** | Comparison matrix with product/service criteria templates, user weights, "unknown" cells shown and never penalized | PS core | S-M | Real |
| **Must** | Evidence-linked report (every claim → receipt → highlighted snapshot; facts vs AI suggestions visually separated) | PS core, evidence | M | Real; Markdown or HTML on screen |
| **Must** | In-app alerts: priority score (magnitude × relevance to your card × confirmed), dedupe | PS core | S | Real |
| **Must** | Mock competitor pages + **DEMO change toggle** (fictional names, banner "Demo data") | The PS demo requires a simulated change | S | Real; fake by design, clearly labelled |
| **Must** | **Deployed walking skeleton first** (frontend + backend + Postgres on public URLs, GitHub repo pushed, auto-deploy on push), then redeploy at every checkpoint | Deployed URL and repo are required; deploying last is the classic hackathon failure | S-M | Real |
| **Must** | PPT (problem, demo screenshots, architecture, detection method, evidence model, simulator assumptions) + README (setup, data sources, detection method, demo-data labelling) | Required deliverables; README doubles as the technical write-up | S | Real; written in the freeze window |
| **Must** | **Basic launch simulator**: 3 price options × best/expected/worst, transparent heuristic (price index vs competitor median, feature coverage, editable elasticity and segment-size assumptions), re-runs on each receipt | Winning feature, your requirement | M | Real, thin; "scenario model, not a forecast" |
| **Should** | Wayback backfill for real competitors (real price history chart) | Runner-up; real-data credibility | M | Real |
| **Should** | Multi-profile switcher: cloud startup (live), quick commerce + shoes (cached discovery and seeded monitoring), quantum idea | Your demo story | S | Thin: profiles 2-4 cached, labelled with run date |
| **Should** | **Viability risk flags** (quantum idea): evidence-cited flags such as few verified India-market competitors or customers, capital intensity, incumbent density; the simulator shows "no scenario breaks even within 36 months *under these assumptions*" | Your demo story, told honestly (see §10) | S-M | Thin |
| **Should** | Review themes (lightweight, from permitted sources or seeded) | Your should-have | S | Seeded, labelled |
| **Should** | Email alert path | A second notification channel | S | Real |
| **Could** | Scheduled monitoring (APScheduler) | The button is enough for a demo | S | Real |
| **Could** | Inspiration-company feature-gap suggestions | Unscored; needs good data | M | Seeded |
| **Could** | Launch-window suggestion (competitor launch cadence from history) | Simulator depth | S | Thin |
| **Could** | Embedding-based semantic diff for positioning copy | Detection depth | M | Real |
| **Could** | Playwright rendering for JS pages | Only if a demo target needs it | M | Real |
| **Won't** | Auth/accounts, Celery, Common Crawl, Amazon/Flipkart scraping, market-cap/revenue scale comparisons, add-on/co-purchase engine, Slack | See cut list | — | — |

**Effort check:** with deploy, repo and PPT now required, Must ≈ 4.5 h of ~4.5 h available. That's **double the ~50% target**, so the Should tier is realistically only partly reachable. Order of sacrifice if behind: email alert → review themes → Wayback backfill → extra profiles (keep quantum last, it's your closer). Checkpoints, each ending **deployed** on the public URL:

- **By ~16:30:** walking skeleton live: repo on GitHub, frontend + backend + DB deployed, one mock pricing page fetched and shown on the public URL.
- **By ~18:00:** core loop on mock pages with a seeded competitor list (card → collect → extract → diff + ledger → receipts → report → alert), deployed. This alone satisfies the PS demo.
- **By ~19:30:** automated discovery replaces the seeded list (cached fallback in place), plus comparison matrix and simulator, deployed.
- **By ~20:15:** whatever Should items fit (quantum risk flags first).
- **20:15-21:00:** feature freeze. Smoke-test the public URL from a phone, write the README, build the PPT, rehearse the golden path twice.

If a checkpoint slips by more than 30 minutes, drop the next tier's lowest item rather than squeezing the freeze.

## 7. Golden-path demo

1. **Pain (15 s):** "A founder launching a cloud deployment service in India can't watch 8 competitors' pricing pages every week, and today's tools flood them with false alerts."
2. **Profile → discovery:** enter the cloud startup's card (service, ₹999 planned Pro price). Competitors are auto-discovered and verified with India signals, split into comparable vs inspiration, each with its source pages, AI-suggested ones marked as such.
3. **Baseline:** the first monitoring run produces the comparison matrix (service criteria, weights, unknowns shown) and a launch simulator scenario at ₹999.
4. **Simulated change:** flip the labelled **DEMO** toggle on *NimbusDeploy (demo)* → **Run monitor** → noise ledger: 15 ignored, 2 meaningful.
5. **Alert + re-plan:** the high-priority alert shows the price −40% and the new feature, and the simulator's recommended price and expected case shift.
6. **Proof:** open the report, click a claim, and the frozen before/after snapshot opens with the excerpt highlighted and observed-at timestamps shown. AI suggestions are visually separate from facts.
7. **Closer (Should):** switch to the quantum-idea profile. The risk flags and "no scenario breaks even within 36 months under these assumptions" show the same engine supports a founder's go/no-go decision.

## 8. Differentiation

"Not seen" means not found in the pages reviewed, not a confirmed absence.

| Capability | Us | Visualping | Competely | Crayon / Klue | Mastra template |
|---|---|---|---|---|---|
| Structured price/plan/feature diff | ✅ | not seen (page diff + AI filter) | partial (re-analysis) | not seen | ✅ classified |
| **Visible noise ledger** | ✅ | ❌ (false alerts = #1 con) | not seen | not seen | partial (ignore policy, not shown) |
| **Frozen evidence + highlighted excerpt** | ✅ | screenshots | live source URLs | not seen | before/after excerpts |
| Observed-at vs published-at | ✅ | not seen | not seen | not seen | not seen |
| Automated discovery | ✅ India-filtered | ❌ | ✅ | not seen | ❌ (you supply URLs) |
| Product/service adaptive criteria | ✅ | ❌ | ✅ "dynamic metrics" | not seen | ❌ |
| **Change → launch scenario re-plan** | ✅ | ❌ | not seen | ❌ (battlecards) | ❌ |
| India / INR focus | ✅ | ❌ | not seen | ❌ | ❌ |
| Price point | free/hackathon | from ~$14/mo | from ~$9/mo | ~$20-40K/yr (unverified) | open template |

## 9. Cut list

- **Login/accounts:** a hardcoded user, because no judging criterion rewards auth.
- **Amazon/Flipkart/Swiggy scraping:** their ToS restrict scraping, and that conflicts with the PS's "permitted sources" rule. Quick commerce and shoe profiles use official brand pages and cached or seeded data, labelled.
- **Market-cap/revenue/funding comparisons:** unreliable for private Indian firms, and they risk fabricated numbers. Show "unknown" instead.
- **Add-on/co-purchase engine:** needs co-purchase data you don't have; "frequently bought together" isn't proof (your own doc says so).
- **Celery/microservices:** a modular monolith is enough.
- **Common Crawl:** heavy to query in the time available. Wayback covers history.
- **One-shot SWOT reports:** the overdone hackathon build. Ours is about change over time.
- **"Will fail in 2-3 years" predictions:** replaced by assumption-bound scenarios (see §10).

## 10. Risks and open questions

| Risk / question | Impact | Mitigation or owner |
|---|---|---|
| Must tier ≈ 4 h vs ~4.5 h left | Core demo unfinished | Checkpoints in §6; core loop on seeded competitors first; discovery second |
| Free LLM rate limits, latency or outages mid-demo | Demo stalls | Cache every LLM call by input hash; rule-based price extraction never needs the LLM; local Ollama fallback |
| Local Ollama can't serve a deployed backend (now certain, since a deployed URL is required) | Deployed app has no LLM | A free hosted tier (Groq or Gemini; check current free limits) is required for the deployed app; Ollama for local dev only; LLM-response cache stored in the DB so the deployed demo replays |
| Free hosting quirks: ephemeral disk, cold starts (e.g. Render free tier sleeps) | Snapshots lost, or first request takes ~30-60 s on stage | Store snapshots in Postgres, not on disk; open the URL a few minutes before demoing to warm it |
| Discovery returns irrelevant or non-Indian companies | Bad first impression | Verify step plus similarity threshold; cached, dated verified run per demo profile; let the user deselect (not add) |
| Discovery needs web search, and free search APIs have quotas and ToS | Discovery breaks | Free-tier search API (e.g., Tavily or Brave; check limits), LLM candidate generation, Wikidata (CC0) for company facts; no scraping of search engines |
| Real competitor pages are JS-rendered or block bots | Extraction fails | Live demo change runs on mock pages; real companies use static pages or Wayback; failed fetch recorded as `status=failed`, never as a change |
| **"Quantum startup will fail in 2-3 years"** | An unsupported prediction directly contradicts the "evidence accuracy" criterion and your own doc ("does not guarantee success") | Show it as **risk flags + scenario outcomes under stated assumptions**: "no break-even within 36 months in any scenario *given these inputs*", with each flag cited |
| Simulator looks like made-up numbers | Judges distrust it | Assumptions panel always visible and editable; inputs cite receipts; label "scenario model, not a forecast" |
| Mock competitor named after a real company | Misleading | Fictional names only (*NimbusDeploy (demo)*), with a demo banner |
| Official submission time unknown | Wrong freeze time | **You:** ask organizers now |

## Source log

- https://mastra.ai/templates/competitor-monitor-jev — used (fetched)
- https://api.github.com/repos/dgtlmoon/changedetection.io — used (stars, activity, issues)
- https://api.github.com/repos/huginn/huginn — used
- https://api.github.com/repos/Keerthivasan-Venkitajalam/competitor-monitor — used
- https://api.github.com/repos/erenmyeager15/competitor-change-intelligence-monitor — used
- https://web.archive.org/cdx/search/cdx?url=vercel.com/pricing — used (API works, real snapshots 2024)
- https://www.union.ai/docs/v2/union/tutorials/agents/competitive-intelligence-agent/page.md — search snippet only
- vahabcore/competitor-intelligence-agent — mirror snippet only (unverified)
- https://github.com/scrapegraphai/scrapehubai — search snippet only
- https://glama.ai/mcp/servers/triposat/competitor-price-tracker — search snippet only
- https://devpost.com/software/competeai — **failed (403)**; prize status unknown
- lablab.ai MarketPulse profile — search snippet only; no prize
- https://www.linode.com/content/aashish-panthi-lootle/ — search snippet only; winning entry unclear
- https://hackquest.io/projects/Product-Price-Tracker — search snippet only
- https://devpost.com/software/price-tracker-5xpd9q — search snippet only
- https://mindsdb.com/blog/agents-in-action-mindsdb-hackathon-recap — snippet; winner unrelated (procurement agent)
- https://www.g2.com/products/visualping (+ review pages) — snippets; false-alert counts
- https://dupple.com/learn/best-ai-competitive-intelligence-tools — snippet; Crayon/Klue pricing (conflicting sources)
- https://g2.com/products/klue/reviews_and_filters?page=9 — snippet
- https://www.gartner.com/reviews/market/competitive-and-market-intelligence-tools/vendor/crayon — snippet
- https://subscribed.fyi/blog/competely-ai-powered-competitive-analysis-in-minutes-for-your-product/ and https://hunted.space/product/competely-ai-agent — snippets (vendor-sourced)
- https://www.softwareadvice.com/bi/prisync-profile/, https://www.getapp.com/marketing-software/a/prisync/ — snippets
- https://us.fitgap.com/products/006936/dataweave, https://www.cbinsights.com/company/dataweave — snippets (conflicting company details)
- https://apify.com/fascinating_lentil/competitor-change-intelligence-monitor — snippet
- Devfolio / Unstop winner searches — nothing relevant found

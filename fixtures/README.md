# Fixtures

Real data samples that the schemas, parsers and tests are based on. They were fetched on **2026-10-23** around 16:20 IST from a Windows laptop in India, using `curl -L` with the User-Agent `Mozilla/5.0 (compatible; RivalLensResearch/0.1; hackathon prototype)`. No redactions were needed because these are public pages.

| Folder | Source | Files | How fetched |
|---|---|---|---|
| `pricing-pages/` | Official pricing pages: render.com, railway.com, netlify.com, vercel.com, e2enetworks.com (Indian provider), digitalocean.com | `<name>-pricing.html` (raw HTML, 220 KB–1.2 MB) | `GET https://<site>/pricing`, all returned HTTP 200 |
| `robots/` | robots.txt of the same 6 hosts | `<name>-robots.txt` | `GET https://<site>/robots.txt` |
| `sample-companies/` | **Synthetic**, not fetched: two fictional businesses for manual exploration (onboarding entries, sales and review CSVs) | `README.md`, `a-ironleaf-*.csv`, `b-homenest-*.csv` | Hand-written test data; see its README |
| `wayback-cdx/` | Internet Archive CDX API | `render-pricing-cdx.json`, `e2enetworks-pricing-cdx.json` | `GET https://web.archive.org/cdx/search/cdx?url=<url>&output=json&from=2025&filter=statuscode:200&collapse=digest&limit=8` |

**Not yet captured (specs marked doc-based and unverified):**
- `llm/` (Gemini and Groq responses)
- `tavily/`
- `resend/`
- quick-commerce and shoe-brand pages

Record the LLM and Tavily responses with `LLM_MODE=record` on the first live run.

## Doc-vs-reality surprises
- **All 6 pricing pages are server-rendered.** Prices appear in the static HTML's visible text (12–24 KB of text), so a headless browser isn't needed.
- **E2E Networks served USD** (`$7.99/hr` for GPUs) to this fetch from India; `₹` appears only in a few places. Currency must be stored as observed.
- **Non-plan numbers live on pricing pages:** `$829,000` (DigitalOcean) and `$1,000–$10,000` credit tiers (Railway). Price extraction needs section scoping and plausibility checks.
- **Wayback digests change on almost every capture** of render.com/pricing (3 different digests in the first two weeks of January 2025). Raw-hash diffing would flag noise.
- **No robots.txt disallows `/pricing`**; they disallow app and auth paths (`/dashboard`, `/api/`, `/login`, `/new`).

## Usage in tests
Integration tests serve these files from a local HTTP server (pytest fixture), so tests never hit the real sites. Note that the pages will change over time. These files are a frozen baseline, not current truth.

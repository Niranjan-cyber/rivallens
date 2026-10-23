# Demo businesses: data sources and licences

The four demo sign-ins are fictional businesses. Their inputs are licensed datasets and public pages; every number on their dashboards is computed by the same pipeline a real user gets (`api/scripts/build_demo.py` calls the live API). Each is labelled "Demo business, modelled on …" in the app.

| Business | Its own data | Licence | Market data (fetched live, robots.txt respected) |
|---|---|---|---|
| Stride & Co. (running shoes, Pune) | Order rhythm of **UCI Online Retail II** (Chen 2012, doi:10.24432/C5CG6D); costs from **Campus Activewear FY26** reported gross margin 53.5%. See `stride/README.md` | CC BY 4.0; public results | Nivia, Neemans, Campus home pages; brand product pages (JSON-LD) for comparables; two fictional shoe brands hosted by us for "Simulate a competitor move" |
| Kesar Bakehouse (bakery café, Pune) | **The Bread Basket** transactions (OpenML 43422), priced from **Theobroma's public online menu**; **Amazon Fine Food Reviews** (SNAP). See `bakery/README.md` | CC0; public page; CC0 (HF mirror Apache-2.0) | Theobroma home page, bakery product pages |
| StackNest (app hosting SaaS, Pune) | None: Money and Customers wait for the business's own uploads | — | E2E Networks, Render and Railway pricing pages; three fictional hosts for "Simulate a competitor move" |
| QuickKart (quick commerce, Bengaluru) | None | — | Eternal (Blinkit) and Swiggy (Instamart) figures from filings and news, each with its quote and link |

Fictional competitors (NimbusDeploy, KiteHost, Orbitly Cloud, ZephyrPace, Monsoon Miles) are marked "(demo)" everywhere and their pages carry a "Demo data: fictional company" ribbon.

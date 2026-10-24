# Sample companies (synthetic test data)

Two **fictional** businesses for exploring the app by hand through the real sign-up and onboarding flow. Every name, number and review here is made up. Nothing is seeded. You type the entries in yourself and upload the files from the Finance and Customers screens.

Both sell kitchenware in Coimbatore, and both have the same fields filled in. They differ in the quality of the business, not in missing data:

- **A, Ironleaf Kitchen:** strong, differentiated, with traction.
- **B, HomeNest Kitchen Store:** ordinary, generic, little to set it apart.

Leave **Website** and **Social handles** blank for both. A made-up domain could belong to a real stranger, and the app would try to fetch it.

The app has no fields for founding story, team, business model or traction. Those go into the one-line description, which saves the full text, though only about the first 500 characters reach the AI drafter. Traction also shows in funding stage and monthly revenue.

## Onboarding entries (`/app/new`, or the header switcher → Add a business)

| Field | A: Ironleaf Kitchen | B: HomeNest Kitchen Store |
|---|---|---|
| Business name | Ironleaf Kitchen | HomeNest Kitchen Store |
| What kind of business is it? | D2C brand | Local business |
| Selling? | Already selling | Already selling |
| City | Coimbatore | Coimbatore |
| What you do, in one line | Pre-seasoned cast-iron cookware made for Indian cooking (dosa tawas, kadhais, appam pans) that is lighter than traditional cast iron and ships ready to use. Founded in 2024 by a third-generation foundry engineer and a former quick-commerce category manager; 4,200 orders and a 31% repeat rate in 14 months, now stocked by 2 regional kitchenware chains. | We sell kitchen items and cookware for homes at good prices, in our shop and online. Started in 2023 by the owner, who wanted to run their own retail business; we stock popular products from different suppliers and are planning to add more items. |
| Main products | cast iron dosa tawa, cast iron kadhai, cast iron appam pan | non-stick tawa, pressure cooker, steel kadhai |
| Funding stage | Angel | Bootstrapped |
| Monthly revenue | ₹10 lakh–1 crore | ₹1–10 lakh |
| Who are your customers? | Health-conscious home cooks aged 28–45 in South Indian metros who are replacing non-stick pans over coating safety concerns | Families and anyone who cooks at home |

**Business card review** (correct any AI-drafted field to these values):

| Field | A | B |
|---|---|---|
| Industry | Kitchenware | Kitchenware |
| Cities | Coimbatore, Bengaluru, Chennai, Hyderabad | Coimbatore |
| You sell a | product | product |
| Category | Cast iron cookware | Kitchen products |
| Key attributes | pre-seasoned, 30% lighter than standard cast iron, induction compatible, no chemical coating, 10-year warranty | good quality, affordable prices, wide range |
| Price | 1899 INR one-time | 899 INR one-time |

**Product prices** (Getting started, "Add the price of …"):
- A: dosa tawa 1899, kadhai 2499, appam pan 1499
- B: non-stick tawa 899, pressure cooker 1799, steel kadhai 749

## Files to upload

| File | Screen | Cash in bank | What to expect |
|---|---|---|---|
| `a-ironleaf-sales-costs.csv` | Finance → Upload an export | 4800000 | Revenue growing to about ₹16.4 lakh in Sep, margin about −5%, burn about ₹1 lakh a month, runway about 45 months; includes a ₹60 lakh angel round |
| `a-ironleaf-reviews.csv` | Customers → Upload | | 12 reviews: praise (weight, seasoning), complaints (rust, dented box), requests (12-inch tawa, glass lid, grill pan, handle sleeve) |
| `b-homenest-sales-costs.csv` | Finance → Upload an export | 300000 | Flat at about ₹3 lakh a month, margin about +10%, not burning |
| `b-homenest-reviews.csv` | Customers → Upload | | 12 short, generic reviews: few clear themes (late delivery, peeling coating, loose lid) |

Columns in the sales files: `date, type (sale/expense/funding), amount, product, description`. Columns in the review files: `date, rating, text, author, product`.

## What to compare

Both companies share one account's competitor-search limit of 5 a day, so use one search each. Then compare:

- product categories
- like-for-like matches and price position
- suggested segment
- competitor relevance
- Finance margin against the benchmark, plus runway
- Customers themes
- what the product simulator's input chips cite
- Overview findings
- the Report

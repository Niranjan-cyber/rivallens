// Fictional competitors for the Demo Lab (specs §1 C-02). Scenario versions stack on top of v1.
type Plan = { name: string; price: number | null; features: string[] };
type Site = { name: string; tagline: string; newTagline: string; nav: string[]; banner: string; plans: Plan[]; shop?: Shop };
// Footwear mocks (B14j) sell shoes, not plans: their own copy, a per-pair price and a different "new feature".
type Shop = { blurb: string; title: string; note: string; unit: string; newFeature: string; faq: [string, string][] };

const SHOE_FAQ: [string, string][] = [
  ["What if the size is wrong?", "Free size exchange within 30 days. Returns are picked up from your door."],
  ["Do you ship across India?", "Yes, to 19,000+ pin codes. Cash on delivery available. Prices include GST."],
];

export const mockSites: Record<string, Site> = {
  zephyrpace: {
    name: "ZephyrPace",
    tagline: "Running shoes built for Indian roads.",
    newTagline: "India's fastest-growing running brand.",
    nav: ["Men", "Women", "Running", "Stores", "Cart"],
    banner: "Free shipping on all orders",
    plans: [
      { name: "Zephyr Daily", price: 2299, features: ["EVA cushioning", "Breathable mesh upper", "Rubber outsole"] },
      { name: "Zephyr Tempo", price: 3499, features: ["Responsive foam midsole", "Engineered mesh", "Reflective details", "Wide fit available"] },
      { name: "Zephyr Elite", price: 6999, features: ["Carbon fibre plate", "Supercritical foam", "Race-day upper"] },
    ],
    shop: { blurb: "Designed in Bengaluru, tested on Indian roads.", title: "Running range", note: "Prices per pair, GST included.",
      unit: " per pair", newFeature: "Monsoon grip outsole", faq: SHOE_FAQ },
  },
  monsoonmiles: {
    name: "Monsoon Miles",
    tagline: "Everyday running shoes that grip in the rain.",
    newTagline: "Performance running for every Indian runner.",
    nav: ["Shop", "Running", "Walking", "Our story", "Cart"],
    banner: "Use code RUN10 for 10% off your first pair",
    plans: [
      { name: "Drizzle", price: 1799, features: ["Lightweight foam", "Knit upper", "Grippy outsole"] },
      { name: "Downpour", price: 2999, features: ["Dual-density cushioning", "Water-resistant mesh", "Reflective heel"] },
      { name: "Cloudburst", price: 4499, features: ["Max cushioning", "Stability frame", "Rocker sole"] },
    ],
    shop: { blurb: "Made for wet roads, from Mumbai.", title: "Shoes", note: "Prices per pair, GST included.",
      unit: " per pair", newFeature: "Half sizes", faq: SHOE_FAQ },
  },
  nimbusdeploy: {
    name: "NimbusDeploy",
    tagline: "Ship Node, Python and Go apps from Git in minutes.",
    newTagline: "The AI-native cloud for Indian startups.",
    nav: ["Product", "Pricing", "Docs", "Blog", "Log in"],
    banner: "Diwali offer: 2 months free on annual plans",
    plans: [
      { name: "Starter", price: 499, features: ["1 app", "512 MB RAM", "Free SSL", "Community support"] },
      { name: "Pro", price: 1499, features: ["10 apps", "2 GB RAM", "Autoscaling", "Preview environments", "Email support"] },
      { name: "Business", price: 3999, features: ["Unlimited apps", "8 GB RAM", "Private networking", "SSO", "Priority support"] },
    ],
  },
  kitehost: {
    name: "KiteHost",
    tagline: "Fast, friendly hosting for Indian SaaS teams.",
    newTagline: "Hosting that bills in rupees and scales with you.",
    nav: ["Features", "Pricing", "Customers", "Docs", "Sign in"],
    banner: "New: Hyderabad region now live",
    plans: [
      { name: "Spark", price: 399, features: ["2 sites", "1 GB storage", "Daily backups"] },
      { name: "Growth", price: 1199, features: ["15 sites", "20 GB storage", "Staging", "Chat support"] },
      { name: "Scale", price: 2999, features: ["Unlimited sites", "100 GB storage", "Dedicated IP", "Phone support"] },
    ],
  },
  orbitly: {
    name: "Orbitly Cloud",
    tagline: "Containers and databases, managed for you.",
    newTagline: "One platform for apps, data and AI workloads.",
    nav: ["Platform", "Pricing", "Partners", "Docs", "Console"],
    banner: "Webinar: scaling Postgres on Orbitly, this Friday",
    plans: [
      { name: "Basic", price: 599, features: ["1 container", "Managed Postgres 1 GB", "Metrics"] },
      { name: "Team", price: 1799, features: ["5 containers", "Managed Postgres 10 GB", "Role-based access", "Audit log"] },
      { name: "Enterprise", price: null, features: ["Custom limits", "Dedicated cluster", "99.95% SLA", "Account manager"] },
    ],
  },
};

export function applyScenarios(site: Site, version: string[]) {
  const has = (v: string) => version.includes(v);
  const plans = site.plans.map((p, i) => {
    const middle = i === 1;
    return {
      ...p,
      price: middle && has("price_cut_40") && p.price ? Math.round(p.price * 0.6) : p.price,
      features: middle && has("add_feature") ? [...p.features, site.shop?.newFeature ?? "Mumbai region"] : p.features,
    };
  });
  return {
    ...site,
    plans,
    tagline: has("positioning") ? site.newTagline : site.tagline,
    nav: has("cosmetic") ? [...site.nav].reverse() : site.nav,
    banner: has("cosmetic") ? `${site.banner}. Limited time!` : site.banner,
    checkedAt: has("cosmetic") ? "14:05" : "10:42",
    cardClass: has("cosmetic") ? "v2" : "v1",
  };
}

const CSS = `body{margin:0;font-family:system-ui,sans-serif;color:#1e293b}.demo-ribbon{background:#fcd34d;padding:6px;text-align:center;font:700 13px system-ui}
nav{display:flex;justify-content:space-between;align-items:center;padding:16px 24px;border-bottom:1px solid #e2e8f0}nav ul{display:flex;gap:20px;list-style:none;margin:0;padding:0}
.banner{background:#4f46e5;color:#fff;text-align:center;padding:8px;font-size:14px}main{max-width:1000px;margin:0 auto;padding:48px 24px}
#hero{text-align:center}h1{font-size:40px;margin:0}.muted{color:#64748b}.cards{display:grid;grid-template-columns:repeat(auto-fit,minmax(240px,1fr));gap:24px;margin-top:32px}
.plan{border:1px solid #cbd5e1;border-radius:12px;padding:24px}.plan.v2{border-width:2px;border-radius:18px}.price{font-size:28px;font-weight:700}
footer{border-top:1px solid #e2e8f0;padding:32px 24px;color:#64748b;font-size:14px}`;

const SAAS_FAQ = `<h3>Can I change plans later?</h3><p>Yes. Upgrades apply immediately and downgrades apply from your next billing cycle.</p>
<h3>Do you issue GST invoices?</h3><p>Every invoice carries your GSTIN. Payments by UPI, card or net banking.</p>
<h3>Where are your servers?</h3><p>Our primary region is in India, with backups replicated to a second availability zone.</p>`;

export function renderMockHtml(site: Site, version: string[]): string {
  const s = applyScenarios(site, version);
  const shop = site.shop;

  const plans = s.plans
    .map((p) => `<div class="plan ${s.cardClass}"><h3>${p.name}</h3>
<p class="price">${p.price === null ? "Contact sales" : `₹${p.price.toLocaleString("en-IN")}${shop?.unit ?? " /month"}`}</p>
<ul>${p.features.map((f) => `<li>${f}</li>`).join("")}</ul></div>`)
    .join("\n");
  const faq = shop ? shop.faq.map(([q, a]) => `<h3>${q}</h3><p>${a}</p>`).join("\n") : SAAS_FAQ;

  const html = `<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="robots" content="noindex"><title>${s.name} ${shop ? "shop" : "pricing"} (demo)</title><style>${CSS}</style></head><body>
<aside class="demo-ribbon">Demo data: fictional company. Not a real business.</aside>
<nav><strong>${s.name}</strong><ul>${s.nav.map((n) => `<li>${n}</li>`).join("")}</ul></nav>
<div class="banner">${s.banner}</div>
<main>
<section id="hero"><h1>${s.tagline}</h1>
<p class="muted">${shop?.blurb ?? "Deploy from GitHub, get a URL, scale when traffic comes. Servers in India."}</p>
<p class="muted">Status: all systems normal · last checked ${s.checkedAt} IST</p></section>
<section id="pricing"><h2>${shop?.title ?? "Simple pricing in rupees"}</h2><p class="muted">${shop?.note ?? "Billed monthly. GST extra. Cancel anytime."}</p>
<div class="cards">
${plans}
</div></section>
<section id="faq"><h2>Questions</h2>
${faq}</section>
</main>
<footer>© 2026 ${s.name} (fictional). Terms · Privacy · Status · Careers</footer>
</body></html>`;

  return html;
}

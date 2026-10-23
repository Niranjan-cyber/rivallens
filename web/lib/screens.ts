// Profile-scoped sections of the app shell (screen IDs from the user-journeys doc).
// The four dashboards; each section below belongs to one group (home is the main dashboard).
export const groups = [
  { key: "home", label: "Overview" },
  { key: "product", label: "Product" },
  { key: "money", label: "Finance" },
  { key: "market", label: "Market" },
  { key: "customers", label: "Customers" },
] as const;

export const groupOf: Record<string, (typeof groups)[number]["key"]> = {
  home: "home", product: "product", simulator: "product", finance: "money", customers: "customers",
  dashboard: "market", competitors: "market", comparison: "market", alerts: "market", reports: "market", settings: "market",
  competitor: "market", run: "market", receipt: "market", card: "home", "product-detail": "product",
};

export const sections = [
  { slug: "home", label: "Overview", screen: "S-21", purpose: "What needs your attention this week across products, finance, market and customers." },
  { slug: "product", label: "Products", screen: "S-22", purpose: "Your existing and new products, each in its exact market category." },
  { slug: "finance", label: "Finance", screen: "S-24", purpose: "Revenue, margins, funding, transactions and runway from your uploads and entries." },
  { slug: "customers", label: "Customers", screen: "S-26", purpose: "What customers say and want, from reviews, comments and mentions." },
  { slug: "dashboard", label: "Market overview", screen: "S-09", purpose: "Latest picture for this business: monitored competitors, recent changes, simulator summary and the Run monitor button." },
  { slug: "competitors", label: "Competitors", screen: "S-08", purpose: "Competitors found for you in the Indian market, split into comparable and inspiration, with the pages being watched." },
  { slug: "comparison", label: "Comparison", screen: "S-13", purpose: "Side-by-side comparison on criteria you choose. Every cell shows its source and the date it was seen." },
  { slug: "simulator", label: "Simulator", screen: "S-14", purpose: "Compare launch prices and scenarios using observed competitor data and assumptions you can edit." },
  { slug: "reports", label: "Reports", screen: "S-15", purpose: "A short report where every claim links to its evidence. Download it as a PDF." },
  { slug: "alerts", label: "Alerts", screen: "S-16", purpose: "Important competitor changes, ranked by priority, each linked to its receipt." },
  { slug: "settings", label: "Settings", screen: "S-17", purpose: "Choose which changes alert you and which pages are watched." },
] as const;

export const extraScreens = {
  "product-detail": { label: "Product", screen: "S-23", purpose: "One product against its exact category: price, features, add-ons, revenue and premium inspirations." },
  competitor: { label: "Competitor", screen: "S-12", purpose: "One competitor over time." },
  card: { label: "Profile card", screen: "S-06", purpose: "The card that drives discovery and comparison." },
  run: { label: "Monitoring run", screen: "S-10", purpose: "What changed since the last check, what was ignored, and why." },
  receipt: { label: "Change receipt", screen: "S-11", purpose: "Proof of one change: before and after, the date it was seen, and the saved page." },
} as const;

export const SAMPLE_PROFILE = "stacknest-demo";

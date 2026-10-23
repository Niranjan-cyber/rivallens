// Profile-scoped sections of the app shell (screen IDs from the user-journeys doc).
export const sections = [
  { slug: "dashboard", label: "Dashboard", screen: "S-09", purpose: "Latest picture for this business: monitored competitors, recent changes, simulator summary and the Run monitor button." },
  { slug: "competitors", label: "Competitors", screen: "S-08", purpose: "Competitors found for you in the Indian market, split into comparable and inspiration, with the pages being watched." },
  { slug: "comparison", label: "Comparison", screen: "S-13", purpose: "Side-by-side comparison on criteria you choose. Every cell shows its source and the date it was seen." },
  { slug: "simulator", label: "Simulator", screen: "S-14", purpose: "Compare launch prices and scenarios using observed competitor data and assumptions you can edit." },
  { slug: "reports", label: "Reports", screen: "S-15", purpose: "A short report where every claim links to its evidence. Download it as a PDF." },
  { slug: "alerts", label: "Alerts", screen: "S-16", purpose: "Important competitor changes, ranked by priority, each linked to its receipt." },
  { slug: "settings", label: "Settings", screen: "S-17", purpose: "Choose which changes alert you and which pages are watched." },
] as const;

export const extraScreens = {
  run: { label: "Monitoring run", screen: "S-10", purpose: "What changed since the last check, what was ignored, and why." },
  receipt: { label: "Change receipt", screen: "S-11", purpose: "Proof of one change: before and after, the date it was seen, and the saved page." },
} as const;

export const SAMPLE_PROFILE = "stacknest-demo";

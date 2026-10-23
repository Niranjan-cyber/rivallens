// Plain-language names for change types and field paths (shared by S-10 and S-11).
export const CHANGES: Record<string, string> = {
  price_decrease: "Price cut",
  price_increase: "Price rise",
  plan_added: "New plan",
  plan_removed: "Plan dropped",
  feature_added: "Feature added",
  feature_removed: "Feature removed",
  positioning_change: "New positioning",
  price_missing: "Price no longer shown",
  price_added: "Price now shown",
  currency_change: "Currency changed",
};

export function fieldLabel(field: string) {
  const [, plan, part] = field.split(".");
  if (field === "headline") return "Headline";
  return part ? `${plan} plan ${part === "price" ? "price" : part}` : `${plan} plan`;
}

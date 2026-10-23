"use client";

import { useEffect, useState } from "react";
import { ButtonLink, SampleBadge } from "@/components/ui";
import { api } from "@/lib/api";

type Field = { value: unknown; origin?: string };
type Profile = { id: string; name: string; kind: string; offering_type: string; card: Record<string, Field | unknown>; is_demo_data: boolean };

const ORIGIN: Record<string, string> = { user: "You entered", ai_drafted: "AI-drafted", public_source: "Public source" };
const ROWS: [string, string][] = [
  ["category", "Category"], ["industry", "Industry"], ["website", "Website"], ["india_markets", "Indian markets"],
  ["price", "Price"], ["attributes", "Key attributes"], ["problem", "Problem"], ["target_customer", "Target customer"],
  ["planned_features", "Planned features"], ["watch", "Watching for"],
];

function show(v: unknown): string {
  if (v == null || v === "" || (Array.isArray(v) && v.length === 0)) return "unknown";
  if (Array.isArray(v)) return v.join(", ");
  if (typeof v === "object" && "amount" in (v as object)) {
    const p = v as { amount: number | null; currency?: string; period?: string };
    if (p.amount == null) return "unknown";
    return `${p.currency === "USD" ? "$" : "₹"}${p.amount.toLocaleString("en-IN")}${p.period && p.period !== "one_time" ? `/${p.period}` : ""}`;
  }
  return String(v);
}

// S-06: the card that drives discovery and comparison, each field labelled by where it came from.
export function CardView({ profileId }: { profileId: string }) {
  const [p, setP] = useState<Profile | null>(null);
  const [error, setError] = useState<string | null>(null);
  useEffect(() => {
    api<Profile>(`/api/v1/profiles/${profileId}`).then(setP, (e: Error) => setError(e.message));
  }, [profileId]);

  if (error) return <p className="rounded-btn bg-lifted p-6 text-charcoal">{error}</p>;
  if (!p) return <div className="h-64 rounded-stadium bg-lifted" aria-busy="true" />;

  return (
    <section data-screen="S-06">
      <div className="flex flex-wrap items-center gap-3">
        <h1 className="text-[32px] leading-tight md:text-[40px]">{p.name}</h1>
        {p.is_demo_data && <SampleBadge label="Demo data" />}
      </div>
      <p className="mt-2 text-[17px] text-charcoal">{p.kind === "idea" ? "Idea card" : "Business card"} · sells a {p.offering_type}</p>
      <dl className="mt-6 divide-y divide-ghost rounded-stadium bg-lifted px-7">
        {ROWS.map(([k, label]) => {
          const raw = p.card[k];
          const f: Field = raw && typeof raw === "object" && "value" in (raw as object) ? (raw as Field) : { value: raw, origin: p.is_demo_data ? undefined : "user" };
          if (f.value == null && ["problem", "target_customer", "planned_features"].includes(k) && p.kind !== "idea") return null;
          return (
            <div key={k} className="grid gap-1 py-4 sm:grid-cols-[180px_1fr_auto] sm:items-baseline sm:gap-6">
              <dt className="text-[15px] text-slate">{label}</dt>
              <dd className={`text-[17px] ${show(f.value) === "unknown" ? "text-slate" : ""}`}>{show(f.value)}</dd>
              <dd className="text-[13px] text-slate">{f.value != null && f.origin ? ORIGIN[f.origin] : ""}</dd>
            </div>
          );
        })}
      </dl>
      <div className="mt-6 flex flex-wrap gap-3">
        <ButtonLink href={`/app/${p.id}/competitors?discover=1`}>Find competitors</ButtonLink>
        <ButtonLink href={`/app/${p.id}/home`} variant="secondary">Go to overview</ButtonLink>
      </div>
    </section>
  );
}

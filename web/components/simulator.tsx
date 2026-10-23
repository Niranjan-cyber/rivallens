"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { SampleBadge } from "@/components/ui";
import { api } from "@/lib/api";

type Scenario = { conversion: number; customers_m12: number; revenue_12m_inr: number; break_even_month: number | null };
type Option = { id: string; price_inr: number; origin: string; scenarios: Record<"best" | "expected" | "worst", Scenario> };
type Assumption = { key: string; value: number; unit: string; origin: "user" | "default" | "your assumption" };
type Flag = { code: string; severity: string; text: string; evidence_ids: string[]; assumption_keys: string[] };
export type Simulation = {
  version: number; label: string; replanned: { from_version: number; trigger_change_event_id: string; summary: string } | null;
  market: { median_price_inr: number; origin: string; n_priced: number; evidence: { name: string; price_inr: number; source_url: string; observed_at: string; evidence_id: string | null }[] };
  feature_coverage: number; options: Option[]; recommended_option: string; recommended_price_inr: number; reason: string; warning: boolean;
  assumption_list: Assumption[]; viability_flags: Flag[]; price_unit?: string;
};

const LABELS: Record<string, string> = {
  segment_size: "Reachable accounts", base_conversion: "Conversion at market price", elasticity_best: "Price sensitivity (best)",
  elasticity_expected: "Price sensitivity (expected)", elasticity_worst: "Price sensitivity (worst)", coverage_weight: "Feature coverage weight",
  ramp_months: "Months to full ramp", upfront_cost: "Upfront cost", monthly_cost: "Monthly cost",
};
const ORIGIN = { user: "you edited", default: "default", "your assumption": "your assumption" };
const inr = (n: number) => `₹${Math.round(n).toLocaleString("en-IN")}`;

// S-14: compare launch prices under stated assumptions. Re-plans when a competitor's price changes.
export function Simulator({ profileId }: { profileId: string }) {
  const [sim, setSim] = useState<Simulation | null>(null);
  const [draft, setDraft] = useState<Record<string, string>>({});
  const [price, setPrice] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    api<Simulation>(`/api/v1/profiles/${profileId}/simulation`).then(setSim, (e: Error) => setError(e.message));
  }, [profileId]);

  async function send(path: string, body: object) {
    setBusy(true);
    await api<Simulation>(`/api/v1/profiles/${profileId}/simulation/${path}`, { method: path === "options" ? "POST" : "PUT", body: JSON.stringify(body) })
      .then((s) => (setSim(s), setDraft({}), setPrice("")), (e: Error) => setError(e.message));
    setBusy(false);
  }

  if (error) return <p className="rounded-btn bg-lifted p-6 text-charcoal">{error}</p>;
  if (!sim) return <div className="h-64 rounded-stadium bg-lifted" aria-busy="true" />;
  const changed = Object.entries(draft).filter(([, v]) => v !== "" && !Number.isNaN(Number(v)));

  return (
    <section data-screen="S-14">
      <div className="flex flex-wrap items-center gap-3">
        <h1 className="text-[32px] leading-tight md:text-[40px]">Launch simulator</h1>
        <span className="rounded-pill border border-ink px-3 py-1 text-[13px] font-medium">{sim.label}</span>
        <SampleBadge label="Demo data" />
      </div>

      {sim.replanned && (
        <Link href={`/app/${profileId}/receipt?id=${sim.replanned.trigger_change_event_id}`}
          className="mt-6 block rounded-btn border-[1.5px] border-signal bg-white p-5 hover:shadow-lift-1">
          <span className="text-[14px] font-medium text-signal">Re-planned from version {sim.replanned.from_version}</span>
          <span className="mt-1 block text-[20px] font-medium tracking-[-0.02em]">{sim.replanned.summary}</span>
          <span className="mt-1 block text-[14px] text-slate">See the receipt for that change</span>
        </Link>
      )}

      <div className="mt-6 rounded-stadium bg-ink p-7 text-canvas sm:p-9">
        <p className="text-[15px] text-dust">Recommended launch price · version {sim.version}</p>
        <p className="mt-1 text-[52px] font-medium leading-none tracking-[-0.03em]">{inr(sim.recommended_price_inr)}<span className="text-[24px] text-dust">{sim.price_unit ?? "/month"}</span></p>
        <p className="mt-3 max-w-[40rem] text-[16px] text-dust">Option {sim.recommended_option}. {sim.reason}</p>
      </div>

      {sim.viability_flags.length > 0 && (
        <ul className="mt-6 grid gap-2">
          {sim.viability_flags.map((f) => (
            <li key={f.code} className={`rounded-btn p-4 ${f.severity === "high" ? "border-[1.5px] border-signal bg-white" : "bg-lifted"}`}>
              <span className="font-medium">{f.text}</span>
              {f.assumption_keys.length > 0 && <span className="block text-[14px] text-slate">Depends on: {f.assumption_keys.map((k) => LABELS[k] ?? k).join(", ")}</span>}
              {f.evidence_ids.filter(Boolean).length > 0 && (
                <span className="block text-[14px]">Evidence: {f.evidence_ids.filter(Boolean).map((id, i) => (
                  <Link key={id} href={`/app/${profileId}/receipt?id=${id}`} className="mr-2 text-link underline">receipt {i + 1}</Link>))}
                </span>
              )}
            </li>
          ))}
        </ul>
      )}

      <h2 className="mt-10 text-[24px] font-medium tracking-[-0.02em]">Options</h2>
      <div className="mt-3 overflow-x-auto rounded-btn border border-dust bg-white">
        <table className="w-full min-w-[640px] border-collapse text-left text-[14px]">
          <thead>
            <tr className="border-b border-dust bg-lifted">
              <th className="p-3 font-medium">Option</th>
              {(["Best", "Expected", "Worst"] as const).map((s) => <th key={s} className="p-3 font-medium">{s} case: 12-month revenue, break-even</th>)}
            </tr>
          </thead>
          <tbody>
            {sim.options.map((o) => (
              <tr key={o.id} className={`border-b border-ghost ${o.id === sim.recommended_option ? "bg-canvas" : ""}`}>
                <th scope="row" className="p-3 align-top font-medium">
                  {o.id} · {inr(o.price_inr)}{sim.price_unit === "" ? "" : "/mo"}{o.id === sim.recommended_option && " ✓"}
                  <span className="block text-[12px] font-normal text-slate">{o.origin}</span>
                </th>
                {(["best", "expected", "worst"] as const).map((s) => (
                  <td key={s} className="p-3 align-top">
                    {inr(o.scenarios[s].revenue_12m_inr)}
                    <span className="block text-[12px] text-slate">
                      {o.scenarios[s].customers_m12} customers by month 12 · {o.scenarios[s].break_even_month ? `break-even month ${o.scenarios[s].break_even_month}` : "no break-even in 36 months"}
                    </span>
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <div className="mt-3 flex flex-wrap items-center gap-2">
        <label htmlFor="own-price" className="text-[15px]">Try your own price</label>
        <input id="own-price" type="number" min={1} value={price} onChange={(e) => setPrice(e.target.value)} placeholder="₹ per month"
          className="w-36 rounded-[14px] border border-ink/30 bg-white px-3 py-2 text-[15px]" />
        <button type="button" disabled={!price || busy} onClick={() => send("options", { price_inr: Number(price) })}
          className="rounded-pill border border-ink px-4 py-2 text-[14px] font-medium disabled:opacity-50">Add option</button>
      </div>

      <div className="mt-10 grid gap-6 lg:grid-cols-2">
        <div>
          <h2 className="text-[24px] font-medium tracking-[-0.02em]">Market price</h2>
          <p className="mt-1 text-charcoal">
            Median {inr(sim.market.median_price_inr)}/month{" "}
            <span className="text-slate">({sim.market.origin === "evidence" ? `from evidence, ${sim.market.n_priced} comparable mid-tier plans` : "your assumption: not enough competitor prices yet"})</span>
          </p>
          <ul className="mt-3 divide-y divide-ghost rounded-btn bg-lifted px-5 text-[15px]">
            {sim.market.evidence.map((e) => (
              <li key={e.name} className="flex flex-wrap justify-between gap-2 py-3">
                <span>{e.name} · {inr(e.price_inr)}/mo</span>
                <span className="text-[13px]">
                  {e.evidence_id ? <Link href={`/app/${profileId}/receipt?id=${e.evidence_id}`} className="text-link underline">receipt</Link>
                    : <a href={e.source_url} target="_blank" rel="noreferrer" className="text-link underline">source</a>}
                  <span className="text-slate"> · seen {new Date(e.observed_at).toLocaleDateString("en-IN", { day: "numeric", month: "short" })}</span>
                </span>
              </li>
            ))}
          </ul>
          <p className="mt-2 text-[14px] text-slate">Your feature coverage vs comparables: {Math.round(sim.feature_coverage * 100)}%</p>
        </div>
        <div>
          <h2 className="text-[24px] font-medium tracking-[-0.02em]">Assumptions</h2>
          <ul className="mt-3 grid gap-2">
            {sim.assumption_list.map((a) => (
              <li key={a.key} className="grid grid-cols-[1fr_auto] items-center gap-3 text-[15px]">
                <label htmlFor={`a-${a.key}`}>
                  {LABELS[a.key] ?? a.key}
                  <span className="block text-[12px] text-slate">{ORIGIN[a.origin]}{a.unit && ` · ${a.unit}`}</span>
                </label>
                <input id={`a-${a.key}`} type="number" step="any" min={0} value={draft[a.key] ?? String(a.value)}
                  onChange={(e) => setDraft({ ...draft, [a.key]: e.target.value })}
                  className="w-36 rounded-[12px] border border-ink/30 bg-white px-3 py-1.5 text-right tabular-nums" />
              </li>
            ))}
          </ul>
          <button type="button" disabled={!changed.length || busy}
            onClick={() => send("assumptions", { assumptions: Object.fromEntries(changed.map(([k, v]) => [k, Number(v)])) })}
            className="mt-4 inline-flex min-h-11 items-center rounded-btn border-[1.5px] border-ink bg-ink px-6 text-[16px] font-medium text-canvas disabled:opacity-50">
            {busy ? "Recalculating…" : "Recalculate"}
          </button>
        </div>
      </div>
    </section>
  );
}

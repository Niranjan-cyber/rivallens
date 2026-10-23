"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { api } from "@/lib/api";

type Scenario = { conversion: number; customers_m12: number; revenue_12m_inr: number; break_even_month: number | null };
type Option = {
  id: string; price_inr: number; origin: string; scenarios: Record<"best" | "expected" | "worst", Scenario>;
  unit_margin_inr?: number; gross_profit_12m_inr?: number; after_runway: boolean;
};
type Input = { label: string; value: string; source: "market" | "money" | "customers" | "product"; link: string | null; evidence_id: string | null };
type Sim = {
  label: string; options: Option[]; recommended_option: string; reason: string; price_unit: string; inputs: Input[];
  viability_flags: { code: string; severity: string; text: string }[];
};
type Segment = { segment: string | null; why: string[]; evidence_ids: string[]; evidence: { id: string; text: string; source: string }[]; message?: string };

const inr = (n: number) => `₹${Math.round(n).toLocaleString("en-IN")}`;
const SOURCE = { market: "Market", money: "Money", customers: "Customers", product: "This product", profile: "Your business card" } as Record<string, string>;

// S-23 decision layer (B14i): a suggested segment and a simulator whose inputs come from the other dashboards.
export function ProductPlan({ productId, profileId, version }: { productId: string; profileId: string; version: unknown }) {
  const [sim, setSim] = useState<Sim | null>(null);
  const [seg, setSeg] = useState<Segment | null>(null);
  const [error, setError] = useState<string | null>(null);
  useEffect(() => {
    api<Sim>(`/api/v1/products/${productId}/simulation`).then((s) => { setSim(s); setError(null); }, (e: Error) => setError(e.message));
    api<Segment>(`/api/v1/products/${productId}/segment`).then(setSeg, () => {});
  }, [productId, version]);
  const href = (link: string | null) => (link === "product-detail" ? `/app/${profileId}/product-detail?id=${productId}` : `/app/${profileId}/${link}`);

  return (
    <div className="mt-8 grid gap-4 md:grid-cols-[1fr_1.6fr]">
      <div className="rounded-stadium bg-lifted p-7" data-testid="segment">
        <p className="text-[15px] font-medium">Suggested customer segment</p>
        {!seg ? <p className="mt-2 text-charcoal" aria-busy="true">Reading Market and Customers…</p> : seg.segment ? (
          <>
            <p className="mt-2 text-[22px] font-medium leading-snug tracking-[-0.01em]">{seg.segment}</p>
            <ul className="mt-3 space-y-1 text-[15px]">{seg.why.map((w) => <li key={w}>· {w}</li>)}</ul>
            <ul className="mt-4 space-y-1.5 border-t border-ink/10 pt-3 text-[13px] text-charcoal">
              {seg.evidence.filter((e) => seg.evidence_ids.includes(e.id)).map((e) => (
                <li key={e.id}><span className="mr-1.5 rounded-pill bg-white px-2 py-0.5 font-medium">{e.id}</span>{e.text} <span className="text-slate">· {SOURCE[e.source]}</span></li>
              ))}
            </ul>
            <p className="mt-3 text-[12px] text-slate">AI suggestion; kept only because it cites the evidence above.</p>
          </>
        ) : <p className="mt-2 text-charcoal">{seg.message}</p>}
      </div>

      <div className="rounded-stadium bg-lifted p-7" data-testid="product-sim">
        <div className="flex flex-wrap items-baseline justify-between gap-2">
          <p className="text-[15px] font-medium">Price simulator for this product</p>
          <p className="text-[12px] text-slate">{sim?.label ?? "Scenario model, not a forecast"}</p>
        </div>
        {error && <p className="mt-2 text-charcoal">{error}</p>}
        {sim && (
          <>
            <ul className="mt-3 flex flex-wrap gap-2" aria-label="Inputs">
              {sim.inputs.map((i) => (
                <li key={i.label}>
                  <Link href={href(i.link)} className="inline-block rounded-pill border border-ink/20 bg-white px-3 py-1 text-[13px] hover:border-ink"
                    data-source={i.source}>
                    <span className="text-slate">{i.label}:</span> {i.value} <span className="font-medium">· {SOURCE[i.source]} →</span>
                  </Link>
                </li>
              ))}
            </ul>
            {sim.viability_flags.map((f) => (
              <p key={f.code} role="note" data-flag={f.code} className={`mt-3 rounded-btn p-3 text-[14px] ${f.severity === "high" ? "bg-ink text-canvas" : "bg-white"}`}>{f.text}</p>
            ))}
            <div className="mt-4 overflow-x-auto">
              <table className="w-full min-w-[560px] text-left text-[14px]">
                <thead className="text-[12px] text-slate">
                  <tr><th className="p-2 font-medium">Price</th><th className="p-2 font-medium">Expected conversion</th><th className="p-2 font-medium">12-month revenue</th>
                    <th className="p-2 font-medium">Gross profit</th><th className="p-2 font-medium">Break-even</th></tr>
                </thead>
                <tbody>
                  {sim.options.map((o) => {
                    const e = o.scenarios.expected;
                    return (
                      <tr key={o.id} className={`border-t border-ink/10 ${o.id === sim.recommended_option ? "bg-white font-medium" : ""}`}>
                        <td className="p-2">{inr(o.price_inr)}{sim.price_unit} <span className="block text-[12px] font-normal text-slate">{o.id === sim.recommended_option ? "Recommended" : o.origin}</span></td>
                        <td className="p-2">{(e.conversion * 100).toFixed(1)}%</td>
                        <td className="p-2">{inr(e.revenue_12m_inr)}</td>
                        <td className="p-2">{o.gross_profit_12m_inr != null ? inr(o.gross_profit_12m_inr) : <span className="text-slate">Unknown</span>}</td>
                        <td className="p-2">{e.break_even_month ? `Month ${e.break_even_month}` : "Not in 36 months"}{o.after_runway && <span className="block text-[12px]">after your runway</span>}</td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
            <p className="mt-3 text-[13px] text-charcoal">{sim.reason}</p>
          </>
        )}
      </div>
    </div>
  );
}

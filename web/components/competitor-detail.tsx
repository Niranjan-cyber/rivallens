"use client";

import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { useEffect, useState } from "react";
import { SampleBadge } from "@/components/ui";
import { api, type Competitor } from "@/lib/api";

type Point = { at: string; amount_inr: number; source: "observed" | "internet_archive" };
type History = Competitor & {
  current_fields: { plans: { name: string; price: { raw: string | null }; features: string[] }[]; headline: { text: string } | null } | null;
  current_observed_at: string | null;
  timeline: { type: "run" | "receipt" | "failure"; at: string; ref_id: string; label: string }[];
  price_series: { plan: string; points: Point[] }[];
};

const day = (ts: string) => new Date(ts).toLocaleString("en-IN", { day: "numeric", month: "short", hour: "numeric", minute: "2-digit" });
const inr = (n: number) => `₹${Math.round(n).toLocaleString("en-IN")}`;

// One plan's monthly ₹ price over time as a step line; points that changed are marked and labelled.
function PriceChart({ plan, points }: { plan: string; points: Point[] }) {
  const W = 320, H = 128, L = 8, R = 64, T = 18, B = 22;
  const ys = points.map((p) => p.amount_inr);
  const lo = Math.min(...ys), hi = Math.max(...ys), span = hi - lo || hi || 1;
  const x = (i: number) => L + (points.length === 1 ? (W - L - R) / 2 : (i * (W - L - R)) / (points.length - 1));
  const y = (v: number) => T + (hi === lo ? (H - T - B) / 2 : ((hi - v) / span) * (H - T - B));
  const path = points.map((p, i) => (i === 0 ? `M${x(i)},${y(p.amount_inr)}` : `H${x(i)}V${y(p.amount_inr)}`)).join("");
  const last = points[points.length - 1];
  return (
    <figure className="rounded-btn bg-lifted p-4">
      <figcaption className="flex justify-between text-[15px]">
        <span className="font-medium">{plan}</span>
        <span className="text-slate">{inr(last.amount_inr)}/mo now</span>
      </figcaption>
      <svg viewBox={`0 0 ${W} ${H}`} className="mt-2 w-full" role="img" aria-label={`${plan} price: ${points.map((p) => `${inr(p.amount_inr)} on ${day(p.at)}`).join(", ")}`}>
        <line x1={L} x2={W - R} y1={H - B} y2={H - B} stroke="var(--color-dust)" strokeWidth="1" />
        <path d={path} fill="none" stroke="var(--color-ink)" strokeWidth="2" strokeLinejoin="round" />
        {points.map((p, i) => {
          const changed = i > 0 && p.amount_inr !== points[i - 1].amount_inr;
          return (
            <g key={i}>
              <circle cx={x(i)} cy={y(p.amount_inr)} r="12" fill="transparent"><title>{`${inr(p.amount_inr)}/mo · ${day(p.at)} · ${p.source === "internet_archive" ? "Internet Archive" : "observed"}`}</title></circle>
              <circle cx={x(i)} cy={y(p.amount_inr)} r={changed ? 5 : 4} fill={changed ? "var(--color-signal)" : "var(--color-ink)"} stroke="var(--color-lifted)" strokeWidth="2" pointerEvents="none" />
              {changed && <text x={x(i) + 8} y={y(p.amount_inr) - 6} fontSize="12" fill="var(--color-ink)">{inr(p.amount_inr)}</text>}
            </g>
          );
        })}
        <text x={W - R + 6} y={y(points[0].amount_inr) + 4} fontSize="11" fill="var(--color-slate)">{points.length > 1 && last.amount_inr !== points[0].amount_inr ? `was ${inr(points[0].amount_inr)}` : ""}</text>
        <text x={L} y={H - 6} fontSize="11" fill="var(--color-slate)">{day(points[0].at)}</text>
        {points.length > 1 && <text x={W - R} y={H - 6} fontSize="11" fill="var(--color-slate)" textAnchor="end">{day(last.at)}</text>}
      </svg>
    </figure>
  );
}

// S-12: one competitor over time.
export function CompetitorDetail({ profileId }: { profileId: string }) {
  const id = useSearchParams().get("id");
  const [h, setH] = useState<History | null>(null);
  const [error, setError] = useState<string | null>(id ? null : "Open a competitor from the Competitors page.");
  useEffect(() => {
    if (id) api<History>(`/api/v1/competitors/${id}`).then(setH, (e: Error) => setError(e.message));
  }, [id]);

  if (error) return <p className="rounded-btn bg-lifted p-6 text-charcoal">{error}</p>;
  if (!h) return <div className="h-64 rounded-stadium bg-lifted" aria-busy="true" />;
  const icon = { run: "○", receipt: "●", failure: "×" };

  return (
    <section data-screen="S-12">
      <Link href={`/app/${profileId}/competitors`} className="text-[15px] text-slate hover:text-ink">Back to competitors</Link>
      <div className="mt-3 flex flex-wrap items-center gap-3">
        <h1 className="text-[32px] leading-tight md:text-[40px]">{h.name}</h1>
        {h.is_demo_data && <SampleBadge label="Demo data" />}
      </div>
      <p className="mt-2 text-[16px] text-charcoal">
        <span className="capitalize">{h.relation}</span> · {h.domain}
        {h.india_signals?.hits?.length ? ` · India: ${h.india_signals.hits.join(", ")}` : ""}
        {h.sources[0] && <> · <a href={h.sources[0].url} target="_blank" rel="noreferrer" className="text-link underline">{h.sources[0].page_type} page</a></>}
      </p>

      <h2 className="mt-8 text-[24px] font-medium tracking-[-0.02em]">Price history</h2>
      {h.price_series.length === 0 ? <p className="mt-2 text-charcoal">No prices observed yet.</p> : (
        <div className="mt-3 grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
          {h.price_series.map((s) => <PriceChart key={s.plan} plan={s.plan} points={s.points} />)}
        </div>
      )}

      <div className="mt-8 grid gap-8 lg:grid-cols-2">
        <div>
          <h2 className="text-[24px] font-medium tracking-[-0.02em]">Timeline</h2>
          <ol className="mt-3 divide-y divide-ghost rounded-btn bg-lifted px-5">
            {h.timeline.map((t, i) => (
              <li key={i} className="grid grid-cols-[1.25rem_1fr] gap-2 py-3 text-[15px]">
                <span aria-hidden="true" className={t.type === "receipt" ? "text-signal" : "text-slate"}>{icon[t.type]}</span>
                <span>
                  {t.type === "receipt" ? <Link href={`/app/${profileId}/receipt?id=${t.ref_id}`} className="font-medium underline">{t.label}</Link>
                    : t.type === "run" && !t.label.startsWith("Baseline") ? <Link href={`/app/${profileId}/run?id=${t.ref_id}`} className="hover:underline">{t.label}</Link>
                    : <span className={t.type === "failure" ? "text-charcoal" : ""}>{t.label}</span>}
                  <span className="block text-[13px] text-slate">{day(t.at)}</span>
                </span>
              </li>
            ))}
          </ol>
        </div>
        <div>
          <h2 className="text-[24px] font-medium tracking-[-0.02em]">Current page</h2>
          {h.current_fields ? (
            <div className="mt-3 rounded-btn bg-lifted p-5 text-[15px]">
              {h.current_fields.headline && <p className="font-medium">“{h.current_fields.headline.text}”</p>}
              <ul className="mt-3 grid gap-2">
                {h.current_fields.plans.map((p) => (
                  <li key={p.name}><span className="font-medium">{p.name}</span> · {p.price.raw ?? "no price shown"}
                    {p.features.length > 0 && <span className="block text-slate">{p.features.join(", ")}</span>}</li>
                ))}
              </ul>
              {h.current_observed_at && <p className="mt-3 text-[13px] text-slate">Seen {day(h.current_observed_at)}</p>}
            </div>
          ) : <p className="mt-2 text-charcoal">Not checked yet.</p>}
        </div>
      </div>
    </section>
  );
}

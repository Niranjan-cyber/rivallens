"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { SampleBadge } from "@/components/ui";
import { api } from "@/lib/api";

type Cell = { value: unknown; display: string; observed_at: string | null; source_url: string | null; known: boolean };
type Criterion = { key: string; label: string; weight: number; direction: "lower_better" | "higher_better" | "info"; enabled: boolean };
type Row = { subject: "you" | "competitor"; competitor_id: string | null; name: string; is_demo_data: boolean; cells: Record<string, Cell>;
  score: number | null; known_weight_pct: number; unknown_count: number; ranked: boolean };
type Comparison = { template: string; criteria: Criterion[]; rows: Row[]; assumptions: { USD_INR_RATE: number } };

const day = (ts: string) => new Date(ts).toLocaleDateString("en-IN", { day: "numeric", month: "short" });

// S-13: you vs competitors on criteria you weight. Unknown cells are shown, counted and never scored.
export function ComparisonMatrix({ profileId }: { profileId: string }) {
  const [set, setSet] = useState<"comparable" | "inspiration">("comparable");
  const [data, setData] = useState<Comparison | null>(null);
  const [error, setError] = useState<string | null>(null);
  const saveTimer = useRef<ReturnType<typeof setTimeout> | null>(null);

  useEffect(() => {
    api<Comparison>(`/api/v1/profiles/${profileId}/comparison?set=${set}`).then(setData, (e: Error) => setError(e.message));
  }, [profileId, set]);

  const save = useCallback((criteria: Criterion[]) => {
    setData((d) => (d ? { ...d, criteria } : d));
    if (saveTimer.current) clearTimeout(saveTimer.current);
    saveTimer.current = setTimeout(() => {
      api<Comparison>(`/api/v1/profiles/${profileId}/criteria?set=${set}`, {
        method: "PUT",
        body: JSON.stringify({ criteria: criteria.map(({ key, enabled, weight }) => ({ key, enabled, weight })) }),
      }).then(setData, (e: Error) => setError(e.message));
    }, 400);
  }, [profileId, set]);

  if (error) return <p className="rounded-btn bg-lifted p-6 text-charcoal">{error}</p>;
  const cols = data?.criteria.filter((c) => c.enabled) ?? [];

  return (
    <section data-screen="S-13">
      <div className="flex flex-wrap items-center gap-3">
        <h1 className="text-[32px] leading-tight md:text-[40px]">Comparison</h1>
        <SampleBadge label="Demo data" />
      </div>
      <p className="mt-3 max-w-[44rem] text-[17px] text-charcoal">
        Each cell shows where it was seen and when. <strong className="font-medium">Unknown</strong> cells are left out of the score, so missing data never counts against anyone; a row needs at least half the weight known to be ranked.
      </p>
      <div role="tablist" className="mt-6 flex gap-2">
        {(["comparable", "inspiration"] as const).map((t) => (
          <button key={t} role="tab" aria-selected={set === t} type="button" onClick={() => (setData(null), setSet(t))}
            className={`rounded-pill border px-4 py-1.5 text-[15px] capitalize ${set === t ? "border-ink bg-ink text-canvas" : "border-ink/30 bg-white"}`}>
            {t}
          </button>
        ))}
      </div>

      {!data ? (
        <div className="mt-6 h-64 rounded-stadium bg-lifted" aria-busy="true" />
      ) : (
        <>
          <details className="mt-6 rounded-btn bg-lifted p-5" open>
            <summary className="cursor-pointer text-[17px] font-medium">Criteria and weights ({data.template} template)</summary>
            <div className="mt-4 grid gap-x-8 gap-y-3 sm:grid-cols-2">
              {data.criteria.filter((c) => c.direction !== "info").map((c) => (
                <label key={c.key} className="grid grid-cols-[auto_1fr_auto] items-center gap-3 text-[15px]">
                  <input type="checkbox" className="size-5 accent-ink" checked={c.enabled}
                    onChange={(e) => save(data.criteria.map((x) => (x.key === c.key ? { ...x, enabled: e.target.checked } : x)))} />
                  <span>{c.label} <span className="text-slate">({c.direction === "lower_better" ? "lower is better" : "higher is better"})</span></span>
                  <span className="flex items-center gap-2">
                    <input type="range" min={0} max={5} value={c.weight} aria-label={`${c.label} weight`} className="w-24 accent-ink"
                      onChange={(e) => save(data.criteria.map((x) => (x.key === c.key ? { ...x, weight: Number(e.target.value) } : x)))} />
                    <span className="w-3 text-right tabular-nums">{c.weight}</span>
                  </span>
                </label>
              ))}
            </div>
            <p className="mt-3 text-[13px] text-slate">Prices are converted to ₹ per month (USD at ₹{data.assumptions.USD_INR_RATE}, yearly ÷ 12).</p>
          </details>

          {data.rows.length <= 1 ? (
            <p className="mt-6 rounded-btn bg-lifted p-6 text-charcoal">No {set} competitors yet. Find competitors, then run monitor to fill this in.</p>
          ) : (
            <div className="mt-6 overflow-x-auto rounded-btn border border-dust bg-white">
              <table className="w-full min-w-[760px] border-collapse text-left text-[14px]">
                <thead>
                  <tr className="border-b border-dust bg-lifted">
                    <th className="sticky left-0 bg-lifted p-3 font-medium">Rank · score</th>
                    {cols.map((c) => <th key={c.key} className="p-3 font-medium">{c.label}{c.direction !== "info" && <span className="text-slate"> ×{c.weight}</span>}</th>)}
                  </tr>
                </thead>
                <tbody>
                  {data.rows.map((r, i) => (
                    <tr key={r.competitor_id ?? "you"} className={`border-b border-ghost ${r.subject === "you" ? "bg-canvas" : ""}`}>
                      <th scope="row" className="sticky left-0 bg-inherit p-3 align-top font-medium">
                        <span className="block">{r.ranked ? `${data.rows.filter((x, j) => x.ranked && j < i).length + 1}. ` : ""}{r.name}</span>
                        <span className="block text-[13px] font-normal text-slate">
                          {r.ranked ? `score ${Math.round((r.score ?? 0) * 100)}` : `not ranked: ${r.known_weight_pct}% of weight known`}
                          {r.unknown_count > 0 && ` · ${r.unknown_count} unknown`}
                        </span>
                      </th>
                      {cols.map((c) => {
                        const cell = r.cells[c.key];
                        return (
                          <td key={c.key} className={`p-3 align-top ${cell?.known ? "" : "bg-lifted text-slate"}`}>
                            <span className={c.key === "positioning" ? "line-clamp-2 block max-w-[14rem]" : "block"}>{cell?.display ?? "Unknown"}</span>
                            {cell?.known && (
                              <span className="block text-[12px] text-slate">
                                {cell.source_url?.startsWith("http") ? (
                                  <a href={cell.source_url} target="_blank" rel="noreferrer" className="underline" title={cell.source_url}>source</a>
                                ) : cell.source_url}
                                {cell.observed_at && ` · ${day(cell.observed_at)}`}
                              </span>
                            )}
                          </td>
                        );
                      })}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </>
      )}
    </section>
  );
}

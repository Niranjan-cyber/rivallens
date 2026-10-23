"use client";

import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { useEffect, useState } from "react";
import { SampleBadge } from "@/components/ui";
import { api, type Run } from "@/lib/api";
import { CHANGES, fieldLabel } from "@/lib/labels";

const REASONS: Record<string, string> = {
  navigation_or_footer: "Menu or footer",
  promo_banner: "Promo banner",
  formatting_only: "Styling only",
  dynamic_content: "Clock or counter",
  whitespace: "Spacing or case",
  reordering: "Same lines, new order",
  outside_pricing: "Outside pricing",
  no_tracked_field: "No tracked field",
};

// S-10: what changed since the last check, and every ignored difference with its reason.
export function RunResult({ profileId }: { profileId: string }) {
  const id = useSearchParams().get("id");
  const [run, setRun] = useState<Run | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const runId = id
      ? Promise.resolve(id)
      : api<{ id: string }[]>(`/api/v1/profiles/${profileId}/runs?limit=1`).then((r) => {
          if (!r[0]) throw new Error("No checks yet. Press Check competitors now on Market to make the first one.");
          return r[0].id;
        });
    runId.then((rid) => api<Run>(`/api/v1/runs/${rid}`)).then(setRun, (e: Error) => setError(e.message));
  }, [id, profileId]);

  if (error) return <p className="rounded-btn bg-lifted p-6 text-charcoal">{error}</p>;
  if (!run) return <div className="h-64 rounded-stadium bg-lifted" aria-busy="true" />;

  const meaningful = run.changes.filter((c) => c.status === "confirmed");
  const review = run.changes.filter((c) => c.status !== "confirmed");
  const when = new Date(run.started_at).toLocaleString("en-IN", { dateStyle: "medium", timeStyle: "short" });

  return (
    <section data-screen="S-10">
      <div className="flex flex-wrap items-center gap-3">
        <h1 className="text-[32px] leading-tight md:text-[40px]">Monitoring run</h1>
        <SampleBadge label="Demo data" />
      </div>
      <p className="mt-3 max-w-[40rem] text-[17px] text-charcoal">
        {run.kind === "baseline"
          ? `First check on ${when}. Every page is saved as the baseline; changes show up from the next run.`
          : `Checked ${run.counts.sources} pages on ${when} and compared each with its previous check.`}
      </p>

      <div className="mt-8 grid gap-4 sm:grid-cols-2">
        <div className="rounded-stadium bg-ink p-8 text-canvas">
          <p className="text-[72px] font-medium leading-none tracking-[-0.04em]">{meaningful.length}</p>
          <p className="mt-3 text-[20px]">meaningful {meaningful.length === 1 ? "change" : "changes"}</p>
          <p className="mt-1 text-[15px] text-dust">Prices, plans, features and positioning</p>
        </div>
        <div className="rounded-stadium bg-lifted p-8">
          <p className="text-[72px] font-medium leading-none tracking-[-0.04em] text-slate">{run.ledger.length}</p>
          <p className="mt-3 text-[20px]">differences ignored</p>
          <p className="mt-1 text-[15px] text-slate">Each one is listed below with the rule that ignored it</p>
        </div>
      </div>

      {meaningful.length > 0 && (
        <>
          <h2 className="mt-12 text-[24px] font-medium tracking-[-0.02em]">What changed</h2>
          <ul className="mt-4 grid gap-3">
            {meaningful.map((c) => (
              <li key={c.change_event_id}>
                <Link href={`/app/${profileId}/receipt?id=${c.change_event_id}`} className="block rounded-btn border-[1.5px] border-ink bg-white p-6 hover:shadow-lift-2">
                <p className="flex justify-between gap-3 text-[15px] text-slate">
                  <span>{c.competitor} · {CHANGES[c.change_type] ?? c.change_type}</span>
                  <span className="font-medium text-ink">See receipt</span>
                </p>
                <p className="mt-1 text-[22px] font-medium tracking-[-0.02em]">
                  {fieldLabel(c.field)}: {c.prev ?? "none"} → {c.curr ?? "none"}
                  {c.delta_pct !== null && (
                    <span className={`ml-2 ${c.delta_pct < 0 ? "text-signal" : "text-charcoal"}`}>
                      ({c.delta_pct > 0 ? "+" : "−"}{Math.abs(c.delta_pct)}%)
                    </span>
                  )}
                </p>
                </Link>
              </li>
            ))}
          </ul>
        </>
      )}

      {review.length > 0 && (
        <>
          <h2 className="mt-12 text-[24px] font-medium tracking-[-0.02em]">Needs a second look</h2>
          <p className="mt-1 text-charcoal">These look unusual (a huge jump, a vanished price or a new currency), so they don&apos;t raise alerts until you check them.</p>
          <ul className="mt-4 grid gap-3">
            {review.map((c) => (
              <li key={c.change_event_id}>
                <Link href={`/app/${profileId}/receipt?id=${c.change_event_id}`} className="block rounded-btn bg-lifted p-6 hover:shadow-lift-1">
                  <p className="text-[15px] text-slate">{c.competitor} · {CHANGES[c.change_type] ?? c.change_type}</p>
                  <p className="mt-1 text-[18px]">{fieldLabel(c.field)}: {c.prev ?? "none"} → {c.curr ?? "none"}</p>
                </Link>
              </li>
            ))}
          </ul>
        </>
      )}

      <h2 className="mt-12 text-[24px] font-medium tracking-[-0.02em]">Ignored, and why</h2>
      {run.ledger.length === 0 ? (
        <p className="mt-2 text-charcoal">{run.kind === "baseline" ? "Nothing to compare yet." : "No other differences on these pages."}</p>
      ) : (
        <ul className="mt-4 divide-y divide-ghost rounded-btn bg-lifted px-6">
          {run.ledger.map((e, i) => (
            <li key={i} className="grid gap-1 py-4 sm:grid-cols-[180px_1fr] sm:gap-6">
              <span className="text-[15px] font-medium">{REASONS[e.reason] ?? e.reason}</span>
              <span className="text-charcoal">
                {e.summary}
                <span className="block text-[14px] text-slate">{e.competitor}, {e.section_key.replace("main#", "")} section</span>
              </span>
            </li>
          ))}
        </ul>
      )}

      {run.failures.length > 0 && (
        <p className="mt-8 rounded-btn bg-lifted p-6 text-charcoal">
          {run.failures.length} {run.failures.length === 1 ? "page" : "pages"} couldn&apos;t be checked this time
          ({run.failures.map((f) => f.status.replace("_", " ")).join(", ")}). They&apos;ll be tried again on the next run.
        </p>
      )}
    </section>
  );
}

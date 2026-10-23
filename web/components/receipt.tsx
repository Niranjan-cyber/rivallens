"use client";

import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { useEffect, useRef, useState } from "react";
import { SampleBadge } from "@/components/ui";
import { api, type Evidence, type EvidenceSide, type Receipt } from "@/lib/api";
import { CHANGES, fieldLabel } from "@/lib/labels";

const fmt = (ts: string) => new Date(ts).toLocaleString("en-IN", { dateStyle: "medium", timeStyle: "short" });

function Pane({ label, side, sha }: { label: string; side: EvidenceSide | null; sha: string | null }) {
  const [html, setHtml] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const box = useRef<HTMLParagraphElement>(null);
  const mark = useRef<HTMLElement>(null);

  useEffect(() => {
    // Open each pane on its highlight, not on the top of the page.
    if (box.current && mark.current) box.current.scrollTop = mark.current.offsetTop - box.current.offsetTop - box.current.clientHeight / 3;
  }, [side]);

  async function viewOriginal() {
    if (!side) return;
    setError(null);
    try {
      const { signed_url } = await api<{ signed_url: string }>(`/api/v1/snapshots/${side.snapshot_id}/html`);
      const res = await fetch(signed_url);
      if (!res.ok || !res.body) throw new Error();
      setHtml(await new Response(res.body.pipeThrough(new DecompressionStream("gzip"))).text());
    } catch {
      setError("The saved page can't be opened right now. The text above is the evidence.");
    }
  }

  if (!side) return <div className="rounded-btn bg-lifted p-6 text-charcoal">{label}: this page wasn&apos;t saved.</div>;
  const { text_window: t, highlight: h } = side;
  return (
    <figure className="min-w-0 rounded-btn bg-lifted p-6">
      <figcaption className="flex flex-wrap items-baseline justify-between gap-2">
        <span className="text-[18px] font-medium">{label}</span>
        <span className="text-[14px] text-slate">seen {fmt(side.observed_at)}</span>
      </figcaption>
      <p ref={box} className="mt-4 max-h-80 overflow-y-auto whitespace-pre-wrap break-words rounded-[12px] bg-white p-4 text-[14px] leading-relaxed text-charcoal">
        {h ? (
          <>
            {t.slice(0, h.start)}
            <mark ref={mark} className="rounded-[4px] bg-signal-light/30 px-0.5 font-medium text-ink">{t.slice(h.start, h.end)}</mark>
            {t.slice(h.end)}
          </>
        ) : t}
      </p>
      <div className="mt-3 flex flex-wrap items-center justify-between gap-2">
        {sha && <span className="text-[13px] text-slate" title={sha}>Page fingerprint {sha.slice(0, 12)}</span>}
        <button type="button" onClick={html ? () => setHtml(null) : viewOriginal}
          className="rounded-pill border border-ink px-4 py-1.5 text-[14px] font-medium hover:bg-white">
          {html ? "Hide original" : "View original"}
        </button>
      </div>
      {error && <p className="mt-2 text-[14px] text-charcoal">{error}</p>}
      {html && (
        // sandbox="" blocks scripts, forms and same-origin access: the saved page is shown, never run.
        <iframe sandbox="" srcDoc={html} referrerPolicy="no-referrer" title={`${label}: saved page`}
          className="mt-3 h-[60vh] w-full rounded-[12px] border border-dust bg-white" />
      )}
    </figure>
  );
}

// S-11: proof of one change. Values, when it was seen, and the saved text on both sides.
export function ReceiptView({ profileId }: { profileId: string }) {
  const id = useSearchParams().get("id");
  const [receipt, setReceipt] = useState<Receipt | null>(null);
  const [evidence, setEvidence] = useState<Evidence | null>(null);
  const [error, setError] = useState<string | null>(id ? null : "Open a change from a monitoring run to see its receipt.");

  useEffect(() => {
    if (!id) return;
    api<Receipt>(`/api/v1/receipts/${id}`).then(setReceipt, (e: Error) => setError(e.message));
    api<Evidence>(`/api/v1/receipts/${id}/evidence`).then(setEvidence, () => {});
  }, [id]);

  async function setRelevant(relevant: boolean) {
    if (!receipt) return;
    await api(`/api/v1/receipts/${receipt.id}/feedback`, { method: "POST", body: JSON.stringify({ relevant }) }).then(
      () => setReceipt({ ...receipt, muted: !relevant }),
      (e: Error) => setError(e.message),
    );
  }

  if (error) return <p className="rounded-btn bg-lifted p-6 text-charcoal">{error} <Link href={`/app/${profileId}/run`} className="text-link underline">Last run</Link></p>;
  if (!receipt) return <div className="h-64 rounded-stadium bg-lifted" aria-busy="true" />;

  const kind = CHANGES[receipt.change_type] ?? receipt.change_type;
  const between = receipt.prev_observed_at && `between ${fmt(receipt.prev_observed_at)} and ${fmt(receipt.observed_at)}`;

  return (
    <section data-screen="S-11">
      <Link href={`/app/${profileId}/run`} className="text-[15px] text-slate hover:text-ink">Back to monitoring run</Link>
      <div className="mt-3 flex flex-wrap items-center gap-3">
        <h1 className="text-[32px] leading-tight md:text-[40px]">Change receipt</h1>
        {receipt.is_demo_data && <SampleBadge label="Demo data" />}
      </div>

      <div className="mt-6 rounded-stadium bg-ink p-7 text-canvas sm:p-10">
        <p className="text-[17px] text-dust">{receipt.competitor.name} · {kind}</p>
        <p className="mt-1 text-[20px]">{fieldLabel(receipt.field)}</p>
        <p className="mt-4 flex flex-wrap items-baseline gap-x-4 gap-y-1 text-[36px] font-medium leading-tight tracking-[-0.03em] sm:text-[52px]">
          <span className="text-dust line-through decoration-2">{receipt.prev_display ?? "none"}</span>
          <span aria-label="changed to">→</span>
          <span>{receipt.curr_display ?? "none"}</span>
          {receipt.delta_pct !== null && (
            <span className="text-signal-light">{receipt.delta_pct > 0 ? "+" : "−"}{Math.abs(receipt.delta_pct)}%</span>
          )}
        </p>
      </div>

      <dl className="mt-6 grid gap-x-8 gap-y-4 sm:grid-cols-2">
        <div>
          <dt className="text-[14px] text-slate">Seen on</dt>
          <dd className="text-[17px]">{fmt(receipt.observed_at)}</dd>
        </div>
        <div>
          <dt className="text-[14px] text-slate">When it happened</dt>
          <dd className="text-[17px]">
            {receipt.published_at ? `Announced ${fmt(receipt.published_at)}` : between ? `Not announced on the page. It changed ${between}.` : "First seen in this check."}
          </dd>
        </div>
        <div className="min-w-0">
          <dt className="text-[14px] text-slate">Page checked</dt>
          <dd className="truncate text-[17px]"><a href={receipt.source_url} target="_blank" rel="noreferrer" className="text-link underline">{receipt.source_url}</a></dd>
        </div>
        <div>
          <dt className="text-[14px] text-slate">Status</dt>
          <dd className="text-[17px]">
            {receipt.status === "confirmed" ? "Confirmed by comparing the saved pages" : "Needs a second look: unusual change, no alert sent"}
          </dd>
        </div>
        {receipt.priority !== null && receipt.priority_breakdown && (
          <div className="sm:col-span-2">
            <dt className="text-[14px] text-slate">Priority</dt>
            <dd className="text-[17px]">
              <span className="font-medium">{receipt.priority} of 100 ({receipt.priority >= 70 ? "high" : receipt.priority >= 40 ? "medium" : "low"})</span>
              <span className="block text-[15px] text-charcoal">
                Size of change {Math.round(receipt.priority_breakdown.m * 100)}% · relevance {Math.round(receipt.priority_breakdown.r * 100)}% · source
                reliability {Math.round(receipt.priority_breakdown.s * 100)}%
                {receipt.priority_breakdown.undercut && ". Their price is now below your planned price."}
              </span>
            </dd>
          </div>
        )}
        {receipt.simulation_impact && (
          <div className="sm:col-span-2">
            <dt className="text-[14px] text-slate">Launch simulation</dt>
            <dd className="text-[17px]">
              <Link href={`/app/${profileId}/simulator`} className="text-link underline">
                Re-planned: recommended ₹{Number(receipt.simulation_impact.before).toLocaleString("en-IN")} → ₹{Number(receipt.simulation_impact.after).toLocaleString("en-IN")}
              </Link>
            </dd>
          </div>
        )}
        {receipt.wayback_url && (
          <div>
            <dt className="text-[14px] text-slate">Independent copy</dt>
            <dd className="text-[17px]"><a href={receipt.wayback_url} target="_blank" rel="noreferrer" className="text-link underline">Internet Archive capture</a></dd>
          </div>
        )}
      </dl>

      <h2 className="mt-10 text-[24px] font-medium tracking-[-0.02em]">The saved pages</h2>
      <p className="mt-1 text-charcoal">Text as captured on each check. The changed value is highlighted.</p>
      {!evidence ? (
        <div className="mt-4 h-48 rounded-btn bg-lifted" aria-busy="true" />
      ) : (
        <div className="mt-4 grid gap-4 lg:grid-cols-2">
          <Pane label="Before" side={evidence.before} sha={evidence.sha256.before} />
          <Pane label="After" side={evidence.after} sha={evidence.sha256.after} />
        </div>
      )}

      <div className="mt-10 flex flex-wrap items-center gap-4 rounded-btn border border-dust p-6">
        {receipt.muted ? (
          <>
            <p className="text-charcoal">Muted. Changes to this field for {receipt.competitor.name} won&apos;t alert you.</p>
            <button type="button" onClick={() => setRelevant(true)} className="rounded-pill border border-ink px-4 py-1.5 text-[14px] font-medium">Undo</button>
          </>
        ) : (
          <>
            <p className="text-charcoal">Not useful to you?</p>
            <button type="button" onClick={() => setRelevant(false)} className="rounded-pill border border-ink px-4 py-1.5 text-[14px] font-medium">Not relevant</button>
          </>
        )}
      </div>
    </section>
  );
}

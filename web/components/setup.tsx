"use client";

import Link from "next/link";
import { useCallback, useEffect, useState } from "react";
import { KIND_LABEL, type Kind } from "@/components/product-plan";
import { LoadError } from "@/components/ui";
import { api, type Job } from "@/lib/api";

export type Action = { label: string; href: string | null; kind: "link" | "price" | "discover" | "comparables" | "monitor" | "wait"; product_id?: string; product?: string; unit?: string; key?: string; why?: string };
type Step = { key: string; title: string; status: "done" | "todo" | "running" | "blocked" | "optional"; detail: string; action: Action | null };
export type Finding = { kind: string; basis: Kind; text: string; evidence: { label: string; href: string }; action: Action };
export type Coverage = { area: string; status: "ok" | "missing" | "failed" | "stale"; detail: string };
export type Since = { at: string; receipts: { id: string; text: string; observed_at: string }[]; mentions: number; runs: number; failed: number };
export type Setup = { steps: Step[]; findings: Finding[]; coverage: Coverage[]; next_action: Action; complete: boolean; since?: Since };
export const COV_LABEL: Record<Coverage["status"], string> = { ok: "Covered", missing: "Missing", failed: "Check failed", stale: "Out of date" };

const btn = "inline-flex min-h-11 items-center rounded-btn border-[1.5px] border-ink px-5 text-[16px] font-medium disabled:opacity-50";
const CHIP: Record<Step["status"], string> = { done: "Done", todo: "To do", running: "Working", blocked: "Blocked", optional: "Optional" };
const COV: Record<Coverage["status"], string> = { ok: "bg-ghost", missing: "bg-lifted text-slate", failed: "bg-signal/15 text-ink", stale: "bg-signal/10 text-ink" };

async function runJob(path: string, onNote: (s: string) => void): Promise<void> {
  const { job_id } = await api<{ job_id: string }>(path, { method: "POST", body: "{}" });
  for (let i = 0; i < 240; i++) {
    const job = await api<Job>(`/api/v1/jobs/${job_id}`);
    const last = job.steps[job.steps.length - 1];
    if (last?.detail) onNote(last.detail);
    if (job.status === "done") return;
    if (job.status === "failed" || job.status === "stale") throw new Error(job.error?.message ?? "This stopped early. Try again.");
    await new Promise((r) => setTimeout(r, 1500));
  }
  throw new Error("Still working. Come back in a minute; progress is saved.");
}

// Runs one setup action in place (link, price, discovery, comparables, first check), then reloads the plan.
function ActionControl({ profileId, action, primary, onDone }: { profileId: string; action: Action; primary?: boolean; onDone: () => void }) {
  const [busy, setBusy] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [price, setPrice] = useState("");
  const cls = `${btn} ${primary ? "bg-ink text-canvas" : "bg-white"}`;

  async function go(fn: () => Promise<unknown>, note: string) {
    setError(null);
    setBusy(note);
    try { await fn(); } catch (e) { setError((e as Error).message); }
    setBusy(null);
    onDone();
  }

  if (action.kind === "link" && action.href) return <Link href={action.href} className={cls}>{action.label}</Link>;
  if (action.kind === "wait") return <p className="text-[15px] text-charcoal">{action.label}…</p>;
  if (action.kind === "price")
    return (
      <form className="flex flex-wrap items-center gap-2" onSubmit={(e) => {
        e.preventDefault();
        go(() => api(`/api/v1/products/${action.product_id}`, { method: "PATCH", body: JSON.stringify({ price: Number(price) }) }), "Saving…");
      }}>
        <label className="sr-only" htmlFor={`price-${action.product_id}`}>Price of {action.product} in rupees</label>
        <span className="text-[17px]">₹</span>
        <input id={`price-${action.product_id}`} type="number" min={1} required value={price} onChange={(e) => setPrice(e.target.value)}
          className="w-32 rounded-[14px] border border-ink/30 bg-white px-4 py-2.5 text-[16px] text-ink" />
        <span className="text-[15px] text-slate">{action.unit && action.unit !== "one_time" ? `per ${action.unit}` : "each"}</span>
        <button disabled={busy !== null || !price} className={cls}>{busy ?? "Save price"}</button>
        {error && <p role="alert" className="w-full text-[15px] text-charcoal">{error}</p>}
      </form>
    );
  const path = action.kind === "discover" ? `/api/v1/profiles/${profileId}/discovery`
    : action.kind === "comparables" ? `/api/v1/products/${action.product_id}/comparables/find`
    : `/api/v1/profiles/${profileId}/monitoring/start`;
  return (
    <div className="grid gap-2">
      <button type="button" disabled={busy !== null} className={cls} onClick={() => go(() => runJob(path, setBusy), "Starting…")}>
        {busy ? "Working…" : action.label}
      </button>
      {busy && <p aria-live="polite" className="text-[15px] text-charcoal">{busy}</p>}
      {error && <p role="alert" className="text-[15px] text-charcoal">{error}</p>}
    </div>
  );
}

// since: the viewer's last visit (kept in this browser only), so the overview can say what is new.
export function useSetup(profileId: string, since?: string | null) {
  const [data, setData] = useState<Setup | null>(null);
  const [error, setError] = useState<string | null>(null);
  const load = useCallback(() => api<Setup>(`/api/v1/profiles/${profileId}/setup${since ? `?since=${encodeURIComponent(since)}` : ""}`)
    .then((d) => (setError(null), setData(d)), (e: Error) => setError(e.message)), [profileId, since]);
  useEffect(() => { load(); }, [load]);
  const running = data?.steps.some((s) => s.status === "running");
  useEffect(() => {
    if (!running) return;
    const t = setInterval(load, 5000);
    return () => clearInterval(t);
  }, [running, load]);
  return { data, error, load };
}

export function NextAction({ profileId, action, onDone }: { profileId: string; action: Action; onDone: () => void }) {
  return (
    <div data-testid="next-action" className="rounded-stadium bg-ink p-7 text-canvas">
      <p className="text-[15px] text-dust">Your next step</p>
      <p className="mt-1 text-[24px] font-medium leading-tight tracking-[-0.02em]">{action.label}</p>
      {action.why && <p className="mt-2 max-w-[44rem] text-[16px] text-dust">{action.why}</p>}
      <div className="mt-4 [&_a]:border-canvas [&_a]:bg-canvas [&_a]:text-ink [&_button]:border-canvas [&_button]:bg-canvas [&_button]:text-ink [&_p]:text-dust">
        <ActionControl key={action.label} profileId={profileId} action={action} onDone={onDone} />
      </div>
    </div>
  );
}

export function Findings({ findings, top = 3 }: { findings: Finding[]; top?: number }) {
  const [all, setAll] = useState(false);
  if (!findings.length)
    return <p className="rounded-btn bg-lifted p-6 text-charcoal">No conclusions yet. We only state a finding when enough real data supports it; the steps above say what is missing.</p>;
  return (
    <ul data-testid="findings" className="grid gap-3">
      {(all ? findings : findings.slice(0, top)).map((f, i) => (
        <li key={i} className="rounded-btn bg-lifted p-5">
          <p className="text-[17px]"><span className="mr-2 rounded-pill bg-white px-2 py-0.5 text-[12px] font-medium">{KIND_LABEL[f.basis]}</span>{f.text}</p>
          <p className="mt-2 flex flex-wrap gap-x-5 gap-y-1 text-[15px]">
            <Link href={f.evidence.href} className="text-link underline">Evidence: {f.evidence.label}</Link>
            {f.action.href && <Link href={f.action.href} className="font-medium underline">Next: {f.action.label}</Link>}
          </p>
        </li>
      ))}
      {findings.length > top && (
        <li><button type="button" onClick={() => setAll(!all)} className="text-[15px] font-medium underline">
          {all ? "Show fewer" : `Show ${findings.length - top} more`}
        </button></li>
      )}
    </ul>
  );
}

export function SinceLastVisit({ since, profileId }: { since: Since; profileId: string }) {
  const parts = [since.receipts.length && `${since.receipts.length} competitor change${since.receipts.length > 1 ? "s" : ""}`,
    since.mentions && `${since.mentions} new review${since.mentions > 1 ? "s" : ""} or comment${since.mentions > 1 ? "s" : ""}`,
    since.runs && `${since.runs} check${since.runs > 1 ? "s" : ""} run`, since.failed && `${since.failed} page${since.failed > 1 ? "s" : ""} couldn't be read`].filter(Boolean);
  return (
    <div data-testid="since" className="rounded-btn bg-lifted p-5 text-[15px]">
      <p className="font-medium">Since your last visit ({since.at})</p>
      <p className="mt-1 text-charcoal">{parts.length ? parts.join(" · ") : "Nothing new."}</p>
      {since.receipts.map((r) => (
        <Link key={r.id} href={`/app/${profileId}/receipt?id=${r.id}`} className="mt-1 block underline">{r.text} (seen {r.observed_at})</Link>
      ))}
    </div>
  );
}

export function CoverageStrip({ coverage }: { coverage: Coverage[] }) {
  return (
    <ul data-testid="coverage" className="grid gap-2 sm:grid-cols-2 lg:grid-cols-4">
      {coverage.map((c) => (
        <li key={c.area} className={`rounded-btn p-4 ${COV[c.status]}`}>
          <p className="text-[14px] font-medium">{c.area} · {COV_LABEL[c.status]}</p>
          <p className="mt-1 text-[14px]">{c.detail}</p>
        </li>
      ))}
    </ul>
  );
}

// Add a product or service by name or by its page (the page's name, price and description are read from it, robots.txt respected).
function AddProduct({ profileId, onDone }: { profileId: string; onDone: () => void }) {
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState<string | null>(null);
  const field = "mt-1 w-full rounded-[14px] border border-ink/30 bg-white px-4 py-2.5 text-[16px]";
  async function submit(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    const form = e.currentTarget;
    const f = new FormData(form);
    const what = String(f.get("what")).trim();
    const isUrl = /^https?:\/\//.test(what);
    setBusy(true);
    setMessage(null);
    await api<{ name: string; category_path: string | null }>(`/api/v1/profiles/${profileId}/products`, {
      method: "POST",
      body: JSON.stringify({ ...(isUrl ? { url: what } : { name: what }), target_customer: String(f.get("who")).trim() || null }),
    }).then((p) => (form.reset(), setMessage(`${p.name} added${p.category_path ? ` in ${p.category_path.split(" > ").pop()}` : ", without a product category"}.`)),
      (err: Error) => setMessage(err.message));
    setBusy(false);
    onDone();
  }
  return (
    <details className="rounded-btn bg-lifted p-5">
      <summary className="cursor-pointer text-[17px] font-medium">Add a product or service</summary>
      <form onSubmit={submit} className="mt-4 grid gap-3 md:grid-cols-[1.4fr_1fr_auto] md:items-end">
        <label className="text-[15px] font-medium">Name, or the link to its page<input name="what" required className={field} placeholder="Cold brew concentrate, or https://…" /></label>
        <label className="text-[15px] font-medium">Who it&apos;s for <span className="font-normal text-slate">(optional)</span><input name="who" className={field} placeholder="If different from your business" /></label>
        <button disabled={busy} className={`${btn} bg-ink text-canvas`}>{busy ? "Adding…" : "Add"}</button>
      </form>
      {message && <p role="status" className="mt-3 text-[15px] text-charcoal">{message}</p>}
    </details>
  );
}

// S-27: guided setup after onboarding. Every step reads from saved data, so it survives refresh, logout and login.
export function SetupView({ profileId }: { profileId: string }) {
  const { data, error, load } = useSetup(profileId);
  if (error && !data) return <LoadError what="your setup plan" message={error} onRetry={load} />;
  if (!data) return <div className="h-60 rounded-stadium bg-lifted" aria-busy="true" />;
  const required = data.steps.filter((s) => s.status !== "optional");
  const done = required.filter((s) => s.status === "done").length;

  return (
    <section data-screen="S-27" className="grid max-w-[60rem] gap-8">
      <div>
        <h1 className="text-[32px] leading-tight md:text-[40px]">Getting started</h1>
        <p className="mt-2 text-[17px] text-charcoal">{done} of {required.length} steps done. Each step uses real pages and your own data; nothing is guessed.</p>
      </div>
      <NextAction profileId={profileId} action={data.next_action} onDone={load} />

      <ol className="grid gap-3">
        {data.steps.map((s, i) => (
          <li key={s.key} data-step={s.key} data-status={s.status} className="grid gap-3 rounded-btn bg-lifted p-5 md:grid-cols-[1fr_auto] md:items-center">
            <div>
              <p className="flex flex-wrap items-center gap-2 text-[18px] font-medium">
                {i + 1}. {s.title}
                <span className={`rounded-pill px-2.5 py-0.5 text-[12px] font-medium ${s.status === "done" ? "bg-ghost" : s.status === "todo" ? "bg-ink text-canvas" : "bg-white text-charcoal"}`}>{CHIP[s.status]}</span>
              </p>
              <p className="mt-1 text-[15px] text-charcoal">{s.detail}</p>
            </div>
            {s.key === data.next_action.key && <span className="text-[15px] text-slate">Your next step, above</span>}
            {s.action && s.status !== "done" && s.key !== data.next_action.key && <ActionControl key={s.action.label} profileId={profileId} action={s.action} onDone={load} />}
            {s.action && s.status === "done" && s.action.href && <Link href={s.action.href} className="text-[15px] underline">{s.action.label}</Link>}
          </li>
        ))}
      </ol>

      <AddProduct profileId={profileId} onDone={load} />

      <div>
        <h2 className="text-[24px] font-medium tracking-[-0.02em]">What we found</h2>
        <div className="mt-3"><Findings findings={data.findings} /></div>
      </div>
      <div>
        <h2 className="text-[24px] font-medium tracking-[-0.02em]">Data coverage</h2>
        <div className="mt-3"><CoverageStrip coverage={data.coverage} /></div>
      </div>
      <Link href={`/app/${profileId}/home`} className={`${btn} w-fit bg-white`}>Go to the overview</Link>
    </section>
  );
}

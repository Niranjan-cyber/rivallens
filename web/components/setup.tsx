"use client";

import Link from "next/link";
import { useCallback, useEffect, useState } from "react";
import { api, type Job } from "@/lib/api";

export type Action = { label: string; href: string | null; kind: "link" | "price" | "discover" | "comparables" | "monitor" | "wait"; product_id?: string; product?: string; unit?: string; key?: string; why?: string };
type Step = { key: string; title: string; status: "done" | "todo" | "running" | "blocked" | "optional"; detail: string; action: Action | null };
export type Finding = { kind: string; text: string; evidence: { label: string; href: string }; action: Action };
export type Coverage = { area: string; status: "ok" | "missing" | "failed"; detail: string };
export type Setup = { steps: Step[]; findings: Finding[]; coverage: Coverage[]; next_action: Action; complete: boolean };

const btn = "inline-flex min-h-11 items-center rounded-btn border-[1.5px] border-ink px-5 text-[16px] font-medium disabled:opacity-50";
const CHIP: Record<Step["status"], string> = { done: "Done", todo: "To do", running: "Working", blocked: "Blocked", optional: "Optional" };
const COV: Record<Coverage["status"], string> = { ok: "bg-ghost", missing: "bg-lifted text-slate", failed: "bg-signal/15 text-ink" };

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
          className="w-32 rounded-[14px] border border-ink/30 bg-white px-4 py-2.5 text-[16px]" />
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

export function useSetup(profileId: string) {
  const [data, setData] = useState<Setup | null>(null);
  const [error, setError] = useState<string | null>(null);
  const load = useCallback(() => api<Setup>(`/api/v1/profiles/${profileId}/setup`).then(setData, (e: Error) => setError(e.message)), [profileId]);
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

export function Findings({ findings }: { findings: Finding[] }) {
  if (!findings.length)
    return <p className="rounded-btn bg-lifted p-6 text-charcoal">No conclusions yet. We only state a finding when enough real data supports it; the steps above say what is missing.</p>;
  return (
    <ul data-testid="findings" className="grid gap-3">
      {findings.map((f, i) => (
        <li key={i} className="rounded-btn bg-lifted p-5">
          <p className="text-[17px]">{f.text}</p>
          <p className="mt-2 flex flex-wrap gap-x-5 gap-y-1 text-[15px]">
            <Link href={f.evidence.href} className="text-link underline">Evidence: {f.evidence.label}</Link>
            {f.action.href && <Link href={f.action.href} className="font-medium underline">Next: {f.action.label}</Link>}
          </p>
        </li>
      ))}
    </ul>
  );
}

export function CoverageStrip({ coverage }: { coverage: Coverage[] }) {
  return (
    <ul data-testid="coverage" className="grid gap-2 sm:grid-cols-2 lg:grid-cols-4">
      {coverage.map((c) => (
        <li key={c.area} className={`rounded-btn p-4 ${COV[c.status]}`}>
          <p className="text-[14px] font-medium">{c.area} · {c.status === "ok" ? "Covered" : c.status === "failed" ? "Check failed" : "Missing"}</p>
          <p className="mt-1 text-[14px]">{c.detail}</p>
        </li>
      ))}
    </ul>
  );
}

// S-27: guided setup after onboarding. Every step reads from saved data, so it survives refresh, logout and login.
export function SetupView({ profileId }: { profileId: string }) {
  const { data, error, load } = useSetup(profileId);
  if (error) return <p className="rounded-btn bg-lifted p-6">{error}</p>;
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
            {s.action && s.status !== "done" && <ActionControl key={s.action.label} profileId={profileId} action={s.action} onDone={load} />}
            {s.action && s.status === "done" && s.action.href && <Link href={s.action.href} className="text-[15px] underline">{s.action.label}</Link>}
          </li>
        ))}
      </ol>

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

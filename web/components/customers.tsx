"use client";

import { useCallback, useEffect, useState, type FormEvent } from "react";
import { LoadError } from "@/components/ui";
import { api, type Job } from "@/lib/api";

type Quote = { id: string; text: string; rating: number | null; date: string | null; author: string | null; url: string | null; source: string; source_type: string; sentiment: string | null };
type Theme = { label: string; kind: "request" | "complaint" | "praise"; count: number; mention_ids: string[]; quotes: Quote[] };
type Data = {
  total: number; sentiment: Record<string, number>; avg_rating: number | null; rated: number; themes: Theme[]; analysed: number; ai: boolean | null; analysed_at: string | null;
  sources: { source: string; source_type: string; rows: number }[]; recent: Omit<Quote, "id">[];
  metrics: { metric: string; source: string; first: number; last: number; first_date: string; last_date: string; points: number }[];
};
type Preview = { filename: string; headers: string[]; rows: number; kind: "reviews" | "metrics"; mapping: Record<string, string>; metrics: string[];
  sample: { text: string; rating: number | null; date: string | null }[] };

const GROUP = [["request", "What customers ask for"], ["complaint", "What they complain about"], ["praise", "What they praise"]] as const;
const SOURCE = { upload: "Upload", own_site: "Your product page", web: "Web mention" } as Record<string, string>;
const input = "w-full rounded-[14px] border border-ink/30 bg-white px-3 py-2 text-[15px] focus:border-ink focus:outline-none";
const FIELDS: Record<string, string> = { text: "Review or comment text", rating: "Rating (1–5)", date: "Date", author: "Author", title: "Title", url: "Link", product: "Product" };

async function waitFor(jobId: string, onStep: (s: string) => void) {
  for (let i = 0; i < 90; i++) {
    const job = await api<Job>(`/api/v1/jobs/${jobId}`);
    const last = job.steps?.[job.steps.length - 1];
    if (last?.detail) onStep(last.detail);
    if (["done", "failed", "stale"].includes(job.status)) return job;
    await new Promise((r) => setTimeout(r, 2500));
  }
}

// S-26: what customers say and want. Every theme opens the quotes it is based on.
export function Customers({ profileId }: { profileId: string }) {
  const [data, setData] = useState<Data | null>(null);
  const [status, setStatus] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const load = useCallback(() => api<Data>(`/api/v1/profiles/${profileId}/customers`).then((d) => (setError(null), setData(d)), (e: Error) => setError(e.message)), [profileId]);
  useEffect(() => { load(); }, [load]);

  async function collect() {
    setStatus("Starting…");
    try {
      const { job_id } = await api<{ job_id: string }>(`/api/v1/profiles/${profileId}/customers/collect`, { method: "POST" });
      await waitFor(job_id, setStatus);
      setStatus(null);
    } catch (e) {
      setStatus((e as Error).message);
    }
    load();
  }

  if (error && !data) return <LoadError what="customer data" message={error} onRetry={load} />;
  if (!data) return <div className="h-40 rounded-stadium bg-lifted" aria-busy="true" />;
  const s = data.sentiment;
  const judged = (s.positive ?? 0) + (s.neutral ?? 0) + (s.negative ?? 0);

  return (
    <section data-screen="S-26">
      <h1 className="text-[32px] leading-tight md:text-[40px]">Customers</h1>
      <p className="mt-3 max-w-[44rem] text-[17px] text-charcoal">
        What customers say, from your review and comment exports, the reviews on your product pages and public web mentions. Each theme shows the quotes it comes from.
      </p>

      {data.total === 0 ? (
        <p className="mt-6 rounded-stadium bg-lifted p-7 text-charcoal">No customer data yet. Upload a reviews or comments export below, or collect from your product pages and the web.</p>
      ) : (
        <div className="mt-6 grid gap-4 md:grid-cols-3">
          <div className="rounded-stadium bg-lifted p-6">
            <p className="text-[14px] text-slate">Mentions</p>
            <p className="mt-1 text-[28px] font-medium tracking-[-0.02em]">{data.total.toLocaleString("en-IN")}</p>
            <p className="mt-1 text-[14px] text-charcoal">{data.sources.length} source{data.sources.length === 1 ? "" : "s"}{data.analysed ? `; latest ${data.analysed} analysed` : ""}</p>
          </div>
          <div className="rounded-stadium bg-lifted p-6">
            <p className="text-[14px] text-slate">Average rating</p>
            <p className="mt-1 text-[28px] font-medium tracking-[-0.02em]">{data.avg_rating != null ? `${data.avg_rating} / 5` : "—"}</p>
            <p className="mt-1 text-[14px] text-charcoal">{data.rated} rated mention{data.rated === 1 ? "" : "s"}</p>
          </div>
          <div className="rounded-stadium bg-lifted p-6">
            <p className="text-[14px] text-slate">Sentiment</p>
            {judged > 0 ? (
              <>
                <div className="mt-3 flex h-3 overflow-hidden rounded-full" role="img" aria-label={`${s.positive ?? 0} positive, ${s.neutral ?? 0} neutral, ${s.negative ?? 0} negative`}>
                  <span style={{ width: `${((s.positive ?? 0) / judged) * 100}%` }} className="bg-ink" />
                  <span style={{ width: `${((s.neutral ?? 0) / judged) * 100}%` }} className="bg-dust" />
                  <span style={{ width: `${((s.negative ?? 0) / judged) * 100}%` }} className="bg-clay" />
                </div>
                <p className="mt-2 text-[14px] text-charcoal">{s.positive ?? 0} positive · {s.neutral ?? 0} neutral · {s.negative ?? 0} negative</p>
              </>
            ) : <p className="mt-1 text-charcoal">Not analysed yet</p>}
          </div>
        </div>
      )}

      {data.themes.length > 0 && (
        <div className="mt-8 grid gap-4 lg:grid-cols-3">
          {GROUP.map(([kind, title]) => {
            const themes = data.themes.filter((t) => t.kind === kind);
            return (
              <div key={kind} className="rounded-stadium bg-lifted p-6">
                <h2 className="text-[20px] font-medium tracking-[-0.02em]">{title}</h2>
                {themes.length === 0 ? <p className="mt-2 text-[14px] text-slate">Nothing yet.</p> : (
                  <ul className="mt-3 grid gap-3">
                    {themes.map((t) => (
                      <li key={t.label}>
                        <details>
                          <summary className="cursor-pointer text-[16px]"><span className="font-medium">{t.label}</span> <span className="text-slate">· {t.count} mention{t.count === 1 ? "" : "s"}</span></summary>
                          <ul className="mt-2 grid gap-2">
                            {t.quotes.map((q) => (
                              <li key={q.id} className="rounded-[14px] bg-white p-3 text-[14px]">
                                <p>&ldquo;{q.text.length > 240 ? `${q.text.slice(0, 240)}…` : q.text}&rdquo;</p>
                                <p className="mt-1 text-[12px] text-slate">
                                  {q.rating != null ? `${q.rating}★ · ` : ""}{q.author ? `${q.author} · ` : ""}{q.date ? `${q.date} · ` : ""}
                                  {q.url ? <a className="underline" href={q.url} target="_blank" rel="noreferrer">{SOURCE[q.source_type]}</a> : `${SOURCE[q.source_type]}: ${q.source}`}
                                </p>
                              </li>
                            ))}
                          </ul>
                        </details>
                      </li>
                    ))}
                  </ul>
                )}
              </div>
            );
          })}
        </div>
      )}
      {data.ai === false && data.total > 0 && <p className="mt-3 text-[14px] text-slate">The AI was busy, so sentiment comes from star ratings only; themes appear on the next analysis.</p>}

      {data.metrics.length > 0 && (
        <div className="mt-8 rounded-stadium bg-lifted p-6">
          <h2 className="text-[20px] font-medium tracking-[-0.02em]">Social media</h2>
          <ul className="mt-3 grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
            {data.metrics.map((m) => {
              const change = m.first ? ((m.last - m.first) / m.first) * 100 : null;
              return (
                <li key={m.source + m.metric} className="rounded-[18px] bg-white p-4">
                  <p className="text-[14px] text-slate">{m.metric}</p>
                  <p className="text-[24px] font-medium">{m.last.toLocaleString("en-IN")}</p>
                  <p className="text-[13px] text-charcoal">{change != null ? `${change >= 0 ? "+" : "−"}${Math.abs(change).toFixed(0)}% since ${m.first_date}` : `since ${m.first_date}`}</p>
                  <p className="text-[12px] text-slate">{m.source}</p>
                </li>
              );
            })}
          </ul>
        </div>
      )}

      <div className="mt-8 grid gap-4 lg:grid-cols-2">
        <Upload profileId={profileId} onDone={load} />
        <div className="rounded-stadium bg-lifted p-6">
          <h2 className="text-[20px] font-medium tracking-[-0.02em]">Collect from your pages and the web</h2>
          <p className="mt-1 text-[14px] text-charcoal">Reads the reviews published on your product pages (robots.txt respected) and searches public web pages that mention your business by name. Social networks aren&apos;t read; upload their exports instead.</p>
          <button type="button" onClick={collect} disabled={status !== null}
            className="mt-3 inline-flex min-h-11 items-center rounded-btn border-[1.5px] border-ink bg-ink px-5 text-[15px] font-medium text-canvas disabled:opacity-60">
            {status ?? "Collect mentions"}
          </button>
          {data.sources.length > 0 && (
            <ul className="mt-4 grid gap-1 text-[14px]">
              {data.sources.map((x) => (
                <li key={x.source} className="flex justify-between gap-2">
                  <span className="truncate">{SOURCE[x.source_type]}: {x.source} ({x.rows})</span>
                  <button type="button" className="shrink-0 text-slate underline" onClick={() => api(`/api/v1/profiles/${profileId}/customers/sources/${encodeURIComponent(x.source)}`, { method: "DELETE" }).then(load)}>Remove</button>
                </li>
              ))}
            </ul>
          )}
        </div>
      </div>
    </section>
  );
}

function Upload({ profileId, onDone }: { profileId: string; onDone: () => void }) {
  const [file, setFile] = useState<File | null>(null);
  const [preview, setPreview] = useState<Preview | null>(null);
  const [mapping, setMapping] = useState<Record<string, string>>({});
  const [msg, setMsg] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  async function look(f: File) {
    setFile(f);
    setMsg(null);
    const fd = new FormData();
    fd.append("file", f);
    await api<Preview>(`/api/v1/profiles/${profileId}/customers/preview`, { method: "POST", body: fd }).then((p) => (setPreview(p), setMapping(p.mapping)), (e: Error) => setMsg(e.message));
  }
  async function importFile(e: FormEvent) {
    e.preventDefault();
    if (!file || !preview) return;
    const fd = new FormData();
    fd.append("file", file);
    fd.append("mapping", JSON.stringify(mapping));
    fd.append("kind", preview.kind);
    setBusy(true);
    try {
      const r = await api<{ imported: number; job_id: string | null }>(`/api/v1/profiles/${profileId}/customers/import`, { method: "POST", body: fd });
      setPreview(null);
      if (r.job_id) {
        setMsg(`Imported ${r.imported}. Finding themes…`);
        onDone();
        await waitFor(r.job_id, () => {});
      }
      setMsg(`Imported ${r.imported} ${preview.kind === "reviews" ? "mentions" : "data points"}.`);
      onDone();
    } catch (err) {
      setMsg((err as Error).message);
    }
    setBusy(false);
  }

  return (
    <div className="rounded-stadium bg-lifted p-6">
      <h2 className="text-[20px] font-medium tracking-[-0.02em]">Upload reviews, comments or insights</h2>
      <p className="mt-1 text-[14px] text-charcoal">CSV or Excel: review exports (Google Business, Play Console, your store), comment exports, or insight exports from Meta Business Suite, LinkedIn and YouTube Studio.</p>
      <label className="mt-3 block text-[15px] font-medium">File
        <input type="file" accept=".csv,.xlsx,.xlsm,.txt" className="mt-1 block w-full text-[15px]" onChange={(e) => e.target.files?.[0] && look(e.target.files[0])} />
      </label>
      {preview && (
        <form onSubmit={importFile} className="mt-4 grid gap-2">
          <p className="text-[14px] text-slate">{preview.rows} rows. {preview.kind === "reviews" ? "Read as reviews or comments; check the columns." : `Read as insights: ${preview.metrics.join(", ") || "no numeric columns found"}.`}</p>
          {preview.kind === "reviews" && Object.keys(FIELDS).map((f) => (
            <label key={f} className="grid grid-cols-[10rem_1fr] items-center gap-2 text-[14px]">{FIELDS[f]}
              <select className={input} value={mapping[f] ?? ""} onChange={(e) => setMapping((m) => { const n = { ...m }; if (e.target.value) n[f] = e.target.value; else delete n[f]; return n; })}>
                <option value="">Not in this file</option>
                {preview.headers.map((h) => <option key={h}>{h}</option>)}
              </select>
            </label>
          ))}
          {preview.sample.length > 0 && <p className="rounded-[14px] bg-white p-3 text-[13px]">&ldquo;{preview.sample[0].text.slice(0, 160)}…&rdquo;</p>}
          <button disabled={busy} className="inline-flex min-h-11 w-fit items-center rounded-btn border-[1.5px] border-ink bg-ink px-6 text-[16px] font-medium text-canvas disabled:opacity-60">Import {preview.rows} rows</button>
        </form>
      )}
      {msg && <p role="status" className="mt-3 text-[14px]">{msg}</p>}
    </div>
  );
}

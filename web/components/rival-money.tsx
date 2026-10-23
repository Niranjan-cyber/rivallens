"use client";

import { useCallback, useEffect, useState, type FormEvent } from "react";
import { inr } from "@/components/money";
import { api, type Job } from "@/lib/api";

type Fact = { company: string; kind: "revenue" | "profit" | "funding"; amount_inr: number; period: string | null; round: string | null;
  event_date: string | null; quote: string; source_url: string; source_title: string | null; added_by_user: boolean; observed_at: string };

const KIND = { revenue: "Revenue", profit: "Profit", funding: "Funding" } as const;
const input = "w-full rounded-[14px] border border-ink/30 bg-white px-3 py-2 text-[15px] focus:border-ink focus:outline-none";
const host = (u: string) => { try { return new URL(u).hostname.replace(/^www\./, ""); } catch { return u; } };

// B14f on S-24: competitors' reported revenue, profit and funding. Every figure is a quote from a linked source, or Unknown.
export function RivalMoney({ profileId }: { profileId: string }) {
  const [data, setData] = useState<{ companies: string[]; facts: Fact[] } | null>(null);
  const [status, setStatus] = useState<string | null>(null);
  const [extra, setExtra] = useState("");
  const load = useCallback(() => api<{ companies: string[]; facts: Fact[] }>(`/api/v1/profiles/${profileId}/money/rivals`).then(setData, () => {}), [profileId]);
  useEffect(() => { load(); }, [load]);

  async function find() {
    setStatus("Starting…");
    const companies = [...(data?.companies ?? []), ...extra.split(",").map((s) => s.trim()).filter(Boolean)];
    try {
      const { job_id } = await api<{ job_id: string }>(`/api/v1/profiles/${profileId}/money/rivals/find`, { method: "POST", body: JSON.stringify({ companies }) });
      for (let i = 0; i < 120; i++) {
        const job = await api<Job>(`/api/v1/jobs/${job_id}`);
        const last = job.steps?.[job.steps.length - 1];
        if (last?.detail) setStatus(last.detail);
        if (job.status === "done" || job.status === "failed" || job.status === "stale") break;
        await new Promise((r) => setTimeout(r, 2500));
      }
    } catch (e) {
      setStatus((e as Error).message);
      return;
    }
    setStatus(null);
    setExtra("");
    load();
  }

  async function add(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    const form = e.currentTarget;
    const f = new FormData(form);
    const s = (k: string) => String(f.get(k) ?? "").trim();
    await api(`/api/v1/profiles/${profileId}/money/rivals/facts`, { method: "POST", body: JSON.stringify({
      company: s("company"), kind: s("kind"), amount_inr: Number(s("amount")) * Number(s("unit")), period: s("period") || null, source_url: s("source_url") }) })
      .then(() => (form.reset(), load()), (err: Error) => setStatus(err.message));
  }

  if (!data) return null;
  const companies = Array.from(new Set([...data.companies, ...data.facts.map((f) => f.company)]));
  return (
    <div className="mt-8 rounded-stadium bg-lifted p-6">
      <h2 className="text-[20px] font-medium tracking-[-0.02em]">Competitors&apos; revenue and funding</h2>
      <p className="mt-1 max-w-[44rem] text-[14px] text-charcoal">
        From results, filings and funding news. A figure is kept only if the exact quote is in its source and the amount matches; everything else stays Unknown.
      </p>
      <div className="mt-3 flex flex-wrap items-center gap-2">
        <input value={extra} onChange={(e) => setExtra(e.target.value)} placeholder="Add companies, comma-separated" aria-label="More companies" className={`${input} max-w-xs`} />
        <button type="button" onClick={find} disabled={status !== null}
          className="inline-flex min-h-11 items-center rounded-btn border-[1.5px] border-ink bg-ink px-5 text-[15px] font-medium text-canvas disabled:opacity-60">
          {status ?? "Find revenue and funding"}
        </button>
      </div>
      {companies.length === 0 ? (
        <p className="mt-4 text-[15px] text-charcoal">Add products or competitors first, or type company names above.</p>
      ) : (
        <ul className="mt-4 grid gap-3 md:grid-cols-2">
          {companies.map((c) => {
            const facts = data.facts.filter((f) => f.company.toLowerCase() === c.toLowerCase());
            return (
              <li key={c} className="rounded-[20px] bg-white p-5">
                <p className="text-[17px] font-medium">{c}</p>
                {facts.length === 0 ? <p className="mt-1 text-[14px] text-slate">Revenue and funding: Unknown</p> : facts.slice(0, 4).map((f, i) => (
                  <div key={i} className="mt-3 border-t border-ink/10 pt-3 text-[14px]">
                    <p><span className="font-medium">{KIND[f.kind]} {inr(f.amount_inr)}</span>{f.period ? ` · ${f.period}` : ""}{f.round ? ` · ${f.round}` : ""}{f.event_date ? ` · ${f.event_date}` : ""}</p>
                    {!f.added_by_user && <p className="mt-1 text-charcoal">&ldquo;{f.quote}&rdquo;</p>}
                    <p className="mt-1 text-[13px] text-slate">
                      <a className="underline" href={f.source_url} target="_blank" rel="noreferrer">{host(f.source_url)}</a>
                      {f.added_by_user ? " · added by you" : ""} · seen {new Date(f.observed_at).toLocaleDateString("en-IN", { dateStyle: "medium" })}
                    </p>
                  </div>
                ))}
              </li>
            );
          })}
        </ul>
      )}
      <form onSubmit={add} className="mt-4 grid gap-2 sm:grid-cols-[1.2fr_0.9fr_0.8fr_0.7fr_0.8fr_1.6fr_auto]">
        <input name="company" required placeholder="Company" aria-label="Company" className={input} />
        <select name="kind" aria-label="Figure" className={input}><option value="revenue">Revenue</option><option value="profit">Profit</option><option value="funding">Funding</option></select>
        <input name="amount" type="number" step="any" min={0} required placeholder="Amount" aria-label="Amount" className={input} />
        <select name="unit" aria-label="Unit" className={input}><option value="10000000">crore</option><option value="100000">lakh</option><option value="1">₹</option></select>
        <input name="period" placeholder="FY26" aria-label="Period" className={input} />
        <input name="source_url" type="url" required placeholder="Source link" aria-label="Source link" className={input} />
        <button className="rounded-btn border-[1.5px] border-ink px-4 font-medium">Add</button>
      </form>
    </div>
  );
}

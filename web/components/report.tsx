"use client";

import { useEffect, useState } from "react";
import { api, type Job } from "@/lib/api";

type Claim = { id: string; text: string; evidence: { type: "receipt" | "observation" | "simulation"; id: string; observed_at: string | null; source_url: string | null } };
type Report = {
  id: string; generated_at: string; range: { from: string; to: string }; summary: string | null; summary_unavailable: boolean;
  sections: { title: string; claims: Claim[] }[]; suggestions: { text: string; claim_ids: string[]; label: string }[]; limitations: string[];
};

const day = (ts: string) => new Date(ts).toLocaleDateString("en-IN", { day: "numeric", month: "short", year: "numeric" });

// S-15: a shareable report where every claim cites its evidence; Download PDF uses the browser's print-to-PDF.
export function ReportView({ profileId }: { profileId: string }) {
  const [report, setReport] = useState<Report | null | undefined>(undefined);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api<Report | null>(`/api/v1/profiles/${profileId}/reports/latest`).then(setReport, (e: Error) => setError(e.message));
  }, [profileId]);

  async function generate() {
    setBusy(true);
    setError(null);
    try {
      const { job_id } = await api<{ job_id: string }>(`/api/v1/profiles/${profileId}/reports`, { method: "POST", body: "{}" });
      for (let i = 0; i < 60; i++) {
        const job = await api<Job & { result: { report_id?: string } | null }>(`/api/v1/jobs/${job_id}`);
        if (job.status === "done" && job.result?.report_id) {
          setReport(await api<Report>(`/api/v1/reports/${job.result.report_id}`));
          break;
        }
        if (job.status === "failed" || job.status === "stale") throw new Error(job.error?.message ?? "The report couldn't be built.");
        await new Promise((r) => setTimeout(r, 1000));
      }
    } catch (e) {
      setError((e as Error).message);
    }
    setBusy(false);
  }

  const href = (c: Claim) =>
    c.evidence.type === "receipt" ? `${window.location.origin}/app/${profileId}/receipt?id=${c.evidence.id}` : (c.evidence.source_url ?? "#");

  return (
    <section data-screen="S-15">
      <div className="flex flex-wrap items-center justify-between gap-3 print:hidden">
        <h1 className="text-[32px] leading-tight md:text-[40px]">Reports</h1>
        <div className="flex gap-3">
          <button type="button" onClick={generate} disabled={busy}
            className="inline-flex min-h-11 items-center rounded-btn border-[1.5px] border-ink bg-white px-6 text-[16px] font-medium disabled:opacity-50">
            {busy ? "Building…" : report ? "Regenerate" : "Generate report"}
          </button>
          {report && (
            <button type="button" onClick={() => window.print()}
              className="inline-flex min-h-11 items-center rounded-btn border-[1.5px] border-ink bg-ink px-6 text-[16px] font-medium text-canvas">
              Download PDF
            </button>
          )}
        </div>
      </div>
      <p className="mt-2 text-[15px] text-slate print:hidden">Last 30 days. Download PDF opens your browser&apos;s print dialog: choose “Save as PDF”. Links and dates are kept.</p>
      {error && <p className="mt-4 rounded-btn bg-lifted p-4 text-charcoal">{error}</p>}

      {report === undefined ? (
        <div className="mt-6 h-64 rounded-stadium bg-lifted" aria-busy="true" />
      ) : report === null ? (
        <p className="mt-6 rounded-btn bg-lifted p-6 text-charcoal">No report yet. Generate one to get a summary where every fact links to its evidence.</p>
      ) : (
        <article className="mt-6 rounded-stadium bg-white p-7 sm:p-10 print:rounded-none print:p-0">
          <header className="border-b border-dust pb-5">
            <p className="text-[14px] text-slate">RivalLens evidence report · demo data, fictional companies marked (demo)</p>
            <h2 className="mt-1 text-[30px] font-medium leading-tight tracking-[-0.02em]">Competitor changes, {day(report.range.from)} to {day(report.range.to)}</h2>
            <p className="mt-1 text-[14px] text-slate">Generated {new Date(report.generated_at).toLocaleString("en-IN", { dateStyle: "medium", timeStyle: "short" })}</p>
          </header>

          <h3 className="mt-6 text-[20px] font-medium">Summary</h3>
          {report.summary_unavailable || !report.summary ? (
            <p className="mt-1 text-slate">Summary unavailable: the AI summariser didn&apos;t respond. Every fact below is still cited.</p>
          ) : (
            <p className="mt-1 max-w-[46rem] text-[16px] leading-relaxed">{report.summary} <span className="text-[13px] text-slate">(AI-written from the claims below)</span></p>
          )}

          {report.sections.map((s) => (
            <section key={s.title} className="mt-7 break-inside-avoid">
              <h3 className="text-[20px] font-medium">{s.title}</h3>
              {s.claims.length === 0 ? <p className="mt-1 text-slate">Nothing with evidence in this period.</p> : (
                <ol className="mt-2 grid gap-2">
                  {s.claims.map((c) => (
                    <li key={c.id} id={c.id} className="grid grid-cols-[2.5rem_1fr] gap-2 text-[16px]">
                      <span className="text-[13px] text-slate">[{c.id}]</span>
                      <span>
                        {c.text}{" "}
                        <a href={href(c)} className="text-[14px] text-link underline">
                          {c.evidence.type === "receipt" ? "receipt" : "source"}{c.evidence.observed_at ? `, seen ${day(c.evidence.observed_at)}` : ""}
                        </a>
                      </span>
                    </li>
                  ))}
                </ol>
              )}
            </section>
          ))}

          {report.suggestions.length > 0 && (
            <section className="mt-7 break-inside-avoid rounded-btn border border-dust p-5">
              <h3 className="text-[20px] font-medium">AI suggestions <span className="text-[14px] font-normal text-slate">(not facts: each cites the claims it rests on)</span></h3>
              <ul className="mt-2 grid gap-2">
                {report.suggestions.map((s, i) => (
                  <li key={i} className="text-[16px]">
                    {s.text} <span className="text-[14px] text-slate">{s.claim_ids.map((id) => <a key={id} href={`#${id}`} className="mr-1 underline">[{id}]</a>)}</span>
                  </li>
                ))}
              </ul>
            </section>
          )}

          {report.limitations.length > 0 && (
            <section className="mt-7 break-inside-avoid">
              <h3 className="text-[20px] font-medium">Data limitations</h3>
              <ul className="mt-2 list-disc pl-5 text-[15px] text-charcoal">{report.limitations.map((l) => <li key={l}>{l}</li>)}</ul>
            </section>
          )}
        </article>
      )}
    </section>
  );
}

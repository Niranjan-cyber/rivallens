"use client";

import { useCallback, useEffect, useState, type FormEvent, type ReactNode } from "react";
import { RivalMoney } from "@/components/rival-money";
import { LoadError } from "@/components/ui";
import { api } from "@/lib/api";

type Month = { month: string; revenue: number; expenses: number };
type Bench = { industry: string; firms: number; gross_margin: number | null; operating_margin: number | null; net_margin: number | null };
type Money = {
  cash: number | null; cash_as_of: string | null; industry: string | null; industry_guessed: boolean; benchmark: Bench | null;
  metrics: {
    months: Month[]; monthly_revenue: number; monthly_expenses: number | null; operating_margin: number | null; monthly_burn: number;
    runway_months: number | null; funding_total: number; products: { product: string; units: number; revenue: number; avg_price: number | null }[];
  };
  transactions_count: number;
  recent: { date: string; kind: string; amount: number; product: string | null; quantity: number | null; description: string | null; source: string }[];
  sources: { source: string; rows: number; first: string; last: string }[];
  industries: string[];
};
type Preview = { filename: string; headers: string[]; rows: number; mapping: Record<string, string>; raw_sample: Record<string, string>[];
  parsed_sample: { date: string; kind: string; amount: number; product: string | null; description: string | null }[] };

export const inr = (v: number | null | undefined) => {
  if (v == null) return "—";
  const a = Math.abs(v);
  const s = a >= 1e7 ? `₹${(a / 1e7).toFixed(2)} cr` : a >= 1e5 ? `₹${(a / 1e5).toFixed(2)} L` : `₹${Math.round(a).toLocaleString("en-IN")}`;
  return v < 0 ? `−${s}` : s;
};
const pct = (v: number | null | undefined) => (v == null ? "Unknown" : `${(v * 100).toFixed(1)}%`);
const input = "w-full rounded-[14px] border border-ink/30 bg-white px-4 py-2.5 text-[16px] focus:border-ink focus:outline-none";
const FIELD_LABEL: Record<string, string> = { date: "Date", amount: "Amount", credit: "Money in (credit)", debit: "Money out (debit)", quantity: "Quantity",
  unit_price: "Unit price", product: "Product", description: "Description", kind: "Type (sale / expense / funding)" };

// S-24: the business's own money, from its exports or manual entries, against the Indian industry benchmark.
export function MoneyDashboard({ profileId }: { profileId: string }) {
  const [data, setData] = useState<Money | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [saveError, setSaveError] = useState<string | null>(null);
  const load = useCallback(() => api<Money>(`/api/v1/profiles/${profileId}/money`).then((d) => (setError(null), setData(d)), (e: Error) => setError(e.message)), [profileId]);
  useEffect(() => { load(); }, [load]);

  async function saveSettings(patch: { cash?: number | null; industry?: string | null }) {
    setSaveError(null);
    await api(`/api/v1/profiles/${profileId}/money/settings`, { method: "PUT", body: JSON.stringify({ cash: data?.cash ?? null, industry: data?.industry ?? null, ...patch }) })
      .then(load, (e: Error) => setSaveError(`Not saved: ${e.message}`));
  }

  if (!data) return error ? <LoadError what="your finance data" message={error} onRetry={load} /> : <div className="h-40 rounded-stadium bg-lifted" aria-busy="true" />;
  const m = data.metrics;
  const b = data.benchmark;
  const marginGap = m.operating_margin != null && b?.operating_margin != null ? m.operating_margin - b.operating_margin : null;

  return (
    <section data-screen="S-24">
      <h1 className="text-[32px] leading-tight md:text-[40px]">Finance</h1>
      <p className="mt-3 max-w-[44rem] text-[17px] text-charcoal">
        From your own exports and entries. Averages use your last three months; the benchmark is Damodaran&apos;s margins by industry for listed Indian companies (Jan 2026).
      </p>

      {data.transactions_count === 0 ? (
        <p className="mt-6 rounded-stadium bg-lifted p-7 text-charcoal">No money data yet. Upload a bank statement, payment gateway or store export below, or add entries by hand.</p>
      ) : (
        <div className="mt-6 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          <Stat label="Revenue per month" value={inr(m.monthly_revenue)} note={m.monthly_expenses != null ? `Expenses ${inr(m.monthly_expenses)} per month` : "No costs uploaded yet"} />
          <Stat label="Operating margin" value={pct(m.operating_margin)}
            note={b ? `${b.industry} in India: ${pct(b.operating_margin)} (${b.firms} listed firms)${marginGap != null ? `, you are ${marginGap >= 0 ? "above" : "below"} by ${pct(Math.abs(marginGap))}` : ""}` : "Pick your industry for a benchmark"} />
          {m.monthly_burn == null || m.monthly_expenses == null ? (
            <Stat label="Burn per month" value="Unknown" note="Upload a bank statement or add expenses to see margin, burn and runway" />
          ) : (
            <Stat label={m.monthly_burn ? "Burn per month" : "Monthly result"} value={m.monthly_burn ? inr(m.monthly_burn) : inr(m.monthly_revenue - m.monthly_expenses)}
              note={m.monthly_burn ? "Expenses above revenue" : "Revenue covers expenses"} />
          )}
          <Stat label="Runway" value={m.runway_months != null ? `${m.runway_months} months` : m.monthly_burn == null ? "Unknown" : m.monthly_burn ? "Add cash" : "Not burning"}
            note={data.cash != null ? `Cash ${inr(data.cash)}${data.cash_as_of ? ` on ${new Date(data.cash_as_of).toLocaleDateString("en-IN", { dateStyle: "medium" })}` : ""}` : "Enter cash in the bank below"} />
        </div>
      )}

      <div className="mt-4 grid gap-4 md:grid-cols-2">
        <form className="rounded-stadium bg-lifted p-6" onSubmit={(e) => { e.preventDefault(); saveSettings({ cash: Number(new FormData(e.currentTarget).get("cash")) }); }}>
          <label className="block text-[15px] font-medium">Cash in the bank today (₹)
            <div className="mt-1 flex gap-2"><input name="cash" type="number" min={0} defaultValue={data.cash ?? ""} className={input} />
              <button className="rounded-btn border-[1.5px] border-ink px-4 font-medium">Save</button></div>
          </label>
          <p className="mt-2 text-[14px] text-slate">Funding recorded: {inr(m.funding_total)}</p>
        </form>
        <div className="rounded-stadium bg-lifted p-6">
          <label className="block text-[15px] font-medium">Industry for the benchmark
            <select className={`${input} mt-1`} value={data.industry ?? ""} onChange={(e) => saveSettings({ industry: e.target.value || null })}>
              <option value="">Choose…</option>
              {data.industries.map((i) => <option key={i}>{i}</option>)}
            </select>
          </label>
          <p className="mt-2 text-[14px] text-slate">
            {data.industry_guessed && data.industry ? "Suggested from your product categories. " : ""}
            {b && `Gross margin ${pct(b.gross_margin)}, net ${pct(b.net_margin)}. `}Source: A. Damodaran, NYU Stern, Margins by Sector (India).
          </p>
        </div>
      </div>

      {saveError && <p role="alert" className="mt-3 rounded-btn bg-lifted p-4 text-[15px]">{saveError}</p>}

      {m.months.length > 0 && <Chart months={m.months} />}

      <RivalMoney profileId={profileId} />

      {m.products.length > 0 && (
        <Block title="Product prices and sales">
          <table className="w-full text-left text-[15px]">
            <thead className="text-[13px] text-slate"><tr><th className="p-2 font-medium">Product</th><th className="p-2 font-medium">Units</th><th className="p-2 font-medium">Revenue</th><th className="p-2 font-medium">Average price</th></tr></thead>
            <tbody>{m.products.slice(0, 10).map((p) => (
              <tr key={p.product} className="border-t border-ink/10"><td className="p-2">{p.product}</td><td className="p-2">{p.units.toLocaleString("en-IN")}</td><td className="p-2">{inr(p.revenue)}</td><td className="p-2">{inr(p.avg_price)}</td></tr>
            ))}</tbody>
          </table>
        </Block>
      )}

      <div className="mt-8 grid gap-4 lg:grid-cols-2">
        <Upload profileId={profileId} onDone={load} />
        <Manual profileId={profileId} onDone={load} />
      </div>

      {data.sources.length > 0 && (
        <Block title="Where the numbers come from">
          <ul className="grid gap-2 text-[15px]">
            {data.sources.map((s) => (
              <li key={s.source} className="flex flex-wrap items-center justify-between gap-2">
                <span>{s.source === "manual" ? "Entered by hand" : s.source} · {s.rows} rows · {s.first} to {s.last}</span>
                <button type="button" className="text-[14px] text-slate underline"
                  onClick={() => confirm(`Remove all rows from ${s.source}?`) && api(`/api/v1/profiles/${profileId}/money/sources/${encodeURIComponent(s.source)}`, { method: "DELETE" }).then(load, (e: Error) => setSaveError(`Not removed: ${e.message}`))}>Remove</button>
              </li>
            ))}
          </ul>
        </Block>
      )}

      {data.recent.length > 0 && (
        <Block title="Transaction log (latest 25)">
          <div className="overflow-x-auto">
            <table className="w-full min-w-[640px] text-left text-[14px]">
              <thead className="text-[13px] text-slate"><tr><th className="p-2 font-medium">Date</th><th className="p-2 font-medium">Type</th><th className="p-2 font-medium">Amount</th><th className="p-2 font-medium">Product / description</th><th className="p-2 font-medium">Source</th></tr></thead>
              <tbody>{data.recent.map((t, i) => (
                <tr key={i} className="border-t border-ink/10"><td className="p-2">{t.date}</td><td className="p-2 capitalize">{t.kind}</td><td className="p-2">{inr(t.amount)}</td>
                  <td className="p-2">{t.product ?? t.description ?? "—"}{t.quantity ? ` × ${t.quantity}` : ""}</td><td className="p-2 text-slate">{t.source}</td></tr>
              ))}</tbody>
            </table>
          </div>
        </Block>
      )}
    </section>
  );
}

function Stat({ label, value, note }: { label: string; value: string; note: string }) {
  return (
    <div className="rounded-stadium bg-lifted p-6">
      <p className="text-[14px] text-slate">{label}</p>
      <p className="mt-1 text-[28px] font-medium tracking-[-0.02em]">{value}</p>
      <p className="mt-1 text-[14px] text-charcoal">{note}</p>
    </div>
  );
}

function Block({ title, children }: { title: string; children: ReactNode }) {
  return (
    <div className="mt-8 rounded-stadium bg-lifted p-6">
      <h2 className="text-[20px] font-medium tracking-[-0.02em]">{title}</h2>
      <div className="mt-3">{children}</div>
    </div>
  );
}

// Revenue and expenses per month: paired bars on one ₹ axis, legend plus hover titles; the log below is the table view.
function Chart({ months }: { months: Month[] }) {
  const shown = months.slice(-12);
  const max = Math.max(1, ...shown.flatMap((m) => [m.revenue, m.expenses]));
  const W = 720, H = 220, pad = 28, slot = (W - pad) / shown.length, bw = Math.min(22, slot / 2 - 4);
  const y = (v: number) => H - 24 - (v / max) * (H - 48);
  return (
    <Block title="Revenue and expenses by month">
      <div className="mb-2 flex gap-5 text-[14px]">
        <span className="flex items-center gap-2"><span className="inline-block size-3 rounded-sm bg-ink" />Revenue</span>
        <span className="flex items-center gap-2"><span className="inline-block size-3 rounded-sm border border-ink bg-dust" />Expenses</span>
      </div>
      <svg viewBox={`0 0 ${W} ${H}`} className="w-full" role="img" aria-label="Monthly revenue and expenses">
        <line x1={pad} x2={W} y1={H - 24} y2={H - 24} stroke="currentColor" strokeOpacity="0.2" />
        <text x={0} y={y(max) + 4} fontSize="11" fill="#696969">{inr(max)}</text>
        {shown.map((m, i) => {
          const x = pad + i * slot + slot / 2;
          return (
            <g key={m.month}>
              <rect x={x - bw - 1} y={y(m.revenue)} width={bw} height={H - 24 - y(m.revenue)} rx="3" fill="#141413"><title>{`${m.month} revenue ${inr(m.revenue)}`}</title></rect>
              <rect x={x + 1} y={y(m.expenses)} width={bw} height={H - 24 - y(m.expenses)} rx="3" fill="#d1cdc7" stroke="#141413" strokeWidth="0.5"><title>{`${m.month} expenses ${inr(m.expenses)}`}</title></rect>
              <text x={x} y={H - 8} fontSize="11" textAnchor="middle" fill="#696969">{m.month.slice(2)}</text>
            </g>
          );
        })}
      </svg>
    </Block>
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
    setBusy(true);
    await api<Preview>(`/api/v1/profiles/${profileId}/money/preview`, { method: "POST", body: fd })
      .then((p) => (setPreview(p), setMapping(p.mapping)), (e: Error) => setMsg(e.message));
    setBusy(false);
  }
  async function confirmImport(e: FormEvent) {
    e.preventDefault();
    if (!file) return;
    const fd = new FormData();
    fd.append("file", file);
    fd.append("mapping", JSON.stringify(mapping));
    setBusy(true);
    await api<{ imported: number; skipped: number }>(`/api/v1/profiles/${profileId}/money/import`, { method: "POST", body: fd }).then(
      (r) => (setMsg(`Imported ${r.imported} transactions${r.skipped ? `; skipped ${r.skipped} rows without a date or amount` : ""}.`), setPreview(null), onDone()),
      (err: Error) => setMsg(err.message),
    );
    setBusy(false);
  }

  return (
    <div className="rounded-stadium bg-lifted p-6">
      <h2 className="text-[20px] font-medium tracking-[-0.02em]">Upload an export</h2>
      <p className="mt-1 text-[14px] text-charcoal">CSV or Excel from your bank, Razorpay, Shopify, Tally or POS. You check the columns before anything is saved. Uploading the same file again replaces it.</p>
      <label className="mt-3 block text-[15px] font-medium">File
        <input type="file" accept=".csv,.xlsx,.xlsm,.txt" className="mt-1 block w-full text-[15px]" onChange={(e) => e.target.files?.[0] && look(e.target.files[0])} />
      </label>
      {busy && <p className="mt-2 text-[14px]">Reading…</p>}
      {preview && (
        <form onSubmit={confirmImport} className="mt-4 grid gap-3">
          <p className="text-[14px] text-slate">{preview.rows} rows in {preview.filename}. We matched these columns; change any that are wrong.</p>
          {Object.keys(FIELD_LABEL).map((f) => (
            <label key={f} className="grid grid-cols-[10rem_1fr] items-center gap-2 text-[14px]">{FIELD_LABEL[f]}
              <select className={input} value={mapping[f] ?? ""} onChange={(e) => setMapping((m) => { const n = { ...m }; if (e.target.value) n[f] = e.target.value; else delete n[f]; return n; })}>
                <option value="">Not in this file</option>
                {preview.headers.map((h) => <option key={h}>{h}</option>)}
              </select>
            </label>
          ))}
          {preview.parsed_sample.length > 0 && (
            <div className="rounded-[14px] bg-white p-3 text-[13px]">
              <p className="font-medium">First rows as we read them</p>
              {preview.parsed_sample.slice(0, 4).map((t, i) => <p key={i}>{t.date} · {t.kind} · {inr(t.amount)} · {t.product ?? t.description ?? ""}</p>)}
            </div>
          )}
          <button disabled={busy} className="inline-flex min-h-11 w-fit items-center rounded-btn border-[1.5px] border-ink bg-ink px-6 text-[16px] font-medium text-canvas disabled:opacity-60">Import {preview.rows} rows</button>
        </form>
      )}
      {msg && <p role="status" className="mt-3 text-[14px]">{msg}</p>}
    </div>
  );
}

function Manual({ profileId, onDone }: { profileId: string; onDone: () => void }) {
  const [msg, setMsg] = useState<string | null>(null);
  async function add(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    const form = e.currentTarget;
    const f = new FormData(form);
    const s = (k: string) => String(f.get(k) ?? "").trim() || null;
    await api(`/api/v1/profiles/${profileId}/money/transactions`, {
      method: "POST",
      body: JSON.stringify({ date: s("date"), kind: s("kind"), amount: Number(s("amount")), product: s("product"), quantity: s("quantity") ? Number(s("quantity")) : null, description: s("description") }),
    }).then(() => (setMsg("Added."), form.reset(), onDone()), (err: Error) => setMsg(err.message));
  }
  return (
    <form onSubmit={add} className="grid gap-3 rounded-stadium bg-lifted p-6">
      <h2 className="text-[20px] font-medium tracking-[-0.02em]">Add an entry</h2>
      <p className="text-[14px] text-charcoal">A sale, an expense or a funding round.</p>
      <div className="grid grid-cols-2 gap-2">
        <label className="text-[14px] font-medium">Date<input name="date" type="date" required className={input} defaultValue={new Date().toISOString().slice(0, 10)} /></label>
        <label className="text-[14px] font-medium">Type<select name="kind" className={input}><option value="sale">Sale</option><option value="expense">Expense</option><option value="funding">Funding</option></select></label>
        <label className="text-[14px] font-medium">Amount (₹)<input name="amount" type="number" min={1} step="any" required className={input} /></label>
        <label className="text-[14px] font-medium">Quantity<input name="quantity" type="number" step="any" className={input} /></label>
      </div>
      <label className="text-[14px] font-medium">Product<input name="product" className={input} placeholder="Stride Runner" /></label>
      <label className="text-[14px] font-medium">Description<input name="description" className={input} placeholder="Seed round from angels, or Shop rent" /></label>
      <button className="inline-flex min-h-11 w-fit items-center rounded-btn border-[1.5px] border-ink bg-ink px-6 text-[16px] font-medium text-canvas">Add entry</button>
      {msg && <p role="status" className="text-[14px]">{msg}</p>}
    </form>
  );
}

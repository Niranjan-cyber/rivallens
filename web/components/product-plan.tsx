"use client";

import Link from "next/link";
import { useCallback, useEffect, useRef, useState } from "react";
import { LoadError } from "@/components/ui";
import { api } from "@/lib/api";

type Scenario = { conversion: number; customers_m12: number; revenue_12m_inr: number; gross_profit_12m_inr: number | null; break_even_month: number | null };
type Option = {
  id: string; price_inr: number; origin: string; scenarios: Record<"best" | "expected" | "worst", Scenario>;
  unit_margin_inr?: number; gross_profit_12m_inr?: number | null; after_runway: boolean; runway_months?: number | null; cash_out_month?: number | null;
};
type Assumption = { key: string; label: string; value: number; origin: "default" | "yours" | "your sales" | "estimate"; help: string; applies: boolean; note?: string };
type Sens = { assumption: string; change: string; recommended_price_inr: number; gross_profit_12m_inr: number; same_recommendation: boolean };
type Saved = { id: string; created_at: string; recommended_price_inr: number; reason: string; flags: string[]; changes: string[] };
export type Kind = "observed" | "yours" | "estimate";
export const KIND_LABEL: Record<Kind, string> = { observed: "Observed", yours: "Your data", estimate: "Estimate" };
type Input = { label: string; value: string; source: "market" | "money" | "customers" | "product"; link: string | null; evidence_id: string | null; kind: Kind };
type Sim = {
  label: string; options: Option[]; recommended_option: string; reason: string; price_unit: string; inputs: Input[];
  viability_flags: { code: string; severity: string; text: string }[]; assumption_list: Assumption[]; sensitivity: Sens[];
  existing: boolean; basis: "gross profit" | "revenue"; runway_now_months: number | null; assumptions: Record<string, number>;
};
const ORIGIN: Record<Assumption["origin"], string> = { default: "Default", yours: "Yours", "your sales": "From your sales", estimate: "Estimate" };
type Segment = { segment: string | null; why: string[]; evidence_ids: string[]; evidence: { id: string; text: string; source: string }[]; message?: string };

const inr = (n: number) => `₹${Math.round(n).toLocaleString("en-IN")}`;
const SOURCE = { market: "Market", money: "Finance", customers: "Customers", product: "This product", profile: "Your business card" } as Record<string, string>;

// S-23 decision layer (B14i): a suggested segment and a simulator whose inputs come from the other dashboards.
export function ProductPlan({ productId, profileId, version }: { productId: string; profileId: string; version: unknown }) {
  const [sim, setSim] = useState<Sim | null>(null);
  const [seg, setSeg] = useState<Segment | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [attempt, setAttempt] = useState(0);
  const [testPrice, setTestPrice] = useState<number | null>(null);
  const [run, setRun] = useState(0); // each new result replays the grid
  const [pending, setPending] = useState(true); // set by clicks, cleared when their result lands
  const latest = useRef(0);
  const load = useCallback((test: number | null) => {
    const n = ++latest.current; // a load that lands after an edit must not put the old numbers back
    api<Sim>(`/api/v1/products/${productId}/simulation${test ? `?test_price=${test}` : ""}`)
      .then((s) => { if (n === latest.current) { setSim(s); setRun((r) => r + 1); setError(null); } }, (e: Error) => setError(e.message))
      .finally(() => { if (n === latest.current) setPending(false); });
  }, [productId]);
  useEffect(() => { load(testPrice); }, [load, testPrice, version, attempt]);
  useEffect(() => {
    api<Segment>(`/api/v1/products/${productId}/segment`).then(setSeg, (e: Error) => setSeg({ segment: null, why: [], evidence_ids: [], evidence: [], message: `Couldn't load the segment: ${e.message}` }));
  }, [productId, version]);
  const href = (link: string | null) => (link === "product-detail" ? `/app/${profileId}/product-detail?id=${productId}` : `/app/${profileId}/${link}`);

  return (
    <div className="mt-8 grid gap-4 md:grid-cols-[1fr_1.6fr]">
      <div className="rounded-stadium bg-lifted p-7" data-testid="segment">
        <p className="text-[15px] font-medium">Suggested customer segment</p>
        {!seg ? <p className="mt-2 text-charcoal" aria-busy="true">Reading Market and Customers…</p> : seg.segment ? (
          <>
            <p className="mt-2 text-[22px] font-medium leading-snug tracking-[-0.01em]">{seg.segment}</p>
            <ul className="mt-3 space-y-1 text-[15px]">{seg.why.map((w) => <li key={w}>· {w}</li>)}</ul>
            <ul className="mt-4 space-y-1.5 border-t border-ink/10 pt-3 text-[13px] text-charcoal">
              {seg.evidence.filter((e) => seg.evidence_ids.includes(e.id)).map((e) => (
                <li key={e.id}><span className="mr-1.5 rounded-pill bg-white px-2 py-0.5 font-medium">{e.id}</span>{e.text} <span className="text-slate">· {SOURCE[e.source]}</span></li>
              ))}
            </ul>
            <p className="mt-3 text-[12px] text-slate">AI suggestion; kept only because it cites the evidence above.</p>
          </>
        ) : <p className="mt-2 text-charcoal">{seg.message}</p>}
      </div>

      <div className="rounded-stadium bg-lifted p-7" data-testid="product-sim">
        <div className="flex flex-wrap items-baseline justify-between gap-2">
          <p className="text-[15px] font-medium">Price simulator for this product</p>
          <p className="text-[12px] text-slate">{sim?.label ?? "Scenario model, not a forecast"}</p>
        </div>
        {error && <div className="mt-3"><LoadError what="the simulator" message={error} onRetry={() => { setError(null); setAttempt((a) => a + 1); }} /></div>}
        {sim && <SimBody sim={sim} run={run} pending={pending} testPrice={testPrice} href={href} productId={productId} onRerun={() => { setPending(true); load(testPrice); }}
          onTest={(v) => { setPending(true); if (v === testPrice) load(v); else setTestPrice(v); }}
          onChange={(s) => { latest.current++; setSim(s); setRun((r) => r + 1); if (testPrice) load(testPrice); }} />}
      </div>
    </div>
  );
}

// After an edit, say what moved, so a change never looks like nothing happened.
function whatChanged(before: Sim, after: Sim, money: string): string {
  const pick = (s: Sim) => s.options.find((o) => o.id === s.recommended_option)!;
  const b = pick(before), a = pick(after), gp = (o: Option) => o.gross_profit_12m_inr ?? o.scenarios.expected.revenue_12m_inr;
  const price = b.price_inr === a.price_inr ? `Recommended price stays ${inr(a.price_inr)}${after.price_unit}` : `Recommended price ${inr(b.price_inr)} → ${inr(a.price_inr)}${after.price_unit}`;
  return gp(b) === gp(a) ? `${price}; ${money.toLowerCase()} unchanged.` : `${price}; ${money.toLowerCase()} ${inr(gp(b))} → ${inr(gp(a))}.`;
}

const STEP = 110, SETTLE = 650; // ms between rows, and how long a cell scrambles before showing its value
const reducedMotion = () => typeof window !== "undefined" && window.matchMedia("(prefers-reduced-motion: reduce)").matches;

// A computed value "decoding" into place: digits scramble briefly, then the real number. Purely visual; the numbers are already final.
function Scramble({ text, delay }: { text: string; delay: number }) {
  const [shown, setShown] = useState(() => (reducedMotion() ? text : text.replace(/\d/g, "0")));
  useEffect(() => {
    if (reducedMotion()) return;
    const start = performance.now();
    const t = setInterval(() => {
      if (performance.now() - start >= delay + SETTLE) { setShown(text); clearInterval(t); }
      else setShown(text.replace(/\d/g, () => String(Math.floor(Math.random() * 10))));
    }, 45);
    return () => clearInterval(t);
  }, [text, delay]);
  return <span className="tabular-nums">{shown}</span>;
}

// The simulator's results, its assumptions (editable), sensitivity and saved scenarios.
function SimBody({ sim, run, pending, testPrice, href, productId, onChange, onRerun, onTest }: {
  sim: Sim; run: number; pending: boolean; testPrice: number | null; href: (l: string | null) => string; productId: string;
  onChange: (s: Sim) => void; onRerun: () => void; onTest: (p: number | null) => void;
}) {
  const [done, setDone] = useState(0);
  const total = reducedMotion() ? 0 : (sim.options.length - 1) * STEP + 2 * 40 + SETTLE + 100;
  useEffect(() => { const t = setTimeout(() => setDone(run), total); return () => clearTimeout(t); }, [run, total]);
  const running = pending || done !== run;
  const best = sim.options.find((o) => o.id === sim.recommended_option)!;
  const [saved, setSaved] = useState<Saved[] | null>(null);
  const [busy, setBusy] = useState(false);
  const [failed, setFailed] = useState<string | null>(null);
  const [changed, setChanged] = useState<string | null>(null);
  const fail = (e: Error) => setFailed(e.message);
  useEffect(() => { api<Saved[]>(`/api/v1/products/${productId}/scenarios`).then(setSaved, () => setSaved([])); }, [productId]);
  const money = sim.basis === "gross profit" ? "12-month gross profit" : "12-month revenue";
  async function setAssumption(key: string, value: number | null) {
    setBusy(true);
    await api<Sim>(`/api/v1/products/${productId}/assumptions`, { method: "PUT", body: JSON.stringify({ assumptions: { [key]: value } }) })
      .then((s) => (setFailed(null), setChanged(whatChanged(sim, s, money)), onChange(s)), fail);
    setBusy(false);
  }
  async function save() {
    setBusy(true);
    await api<Saved[]>(`/api/v1/products/${productId}/scenarios`, { method: "POST", body: "{}" }).then((s) => (setFailed(null), setSaved(s)), fail);
    setBusy(false);
  }
  return (
    <>
      <ul className="mt-3 flex flex-wrap gap-2" aria-label="Inputs">
        {sim.inputs.map((i) => (
          <li key={i.label}>
            <Link href={href(i.link)} className="inline-block rounded-pill border border-ink/20 bg-white px-3 py-1 text-[13px] hover:border-ink" data-source={i.source}>
              <span className="text-slate">{i.label}:</span> {i.value} <span className="text-slate">({KIND_LABEL[i.kind] ?? i.kind})</span> <span className="font-medium">· {SOURCE[i.source]} →</span>
            </Link>
          </li>
        ))}
      </ul>
      {failed && <p role="alert" className="mt-3 rounded-btn bg-white p-3 text-[14px]">Not saved: {failed}</p>}
      {changed && <p role="status" data-testid="sim-changed" className="mt-3 rounded-btn bg-white p-3 text-[14px]">{changed}</p>}
      {sim.viability_flags.map((f) => (
        <p key={f.code} role="note" data-flag={f.code} className={`mt-3 rounded-btn p-3 text-[14px] ${f.severity === "high" ? "bg-ink text-canvas" : "bg-white"}`}>{f.text}</p>
      ))}
      <div className="mt-4 flex flex-wrap items-center gap-3">
        <button type="button" onClick={onRerun} disabled={running} data-testid="sim-run"
          className="inline-flex min-h-10 items-center rounded-btn border-[1.5px] border-ink bg-ink px-4 text-[14px] font-medium text-canvas disabled:opacity-60">
          {running ? "Simulating…" : "Run simulation again"}
        </button>
        <p aria-live="polite" data-testid="sim-status" className="text-[13px] text-charcoal">
          {running ? `Testing ${sim.options.length} prices × 3 levels of price sensitivity…`
            : `${sim.options.length * 3} scenarios run. Best: ${inr(best.price_inr)}${sim.price_unit}.`}
        </p>
      </div>
      <div className="mt-3 overflow-x-auto">
        <table className="w-full min-w-[620px] text-left text-[14px]" data-testid="sim-grid">
          <thead className="text-[12px] text-slate">
            <tr><th className="p-2 font-medium" rowSpan={2}>Price</th><th className="p-2 font-medium" rowSpan={2}>Sold a month</th>
              <th className="p-2 text-center font-medium" colSpan={3}>{money}</th>
              <th className="p-2 font-medium" rowSpan={2}>{sim.existing ? "Runway at this price" : "Break-even"}</th>
              {!sim.existing && <th className="p-2 font-medium" rowSpan={2}>Cash runs out</th>}</tr>
            <tr><th className="p-2 text-right font-normal">Buyers less price-sensitive ({sim.assumptions.elasticity_best})</th>
              <th className="p-2 text-right font-medium">Expected ({sim.assumptions.elasticity_expected})</th>
              <th className="p-2 text-right font-normal">More price-sensitive ({sim.assumptions.elasticity_worst})</th></tr>
          </thead>
          <tbody>
            {sim.options.map((o, i) => {
              const e = o.scenarios.expected, rec = !running && o.id === sim.recommended_option;
              const val = (s: Scenario) => inr(s.gross_profit_12m_inr ?? s.revenue_12m_inr);
              const cell = (t: string, j: number) => <Scramble key={`${run}-${t}`} text={t} delay={i * STEP + j * 40} />;
              return (
                <tr key={o.id} data-option={o.id} className={`border-t border-ink/10 transition-colors duration-300 ${rec ? "bg-white font-medium" : ""}`}>
                  <td className="p-2">{inr(o.price_inr)}{sim.price_unit} <span className="block text-[12px] font-normal text-slate">{rec ? `Recommended${o.origin.startsWith("your") ? ` · ${o.origin}` : ""}` : o.origin}</span></td>
                  <td className="p-2">{cell(e.customers_m12.toLocaleString("en-IN"), 0)}</td>
                  <td className="p-2 text-right text-charcoal">{cell(val(o.scenarios.best), 0)}</td>
                  <td className="p-2 text-right">{cell(val(e), 1)}</td>
                  <td className="p-2 text-right text-charcoal">{cell(val(o.scenarios.worst), 2)}</td>
                  {sim.existing
                    ? <td className="p-2">{o.runway_months != null ? cell(`${o.runway_months} months`, 2) : <span className="text-slate">{sim.runway_now_months == null ? "Unknown: add costs and cash" : "Not burning cash"}</span>}</td>
                    : <td className="p-2">{e.break_even_month ? cell(`Month ${e.break_even_month}`, 2) : "Not in 36 months"}</td>}
                  {!sim.existing && <td className="p-2">{o.cash_out_month ? cell(`Month ${o.cash_out_month}`, 2) : <span className="text-slate">Not within 36 months, or unknown</span>}</td>}
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
      <p className="mt-3 text-[13px] text-charcoal">{sim.reason}</p>
      <form className="mt-3 flex flex-wrap items-center gap-2 text-[14px]" key={testPrice ?? "none"} onSubmit={(e) => {
        e.preventDefault();
        const v = Number(new FormData(e.currentTarget).get("test"));
        if (v > 0) onTest(v);
      }}>
        <label htmlFor="test-price" className="font-medium">What if I charge</label>
        <span>₹</span>
        <input id="test-price" name="test" type="number" min={1} step="any" required defaultValue={testPrice ?? ""} className="w-28 rounded-[10px] border border-ink/30 bg-white px-2 py-1" />
        <button disabled={running} className="rounded-btn border border-ink bg-white px-3 py-1 text-[13px] font-medium">Test this price</button>
        {testPrice && <button type="button" onClick={() => onTest(null)} className="text-[13px] underline">Remove ₹{testPrice.toLocaleString("en-IN")}</button>}
      </form>

      <details className="mt-4 rounded-btn bg-white p-4" data-testid="assumptions">
        <summary className="cursor-pointer text-[14px] font-medium">Assumptions ({sim.assumption_list.filter((x) => x.origin === "default").length} still default)</summary>
        <ul className="mt-3 grid gap-2 text-[14px]">
          {sim.assumption_list.map((x) => (
            <li key={x.key} className="flex flex-wrap items-center gap-2">
              <span className="min-w-[12rem] max-w-[22rem]">{x.label}<span className="block text-[12px] text-slate">{x.help}</span></span>
              <form key={`${x.key}-${x.value}`} className="flex items-center gap-2" onSubmit={(e) => {
                e.preventDefault();
                setAssumption(x.key, Number(new FormData(e.currentTarget).get("v")));
              }}>
                <input name="v" type="number" step="any" min={0} defaultValue={x.value} aria-label={x.label} disabled={!x.applies} className="w-28 rounded-[10px] border border-ink/30 px-2 py-1 disabled:opacity-50" />
                <button disabled={busy || !x.applies} className="rounded-btn border border-ink px-3 py-1 text-[13px] disabled:opacity-50">Set</button>
              </form>
              <span className="text-[12px] text-slate">{ORIGIN[x.origin]}</span>
              {!x.applies && <span className="w-full text-[12px] text-charcoal">{x.note}</span>}
              {x.origin === "yours" && <button type="button" disabled={busy} onClick={() => setAssumption(x.key, null)} className="text-[12px] underline">Reset</button>}
            </li>
          ))}
        </ul>
      </details>

      {sim.sensitivity.length > 0 && (
        <div className="mt-4" data-testid="sensitivity">
          <p className="text-[14px] font-medium">If an assumption is off by 20%</p>
          <ul className="mt-2 grid gap-1 text-[13px]">
            {sim.sensitivity.map((r) => (
              <li key={r.assumption + r.change} className={r.same_recommendation ? "text-charcoal" : "font-medium"}>
                {r.assumption} {r.change}: best price {inr(r.recommended_price_inr)}{sim.price_unit}, {money.toLowerCase()} {inr(r.gross_profit_12m_inr)}
                {r.same_recommendation ? " (same choice)" : " (the choice changes)"}
              </li>
            ))}
          </ul>
        </div>
      )}

      <div className="mt-4 border-t border-ink/10 pt-4" data-testid="scenarios">
        <button type="button" onClick={save} disabled={busy} className="rounded-btn border-[1.5px] border-ink bg-white px-4 py-2 text-[14px] font-medium">Save this scenario</button>
        {saved && saved.length > 0 && (
          <ol className="mt-3 grid gap-2 text-[13px]">
            {saved.map((x) => (
              <li key={x.id} className="rounded-btn bg-white p-3">
                <span className="font-medium">{new Date(x.created_at).toLocaleString("en-IN", { dateStyle: "medium", timeStyle: "short" })}</span> · recommended {inr(x.recommended_price_inr)}{sim.price_unit}
                {x.changes.length > 0 && <ul className="mt-1 text-charcoal">{x.changes.map((c) => <li key={c}>· {c}</li>)}</ul>}
              </li>
            ))}
          </ol>
        )}
      </div>
    </>
  );
}

"use client";

import Link from "next/link";
import { useCallback, useEffect, useState } from "react";
import { rupees } from "@/components/products";
import { api, type Mock } from "@/lib/api";

const MOVES = [
  { id: "cosmetic", label: "Redesign only", hint: "Menu, banner, styling and a clock change. Should be ignored." },
  { id: "price_cut_40", label: "Cut a price 40%", hint: "The middle plan or shoe drops 40%: one real price change." },
  { id: "add_feature", label: "Add a feature", hint: "A new feature on the middle plan or shoe." },
  { id: "positioning", label: "New headline", hint: "A different pitch." },
] as const;

// Replaces the Demo Lab page (D-76): demo accounts change their fictional competitor's website, then check competitors.
export function SimulateMove() {
  const [mocks, setMocks] = useState<Mock[] | null>(null);
  const [msg, setMsg] = useState<string | null>(null);
  const load = useCallback(() => api<{ mocks: Mock[] }>("/api/v1/demo/mocks").then((r) => setMocks(r.mocks), () => setMocks([])), []);
  useEffect(() => { load(); }, [load]);
  if (!mocks?.length) return null;

  async function apply(slug: string, id: string, label: string) {
    await api(`/api/v1/demo/mocks/${slug}/scenario`, { method: "POST", body: JSON.stringify({ scenario: id }) })
      .then(() => setMsg(`${label} applied. Now press Check competitors now.`), (e: Error) => setMsg(e.message));
    load();
  }
  async function reset() {
    await api("/api/v1/demo/mocks/reset", { method: "POST", body: "{}" }).then(() => setMsg("Competitor pages are back to their original version."));
    load();
  }

  return (
    <div className="mt-6 rounded-stadium border-[1.5px] border-dashed border-ink/40 p-6">
      <div className="flex flex-wrap items-baseline justify-between gap-2">
        <h2 className="text-[20px] font-medium tracking-[-0.02em]">Simulate a competitor move</h2>
        <button type="button" onClick={reset} className="text-[14px] underline">Reset competitor pages</button>
      </div>
      <p className="mt-1 max-w-[44rem] text-[14px] text-charcoal">
        Demo accounts only. This changes the website of a fictional competitor we host, so you can watch a change being caught or ignored.
      </p>
      {mocks.map((m) => (
        <div key={m.slug} className="mt-4">
          <p className="text-[15px]">
            <span className="font-medium">{m.name}</span>{" "}
            <span className="text-slate">· now showing {m.version.length === 1 ? "the original page" : m.version.slice(1).map((v) => MOVES.find((x) => x.id === v)?.label ?? v).join(" + ")}</span>{" "}
            <a href={m.url} target="_blank" rel="noreferrer" className="text-[14px] underline">View page</a>
          </p>
          <div className="mt-2 flex flex-wrap gap-2">
            {MOVES.map((x) => (
              <button key={x.id} type="button" title={x.hint} disabled={m.version.includes(x.id)} onClick={() => apply(m.slug, x.id, x.label)}
                className="rounded-pill border-[1.5px] border-ink bg-white px-4 py-2 text-[14px] font-medium hover:shadow-lift-1 disabled:border-dust disabled:bg-canvas disabled:text-slate">
                {x.label}{m.version.includes(x.id) ? " ✓" : ""}
              </button>
            ))}
          </div>
        </div>
      ))}
      {msg && <p role="status" className="mt-3 text-[14px]">{msg}</p>}
    </div>
  );
}

type Market = {
  news: { title: string; url: string; source: string; published: string; snippet: string; funding: boolean }[];
  queries: string[]; news_fetched_at: string | null;
  categories: { category_path: string | null; niche: string | null; product: string; product_id: string; n: number; median: number | null; min: number | null; max: number | null; seen: string | null }[];
};

// B14h: category prices now and what's moving in the market (Indian business news, each linked and dated).
export function MarketPulse({ profileId }: { profileId: string }) {
  const [data, setData] = useState<Market | null>(null);
  const [busy, setBusy] = useState(false);
  const [msg, setMsg] = useState<string | null>(null);
  const load = useCallback(() => api<Market>(`/api/v1/profiles/${profileId}/market`).then(setData, () => {}), [profileId]);
  useEffect(() => { load(); }, [load]);

  async function refresh() {
    setBusy(true);
    setMsg(null);
    await api<{ items: number }>(`/api/v1/profiles/${profileId}/market/news`, { method: "POST" })
      .then((r) => setMsg(r.items ? null : "No recent news about this market in Indian business news."), (e: Error) => setMsg(e.message));
    setBusy(false);
    load();
  }

  if (!data) return null;
  return (
    <>
      {data.categories.length > 0 && (
        <div className="mt-8">
          <h2 className="text-[24px] font-medium tracking-[-0.02em]">Your categories now</h2>
          <ul className="mt-3 grid gap-4 md:grid-cols-2">
            {data.categories.map((c) => (
              <li key={c.product_id} className="rounded-stadium bg-lifted p-6">
                <p className="text-[14px] text-slate">{c.category_path?.split(" > ").slice(-2).join(" › ") ?? "No category"}{c.niche ? ` · ${c.niche}` : ""}</p>
                <p className="mt-1 text-[17px] font-medium">{c.product}</p>
                {c.n > 0 ? (
                  <p className="mt-1 text-[15px] text-charcoal">Median {rupees(c.median)} across {c.n} priced products; range {rupees(c.min)}–{rupees(c.max)}{c.seen ? `, seen ${new Date(c.seen).toLocaleDateString("en-IN", { dateStyle: "medium" })}` : ""}.</p>
                ) : <p className="mt-1 text-[15px] text-slate">No priced products in this category yet.</p>}
                <Link href={`/app/${profileId}/product-detail?id=${c.product_id}`} className="mt-2 inline-block text-[14px] underline">{c.n > 0 ? "Compare" : "Find comparable products"}</Link>
              </li>
            ))}
          </ul>
        </div>
      )}

      <div className="mt-8 flex flex-wrap items-baseline justify-between gap-3">
        <h2 className="text-[24px] font-medium tracking-[-0.02em]">News and funding in your market</h2>
        <button type="button" onClick={refresh} disabled={busy} className="rounded-pill border-[1.5px] border-ink px-4 py-2 text-[14px] font-medium disabled:opacity-60">
          {busy ? "Searching…" : data.news_fetched_at ? "Refresh" : "Find news"}
        </button>
      </div>
      <p className="mt-1 text-[14px] text-slate">
        Indian business news from the last 90 days about {data.queries.length ? data.queries.map((q) => q.replace(/ India market| brand raises funding India/, "").toLowerCase()).filter((v, i, a) => a.indexOf(v) === i).join(", ") : "your products' categories"}.
        {data.news_fetched_at ? ` Checked ${new Date(data.news_fetched_at).toLocaleString("en-IN", { dateStyle: "medium", timeStyle: "short" })}.` : ""}
      </p>
      {msg && <p role="status" className="mt-2 text-[14px]">{msg}</p>}
      {data.news.length > 0 && (
        <ul className="mt-3 divide-y divide-ghost rounded-stadium bg-lifted px-6">
          {data.news.map((n) => (
            <li key={n.url} className="py-4">
              <a href={n.url} target="_blank" rel="noreferrer" className="text-[16px] font-medium underline-offset-4 hover:underline">{n.title}</a>
              <p className="mt-1 text-[13px] text-slate">{n.source}{n.published ? ` · ${n.published}` : ""}{n.funding ? " · Funding" : ""}</p>
              <p className="mt-1 text-[14px] text-charcoal">{n.snippet}</p>
            </li>
          ))}
        </ul>
      )}
    </>
  );
}

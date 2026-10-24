"use client";

import { useSearchParams } from "next/navigation";
import { useCallback, useEffect, useState, type FormEvent } from "react";
import { inr } from "@/components/money";
import { ProductPlan } from "@/components/product-plan";
import { rupees } from "@/components/products";
import { api, type Job, type Product } from "@/lib/api";

type Row = {
  url: string; domain: string; name: string; brand: string | null; niche: string | null; price: number | null;
  rating: number | null; review_count: number | null; features: string[]; observed_at: string; same_niche: boolean; excluded?: string;
};
type Position = { n: number; median: number | null; min: number | null; max: number | null; q75: number | null; pct_vs_median: number | null; rank: number | null };
type Comparison = { product: Product; basis: "niche" | "category"; position: Position; rows: Row[]; premium: Row[]; brands: { brand: string; products: number; min: number | null; max: number | null; revenue: { amount_inr: number; period: string | null; source_url: string; quote: string } | null }[] };

const date = (ts: string) => new Date(ts).toLocaleDateString("en-IN", { dateStyle: "medium" });
const input = "w-full rounded-[14px] border border-ink/30 bg-white px-4 py-2.5 text-[16px] focus:border-ink focus:outline-none";

// S-23: one product against its exact category, with premium inspirations and each brand's range.
export function ProductDetail() {
  const id = useSearchParams().get("id");
  const [data, setData] = useState<Comparison | null>(null);
  const [tab, setTab] = useState<"compare" | "premium" | "brands">("compare");
  const [status, setStatus] = useState<string | null>(null);
  const [note, setNote] = useState<string | null>(null);
  const load = useCallback(() => id && api<Comparison>(`/api/v1/products/${id}/comparison`).then(setData, (e: Error) => setNote(e.message)), [id]);
  useEffect(() => { load(); }, [load]);

  async function find() {
    setNote(null);
    setStatus("Starting…");
    try {
      const { job_id } = await api<{ job_id: string }>(`/api/v1/products/${id}/comparables/find`, { method: "POST" });
      for (let i = 0; i < 90; i++) {
        const job = await api<Job & { result: { pages_read: number; same_category: number } | null }>(`/api/v1/jobs/${job_id}`);
        const last = job.steps?.[job.steps.length - 1];
        if (last?.detail) setStatus(last.detail);
        if (job.status === "done") {
          setNote(`Read ${job.result?.pages_read ?? 0} product pages; ${job.result?.same_category ?? 0} are in the same category.`);
          break;
        }
        if (job.status === "failed" || job.status === "stale") throw new Error(job.error?.message ?? "Search failed.");
        await new Promise((r) => setTimeout(r, 2000));
      }
    } catch (e) {
      setNote((e as Error).message);
    }
    setStatus(null);
    load();
  }

  async function addUrl(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    const url = String(new FormData(e.currentTarget).get("url") ?? "").trim();
    if (!url) return;
    setStatus("Reading that page…");
    await api<{ message: string }>(`/api/v1/products/${id}/comparables`, { method: "POST", body: JSON.stringify({ url }) })
      .then((r) => setNote(r.message), (err: Error) => setNote(err.message));
    setStatus(null);
    load();
  }

  async function setPrice(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    const price = Number(new FormData(e.currentTarget).get("price"));
    await api(`/api/v1/products/${id}`, { method: "PATCH", body: JSON.stringify({ price }) });
    load();
  }

  if (!id) return <p className="rounded-btn bg-lifted p-4">Pick a product from Products.</p>;
  if (!data) return <div className="h-40 rounded-stadium bg-lifted" aria-busy="true">{note}</div>;
  const { product: p, position: pos } = data;
  const path = p.category_path?.split(" > ") ?? [];
  const sameNiche = data.rows.filter((r) => r.same_niche).length;

  return (
    <section data-screen="S-23">
      <p className="text-[14px] text-slate">{path.join(" › ") || "No category yet"} · Google product taxonomy</p>
      <h1 className="mt-1 text-[32px] leading-tight md:text-[40px]">{p.name}</h1>
      {p.niche && <p className="mt-1 text-[18px] text-charcoal">{p.niche}</p>}

      <div className="mt-6 grid gap-4 md:grid-cols-[1.4fr_1fr]">
        <div className="rounded-stadium bg-ink p-7 text-canvas">
          <p className="text-[15px] opacity-80">Price position</p>
          {p.price == null ? (
            <form onSubmit={setPrice} className="mt-3 flex gap-2">
              <input name="price" type="number" min={1} required placeholder="Your price in ₹" aria-label="Your price in rupees" className={`${input} text-ink`} />
              <button className="rounded-btn border-[1.5px] border-canvas px-5 font-medium">Save</button>
            </form>
          ) : pos.n === 0 ? (
            <p className="mt-2 text-[20px]">
              {rupees(p.price, p.unit)}.{" "}
              {data.rows.some((r) => r.price != null)
                ? `Fewer than 3 of the products found are ${(p.niche ?? p.name).toLowerCase()}, so there is no like-for-like median yet. Find more below, or paste a rival's product page.`
                : "No priced products in this category yet: find some below."}
            </p>
          ) : (
            <>
              <p className="mt-2 text-[28px] font-medium leading-tight tracking-[-0.02em]">
                {rupees(p.price, p.unit)} is {pos.pct_vs_median === 0 ? "at" : `${Math.abs(pos.pct_vs_median ?? 0)}% ${(pos.pct_vs_median ?? 0) > 0 ? "above" : "below"}`} the median
              </p>
              <p className="mt-2 opacity-80">
                Median {rupees(pos.median)} across {pos.n} {data.basis === "niche" ? (p.niche ?? "products").toLowerCase() : "products in this category"}; range {rupees(pos.min)}–{rupees(pos.max)}.
                {pos.rank && ` Yours is #${pos.rank} cheapest of ${pos.n + 1}.`}
              </p>
            </>
          )}
        </div>
        <div className="rounded-stadium bg-lifted p-7">
          <p className="text-[15px] font-medium">Find products to compare</p>
          <p className="mt-1 text-[14px] text-charcoal">We read Indian brand stores&apos; public product pages (robots.txt respected). Only products in exactly this category are compared.</p>
          <button type="button" onClick={find} disabled={status !== null}
            className="mt-3 inline-flex min-h-11 items-center rounded-btn border-[1.5px] border-ink bg-ink px-5 text-[15px] font-medium text-canvas disabled:opacity-60">
            {status ?? "Find comparable products"}
          </button>
          <form onSubmit={addUrl} className="mt-3 flex gap-2">
            <input name="url" type="url" placeholder="Or paste a rival's product page" aria-label="Rival product page link" className={input} />
            <button disabled={status !== null} className="rounded-btn border-[1.5px] border-ink px-4 font-medium">Add</button>
          </form>
          {note && <p role="status" className="mt-3 text-[14px] text-charcoal">{note}</p>}
        </div>
      </div>

      <ProductPlan productId={p.id} profileId={p.profile_id} version={data} />

      <div role="tablist" className="mt-8 flex w-fit gap-1 rounded-pill bg-lifted p-1">
        {([["compare", `Compare (${data.rows.length})`], ["premium", `Premium inspirations (${data.premium.length})`], ["brands", `Brands (${data.brands.length})`]] as const).map(([k, label]) => (
          <button key={k} role="tab" aria-selected={tab === k} type="button" onClick={() => setTab(k)}
            className={`rounded-pill px-5 py-2 text-[15px] font-medium ${tab === k ? "bg-ink text-canvas" : ""}`}>{label}</button>
        ))}
      </div>

      {tab === "compare" && (
        data.rows.length === 0 ? <p className="mt-4 rounded-stadium bg-lifted p-7 text-charcoal">Nothing to compare yet. Use “Find comparable products” or paste a rival&apos;s product page.</p> : (
          <div className="mt-4 overflow-x-auto rounded-stadium bg-lifted p-2">
            <table className="w-full min-w-[720px] text-left text-[15px]">
              <thead className="text-[13px] text-slate">
                <tr><th className="p-3 font-medium">Product</th><th className="p-3 font-medium">Price</th><th className="p-3 font-medium">Rating</th><th className="p-3 font-medium">Features stated on its page</th><th className="p-3 font-medium">Seen</th></tr>
              </thead>
              <tbody>
                <tr className="border-t border-ink/10 bg-white">
                  <td className="p-3"><span className="font-medium">{p.name}</span><span className="block text-[13px] text-slate">Yours</span></td>
                  <td className="p-3">{rupees(p.price, p.unit)}</td><td className="p-3 text-slate">—</td>
                  <td className="p-3">{p.features.length ? p.features.join(" · ") : <span className="text-slate">Add your features on the product</span>}</td><td className="p-3" />
                </tr>
                {data.rows.map((r) => <RowView key={r.url} r={r} />)}
              </tbody>
            </table>
            <p className="p-3 text-[13px] text-slate">
              {sameNiche} of {data.rows.length} are {p.niche?.toLowerCase() ?? "the same niche"}; the rest share the category. Prices in ₹ as listed on each page; anything not on the page is Unknown.
            </p>
          </div>
        )
      )}
      {tab === "premium" && (
        <ul className="mt-4 grid gap-4 md:grid-cols-2">
          {data.premium.length === 0 && <li className="rounded-stadium bg-lifted p-7 text-charcoal">Premium products appear once there are a few priced comparables.</li>}
          {data.premium.map((r) => (
            <li key={r.url} className="rounded-stadium bg-lifted p-7">
              <a href={r.url} target="_blank" rel="noreferrer" className="text-[18px] font-medium underline-offset-4 hover:underline">{r.name}</a>
              <p className="text-[14px] text-slate">{r.brand ?? r.domain} · {rupees(r.price)} · top 25% by price</p>
              {r.features.length > 0 && <p className="mt-3 text-[15px]">What it offers: {r.features.join(" · ")}</p>}
            </li>
          ))}
        </ul>
      )}
      {tab === "brands" && (
        <ul className="mt-4 grid gap-3 md:grid-cols-2">
          {data.brands.map((b) => (
            <li key={b.brand} className="rounded-stadium bg-lifted p-6">
              <p className="text-[17px] font-medium">{b.brand}</p>
              <p className="text-[15px] text-charcoal">{b.products} product{b.products > 1 ? "s" : ""} in this category{b.min != null ? `, ${rupees(b.min)}${b.max !== b.min ? `–${rupees(b.max)}` : ""}` : ""}</p>
              <p className="mt-1 text-[14px]">
                Revenue: {b.revenue ? <a className="underline" href={b.revenue.source_url} target="_blank" rel="noreferrer">{inr(b.revenue.amount_inr)}{b.revenue.period ? ` (${b.revenue.period})` : ""}</a> : <span className="text-slate">Unknown (find it on Finance)</span>}
              </p>
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}

function RowView({ r }: { r: Row }) {
  return (
    <tr className="border-t border-ink/10 align-top">
      <td className="p-3">
        <a href={r.url} target="_blank" rel="noreferrer" className="font-medium underline-offset-4 hover:underline">{r.name}</a>
        <span className="block text-[13px] text-slate">{r.brand ?? r.domain}{r.same_niche ? "" : " · same category, different niche"}</span>
        {r.excluded && <span className="block text-[13px] text-charcoal">Not counted: {r.excluded}</span>}
      </td>
      <td className="p-3">{r.price != null ? rupees(r.price) : <span className="text-slate">Unknown</span>}</td>
      <td className="p-3">{r.rating != null ? `${r.rating}★${r.review_count ? ` (${r.review_count})` : ""}` : <span className="text-slate">Unknown</span>}</td>
      <td className="p-3 text-[14px]">{r.features.length ? r.features.join(" · ") : <span className="text-slate">Not stated</span>}</td>
      <td className="p-3 text-[13px] text-slate">{date(r.observed_at)}</td>
    </tr>
  );
}

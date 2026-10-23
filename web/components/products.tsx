"use client";

import Link from "next/link";
import { useCallback, useEffect, useState, type FormEvent } from "react";
import { SampleBadge } from "@/components/ui";
import { api, type Product } from "@/lib/api";

const UNIT: Record<string, string> = { one_time: "", month: "/month", year: "/year", hour: "/hour", user: "/user" };
export const rupees = (v: number | null, unit = "one_time") => (v == null ? "No price yet" : `₹${v.toLocaleString("en-IN")}${UNIT[unit] ?? ""}`);
const input = "mt-1 w-full rounded-[14px] border border-ink/30 bg-white px-4 py-2.5 text-[16px] focus:border-ink focus:outline-none";
const SOURCE: Record<string, string> = { ai: "AI-picked category", top_match: "Best keyword match", user: "Category set by you", none: "No category yet" };

// S-22: existing and new products, each in an exact Google product taxonomy category.
export function Products({ profileId }: { profileId: string }) {
  const [products, setProducts] = useState<Product[] | null>(null);
  const [tab, setTab] = useState<"existing" | "new">("existing");
  const [adding, setAdding] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const load = useCallback(() => api<Product[]>(`/api/v1/profiles/${profileId}/products`).then(setProducts, (e: Error) => setError(e.message)), [profileId]);

  useEffect(() => {
    load();
    const t = setInterval(load, 4000); // products listed at onboarding are classified in the background
    const stop = setTimeout(() => clearInterval(t), 40000);
    return () => (clearInterval(t), clearTimeout(stop));
  }, [load]);

  const shown = (products ?? []).filter((p) => p.stage === tab);
  return (
    <section data-screen="S-22">
      <h1 className="text-[32px] leading-tight md:text-[40px]">Products</h1>
      <p className="mt-3 max-w-[44rem] text-[17px] text-charcoal">
        Every product sits in one exact category from Google&apos;s product taxonomy, so a football is only ever compared with footballs.
      </p>
      <div className="mt-6 flex flex-wrap items-center gap-3">
        <div role="tablist" className="flex gap-1 rounded-pill bg-lifted p-1">
          {(["existing", "new"] as const).map((t) => (
            <button key={t} role="tab" aria-selected={tab === t} type="button" onClick={() => setTab(t)}
              className={`rounded-pill px-5 py-2 text-[15px] font-medium ${tab === t ? "bg-ink text-canvas" : ""}`}>
              {t === "existing" ? "Existing products" : "New products"} ({(products ?? []).filter((p) => p.stage === t).length})
            </button>
          ))}
        </div>
        <button type="button" onClick={() => setAdding(!adding)}
          className="inline-flex min-h-11 items-center rounded-btn border-[1.5px] border-ink bg-ink px-6 text-[16px] font-medium text-canvas">
          {adding ? "Close" : tab === "new" ? "Add a new product" : "Add a product"}
        </button>
      </div>
      {adding && <AddProduct profileId={profileId} stage={tab} onAdded={(p) => (setProducts((ps) => [...(ps ?? []), p]), setAdding(false))} />}
      {error && <p className="mt-4 rounded-btn bg-lifted p-4 text-charcoal">{error}</p>}
      {!products ? (
        <div className="mt-6 h-40 rounded-stadium bg-lifted" aria-busy="true" />
      ) : shown.length === 0 ? (
        <p className="mt-6 rounded-stadium bg-lifted p-7 text-charcoal">
          {tab === "existing" ? "No products yet. Add what you sell, by name or by pasting its product page." : "No new products yet. Add something you plan to launch to compare it before you price it."}
        </p>
      ) : (
        <ul className="mt-6 grid gap-4 md:grid-cols-2">
          {shown.map((p) => <ProductCard key={p.id} product={p} onChange={(np) => setProducts((ps) => ps?.map((x) => (x.id === np.id ? np : x)) ?? null)} />)}
        </ul>
      )}
    </section>
  );
}

function ProductCard({ product: p, onChange }: { product: Product; onChange: (p: Product) => void }) {
  const [editing, setEditing] = useState(false);
  const [q, setQ] = useState("");
  const [options, setOptions] = useState<{ id: number; path: string }[]>([]);

  async function search(e: FormEvent) {
    e.preventDefault();
    setOptions(await api<{ id: number; path: string }[]>(`/api/v1/taxonomy?q=${encodeURIComponent(q)}`));
  }
  async function pick(id: number) {
    onChange(await api<Product>(`/api/v1/products/${p.id}`, { method: "PATCH", body: JSON.stringify({ taxonomy_id: id }) }));
    setEditing(false);
  }
  const path = p.category_path?.split(" > ") ?? [];

  return (
    <li className="rounded-stadium bg-lifted p-7">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <Link href={`/app/${p.profile_id}/product-detail?id=${p.id}`} className="text-[22px] font-medium tracking-[-0.02em] underline-offset-4 hover:underline">{p.name}</Link>
        {p.is_demo_data && <SampleBadge label="Demo business" />}
      </div>
      {p.niche && <p className="mt-1 text-[17px]">{p.niche}</p>}
      <p className="mt-2 text-[14px] text-slate">
        {path.length ? path.map((s, i) => <span key={i}>{i > 0 && " › "}<span className={i === path.length - 1 ? "font-medium text-ink" : ""}>{s}</span></span>) : "Finding the category…"}
      </p>
      <p className="mt-1 text-[13px] text-slate">{SOURCE[p.category_source]} · Google product taxonomy</p>
      <p className="mt-4 text-[17px]">{rupees(p.price, p.unit)}</p>
      {p.source && <p className="mt-1 text-[13px] text-slate">Read from <a className="underline" href={p.source.url} target="_blank" rel="noreferrer">its product page</a> on {new Date(p.source.observed_at).toLocaleDateString("en-IN", { dateStyle: "medium" })}</p>}
      <div className="mt-4 flex flex-wrap gap-4 text-[15px]">
        <Link href={`/app/${p.profile_id}/product-detail?id=${p.id}`} className="font-medium underline">Compare</Link>
        <button type="button" onClick={() => setEditing(!editing)} className="underline">{editing ? "Cancel" : "Change category"}</button>
      </div>
      {editing && (
        <form onSubmit={search} className="mt-3">
          <label className="block text-[14px] font-medium">Search categories
            <input className={input} value={q} onChange={(e) => setQ(e.target.value)} placeholder="e.g. running shoes, birthday cake" />
          </label>
          <ul className="mt-2 max-h-56 overflow-y-auto">
            {options.map((o) => (
              <li key={o.id}><button type="button" onClick={() => pick(o.id)} className="w-full rounded-[10px] px-3 py-2 text-left text-[14px] hover:bg-white">{o.path}</button></li>
            ))}
          </ul>
        </form>
      )}
    </li>
  );
}

function AddProduct({ profileId, stage, onAdded }: { profileId: string; stage: "existing" | "new"; onAdded: (p: Product) => void }) {
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function submit(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    const f = new FormData(e.currentTarget);
    const s = (k: string) => String(f.get(k) ?? "").trim() || null;
    setBusy(true);
    setError(null);
    await api<Product>(`/api/v1/profiles/${profileId}/products`, {
      method: "POST",
      body: JSON.stringify({ stage, name: s("name"), url: s("url"), description: s("description"), price: s("price") ? Number(s("price")) : null, unit: s("unit") ?? "one_time" }),
    }).then(onAdded, (err: Error) => setError(err.message));
    setBusy(false);
  }

  return (
    <form onSubmit={submit} className="mt-6 grid max-w-[44rem] gap-4 rounded-stadium bg-lifted p-7">
      <p className="text-[15px] text-charcoal">Give a name, or paste the product&apos;s page link and we&apos;ll read the name and price from it.</p>
      <label className="block text-[15px] font-medium">Product name<input name="name" className={input} placeholder="Stride Runner" /></label>
      <label className="block text-[15px] font-medium">Product page link <span className="font-normal text-slate">(optional)</span><input name="url" type="url" className={input} placeholder="https://" /></label>
      <label className="block text-[15px] font-medium">What it is <span className="font-normal text-slate">(optional)</span><input name="description" className={input} placeholder="Lightweight running shoe for Indian roads" /></label>
      <div className="grid grid-cols-[1fr_auto] gap-2">
        <label className="block text-[15px] font-medium">Price in ₹ <span className="font-normal text-slate">(optional)</span><input name="price" type="number" min={0} className={input} /></label>
        <label className="block text-[15px] font-medium">Per
          <select name="unit" className={input}><option value="one_time">item</option><option value="month">month</option><option value="year">year</option><option value="user">user</option></select>
        </label>
      </div>
      {error && <p role="alert" className="rounded-btn bg-white p-4 text-charcoal">{error}</p>}
      <button disabled={busy} className="inline-flex min-h-11 w-fit items-center rounded-btn border-[1.5px] border-ink bg-ink px-6 text-[16px] font-medium text-canvas disabled:opacity-60">
        {busy ? "Finding its category…" : "Add product"}
      </button>
    </form>
  );
}

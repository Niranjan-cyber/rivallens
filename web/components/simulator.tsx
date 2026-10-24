"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { LoadError } from "@/components/ui";
import { api, type Product } from "@/lib/api";

type Summary = { recommended_price_inr: number; price_unit: string; current_price_inr: number | null } | { error: string };

const inr = (n: number) => `₹${Math.round(n).toLocaleString("en-IN")}`;

// S-14: one price simulator per product (its market, costs and customers differ), so this page lists them.
export function Simulator({ profileId }: { profileId: string }) {
  const [products, setProducts] = useState<Product[] | null>(null);
  const [sims, setSims] = useState<Record<string, Summary>>({});
  const [error, setError] = useState<string | null>(null);
  const [attempt, setAttempt] = useState(0);

  useEffect(() => {
    api<Product[]>(`/api/v1/profiles/${profileId}/products`).then((ps) => {
      setProducts(ps);
      for (const p of ps)
        api<Summary>(`/api/v1/products/${p.id}/simulation`).then((s) => setSims((m) => ({ ...m, [p.id]: s })),
          (e: Error) => setSims((m) => ({ ...m, [p.id]: { error: e.message } })));
    }, (e: Error) => setError(e.message));
  }, [profileId, attempt]);

  if (error) return <LoadError what="your products" message={error} onRetry={() => { setError(null); setAttempt((a) => a + 1); }} />;
  if (!products) return <div className="h-40 rounded-stadium bg-lifted" aria-busy="true" />;

  return (
    <section data-screen="S-14">
      <h1 className="text-[32px] leading-tight md:text-[40px]">Price simulator</h1>
      <p className="mt-3 max-w-[44rem] text-[17px] text-charcoal">
        Each product has its own simulator: its like-for-like market prices, your unit cost and runway from Finance, and what customers ask for.
        Pick one to test prices, change the assumptions and save scenarios.
      </p>
      {products.length === 0 ? (
        <p className="mt-6 rounded-stadium bg-lifted p-7 text-charcoal">
          No products yet. <Link href={`/app/${profileId}/product`} className="underline">Add a product</Link> with its price to simulate it.
        </p>
      ) : (
        <ul className="mt-6 grid gap-3 md:grid-cols-2" data-testid="sim-products">
          {products.map((p) => {
            const s = sims[p.id];
            return (
              <li key={p.id}>
                <Link href={`/app/${profileId}/product-detail?id=${p.id}`} className="block h-full rounded-stadium bg-lifted p-6 hover:shadow-lift-2">
                  <p className="text-[18px] font-medium">{p.name}</p>
                  <p className="text-[14px] text-slate">{p.niche ?? "No category yet"}</p>
                  <p className="mt-3 text-[15px]">
                    {!s ? <span className="text-slate">Simulating…</span>
                      : "error" in s ? <span className="text-charcoal">{s.error}</span>
                      : <>Today {s.current_price_inr != null ? `${inr(s.current_price_inr)}${s.price_unit}` : "no price"} · recommended <span className="font-medium">{inr(s.recommended_price_inr)}{s.price_unit}</span></>}
                  </p>
                  <p className="mt-3 text-[15px] font-medium underline">Open its simulator</p>
                </Link>
              </li>
            );
          })}
        </ul>
      )}
      <p className="mt-4 text-[13px] text-slate">Scenario model, not a forecast.</p>
    </section>
  );
}

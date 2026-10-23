"use client";

import Link from "next/link";
import { useEffect, useState, type ReactNode } from "react";
import { inr } from "@/components/money";
import { SampleBadge } from "@/components/ui";
import { api, type Product, type ProfileSummary } from "@/lib/api";

type Card = Record<string, { value: unknown } | undefined>;
type Profile = { id: string; name: string; card: Card; is_demo_data: boolean };

const list = (v: unknown) => (Array.isArray(v) ? v.map(String) : typeof v === "string" && v ? v.split(",").map((s) => s.trim()) : []);

type Customers = { total: number; sentiment: Record<string, number>; themes: { label: string; kind: string }[] };

// S-21: the main dashboard. One card per dashboard, each saying what needs attention or what to add first.
export function Overview({ profileId }: { profileId: string }) {
  const [profile, setProfile] = useState<Profile | null>(null);
  const [summary, setSummary] = useState<ProfileSummary | null>(null);
  const [items, setItems] = useState<Product[] | null>(null);
  const [customers, setCustomers] = useState<Customers | null>(null);
  const [money, setMoney] = useState<{ transactions_count: number; metrics: { monthly_revenue: number; operating_margin: number | null; runway_months: number | null; monthly_burn: number | null }; benchmark: { industry: string; operating_margin: number | null } | null } | null>(null);

  useEffect(() => {
    api<Profile>(`/api/v1/profiles/${profileId}`).then(setProfile, () => {});
    api<Product[]>(`/api/v1/profiles/${profileId}/products`).then(setItems, () => {});
    api<NonNullable<typeof money>>(`/api/v1/profiles/${profileId}/money`).then(setMoney, () => {});
    api<ProfileSummary[]>("/api/v1/profiles").then((ps) => setSummary(ps.find((p) => p.id === profileId) ?? null), () => {});
    api<Customers>(`/api/v1/profiles/${profileId}/customers`).then(setCustomers, () => {});
  }, [profileId]);

  const card = profile?.card ?? {};
  const val = (k: string) => card[k]?.value;
  const products = items?.length ? items.map((p) => p.niche ? `${p.name} (${p.niche})` : p.name) : list(val("main_products"));
  const meta = [val("business_type"), list(val("india_markets"))[0]].filter(Boolean).join(" in ");

  return (
    <section data-screen="S-21">
      <div className="flex flex-wrap items-center gap-3">
        <h1 className="text-[32px] leading-tight md:text-[40px]">{profile?.name ?? "Your business"}</h1>
        {profile?.is_demo_data && <SampleBadge label={val("demo_basis") ? `Demo business, modelled on ${val("demo_basis")}` : "Demo business"} />}
      </div>
      <p className="mt-2 text-[17px] text-charcoal">
        {meta ? `${meta}. ` : ""}
        <Link href={`/app/${profileId}/card`} className="underline">Business card</Link>
      </p>

      <div className="mt-8 grid gap-4 md:grid-cols-2">
        <Tile title="Product" href={`/app/${profileId}/product`} cta={products.length ? "Open products" : "Add your products"}>
          {products.length ? (
            <>
              <p className="text-[28px] font-medium tracking-[-0.02em]">{products.length} product{products.length > 1 ? "s" : ""}</p>
              <p className="mt-1 text-charcoal">{products.slice(0, 4).join(" · ")}</p>
            </>
          ) : (
            <p className="text-charcoal">Add what you sell or plan to sell. Each product is compared only with products in its exact category.</p>
          )}
        </Tile>
        <Tile title="Finance" href={`/app/${profileId}/finance`} cta={money?.transactions_count ? "Open finance" : "Upload sales or add entries"}>
          {money?.transactions_count ? (
            <>
              <p className="text-[28px] font-medium tracking-[-0.02em]">
                {money.metrics.runway_months != null ? `${money.metrics.runway_months} months of runway` : money.metrics.monthly_burn == null ? `${inr(money.metrics.monthly_revenue)} revenue a month` : money.metrics.monthly_burn ? "Add cash to see runway" : "Not burning cash"}
              </p>
              <p className="mt-1 text-charcoal">
                {inr(money.metrics.monthly_revenue)} revenue a month, operating margin {money.metrics.operating_margin != null ? `${(money.metrics.operating_margin * 100).toFixed(1)}%` : "—"}
                {money.benchmark?.operating_margin != null ? ` vs ${(money.benchmark.operating_margin * 100).toFixed(1)}% for ${money.benchmark.industry} in India` : ""}.
              </p>
            </>
          ) : (
            <p className="text-charcoal">Upload a CSV or Excel export from your bank, payment gateway or accounting tool to see revenue, margin and runway.</p>
          )}
        </Tile>
        <Tile title="Market" href={`/app/${profileId}/dashboard`} cta="Open market">
          {summary ? (
            <>
              <p className="text-[28px] font-medium tracking-[-0.02em]">{summary.competitors_monitored} competitors watched</p>
              <p className="mt-1 text-charcoal">
                {summary.unread_alerts ? `${summary.unread_alerts} unread alert${summary.unread_alerts > 1 ? "s" : ""}. ` : "No unread alerts. "}
                {summary.last_run_at ? `Last checked ${new Date(summary.last_run_at).toLocaleString("en-IN", { dateStyle: "medium", timeStyle: "short" })}.` : "Not checked yet."}
              </p>
            </>
          ) : (
            <p className="text-charcoal">Find competitors in India and watch their prices, plans and features.</p>
          )}
        </Tile>
        <Tile title="Customers" href={`/app/${profileId}/customers`} cta={customers?.total ? "Open customers" : "Add reviews or comments"}>
          {customers?.total ? (
            <>
              <p className="text-[28px] font-medium tracking-[-0.02em]">{customers.total} mentions</p>
              <p className="mt-1 text-charcoal">
                {customers.sentiment.positive ?? 0} positive · {customers.sentiment.negative ?? 0} negative
                {customers.themes[0] ? `. Top theme: ${customers.themes[0].label} (${customers.themes[0].kind}).` : "."}
              </p>
            </>
          ) : (
            <p className="text-charcoal">Upload reviews or social media exports, or point us at your product pages, to see what customers actually ask for.</p>
          )}
        </Tile>
      </div>
    </section>
  );
}

function Tile({ title, href, cta, children }: { title: string; href: string; cta: string; children: ReactNode }) {
  return (
    <Link href={href} className="flex flex-col rounded-stadium bg-lifted p-7 hover:shadow-lift-2">
      <p className="text-[15px] font-medium text-slate">{title}</p>
      <div className="mt-2 flex-1">{children}</div>
      <p className="mt-5 text-[15px] font-medium underline">{cta}</p>
    </Link>
  );
}

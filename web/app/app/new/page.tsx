"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";
import { api, type Job } from "@/lib/api";

type Origin = "user" | "ai_drafted";
type Field = { value: unknown; origin: Origin };
type Card = Record<string, Field>;
type Kind = "business" | "idea";

const LIST_FIELDS = new Set(["india_markets", "attributes", "planned_features"]);
const STEPS = ["Basics", "Offering", "Priorities"] as const;
const WATCH = [
  { key: "price", label: "Price changes" },
  { key: "plan", label: "Plans added or dropped" },
  { key: "feature", label: "Features added or removed" },
  { key: "positioning", label: "Positioning changes" },
];

function fromDraft(draft: Record<string, unknown>): Card {
  const card: Card = {};
  for (const [k, v] of Object.entries(draft)) {
    const empty = v === null || v === "" || (Array.isArray(v) && v.length === 0);
    if (!empty) card[k] = { value: v, origin: "ai_drafted" };
  }
  return card;
}

const inputCls = "mt-1 w-full rounded-[14px] border border-ink/30 bg-white px-4 py-2.5 text-[17px] focus:border-ink focus:outline-none";

// S-04 (path + quick start) and S-05 (3-step wizard) in one flow; Finish saves and opens S-06.
export default function NewProfile() {
  const router = useRouter();
  const [kind, setKind] = useState<Kind>("business");
  const [input, setInput] = useState("");
  const [status, setStatus] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [card, setCard] = useState<Card | null>(null);
  const [step, setStep] = useState(0);

  async function draft() {
    setError(null);
    const isUrl = /^https?:\/\//i.test(input.trim());
    setStatus(isUrl ? "Reading your site…" : "Drafting your card…");
    try {
      const { job_id } = await api<{ job_id: string }>("/api/v1/profiles/draft", {
        method: "POST",
        body: JSON.stringify({ kind, ...(isUrl ? { url: input.trim() } : { description: input.trim() }) }),
      });
      for (let i = 0; i < 60; i++) {
        const job = await api<Job & { result: Record<string, unknown> | null }>(`/api/v1/jobs/${job_id}`);
        if (job.status === "done" && job.result) return (setCard(fromDraft(job.result)), setStep(0), setStatus(null));
        if (job.status === "failed" || job.status === "stale") throw new Error(job.error?.message ?? "Drafting failed. Fill the card in manually.");
        await new Promise((r) => setTimeout(r, 1000));
      }
      throw new Error("Drafting is taking too long. Fill the card in manually.");
    } catch (e) {
      setError((e as Error).message);
      setStatus(null);
    }
  }

  const get = (k: string) => card?.[k]?.value;
  const text = (k: string) => {
    const v = get(k);
    return Array.isArray(v) ? v.join(", ") : v == null ? "" : String(v);
  };
  const set = (k: string, raw: string) =>
    setCard((c) => ({
      ...c,
      [k]: { value: LIST_FIELDS.has(k) ? raw.split(",").map((s) => s.trim()).filter(Boolean) : raw, origin: "user" },
    }));
  const price = (get("price") ?? {}) as { amount?: number | null; currency?: string | null; period?: string | null };
  const setPrice = (patch: object) => setCard((c) => ({ ...c, price: { value: { currency: "INR", period: "month", ...price, ...patch }, origin: "user" } }));
  const watch = (get("watch") as string[] | undefined) ?? WATCH.map((w) => w.key);

  function badge(k: string) {
    return card?.[k]?.origin === "ai_drafted" ? (
      <span className="ml-2 rounded-pill bg-ghost px-2 py-0.5 text-[12px] font-medium text-charcoal">AI-drafted</span>
    ) : null;
  }
  function textField(k: string, label: string, placeholder?: string) {
    return (
      <label key={k} className="block">
        <span className="text-[15px] font-medium">{label}{badge(k)}</span>
        <input className={inputCls} value={text(k)} placeholder={placeholder} onChange={(e) => set(k, e.target.value)} />
      </label>
    );
  }

  async function finish() {
    if (!card) return;
    const name = text("name").trim();
    if (!name) return (setStep(0), setError("Give the business or idea a name."));
    const offering = (get("offering_type") as string) === "product" ? "product" : "service";
    const full: Card = { ...card, watch: { value: watch, origin: card.watch?.origin ?? "user" } };
    await api<{ id: string }>("/api/v1/profiles", { method: "POST", body: JSON.stringify({ kind, offering_type: offering, name, card: full }) }).then(
      (p) => router.push(`/app/${p.id}/card`),
      (e: Error) => setError(e.message),
    );
  }

  if (!card)
    return (
      <section data-screen="S-04">
        <h1 className="text-[32px] leading-tight md:text-[40px]">Add a business</h1>
        <p className="mt-3 max-w-[40rem] text-[17px] text-charcoal">Describe it in one line or paste your website. We draft the profile; you check it.</p>
        <div role="radiogroup" aria-label="What are you adding?" className="mt-6 grid gap-3 sm:grid-cols-2">
          {([["business", "I run a business", "Watch competitors of something already selling."], ["idea", "I have an idea", "Size up the market before you launch."]] as const).map(([k, title, hint]) => (
            <button key={k} type="button" role="radio" aria-checked={kind === k} onClick={() => setKind(k)}
              className={`rounded-stadium p-6 text-left ${kind === k ? "border-[1.5px] border-ink bg-white" : "border-[1.5px] border-transparent bg-lifted"}`}>
              <span className="block text-[20px] font-medium">{title}</span>
              <span className="mt-1 block text-charcoal">{hint}</span>
            </button>
          ))}
        </div>
        <label className="mt-6 block max-w-[40rem]">
          <span className="text-[15px] font-medium">Your website or a one-line description</span>
          <textarea className={`${inputCls} min-h-24`} maxLength={500} value={input} onChange={(e) => setInput(e.target.value)}
            placeholder="Pune startup, managed app deployment for Indian developers, Pro ₹999/mo" />
        </label>
        <div className="mt-4 flex flex-wrap items-center gap-4">
          <button type="button" disabled={!input.trim() || status !== null} onClick={draft}
            className="inline-flex min-h-11 items-center rounded-btn border-[1.5px] border-ink bg-ink px-6 text-[16px] font-medium text-canvas disabled:opacity-50">
            {status ?? "Draft my card"}
          </button>
          <button type="button" onClick={() => setCard({})} className="text-[15px] underline">Fill manually</button>
        </div>
        {error && <p className="mt-4 max-w-[40rem] rounded-btn bg-lifted p-4 text-charcoal">{error}</p>}
      </section>
    );

  return (
    <section data-screen="S-05" className="max-w-[44rem]">
      <h1 className="text-[32px] leading-tight md:text-[40px]">Check your {kind === "idea" ? "idea" : "business"} card</h1>
      <ol className="mt-4 flex gap-2 text-[15px]" aria-label="Steps">
        {STEPS.map((s, i) => (
          <li key={s} aria-current={i === step ? "step" : undefined}
            className={`rounded-pill px-4 py-1.5 ${i === step ? "bg-ink text-canvas" : i < step ? "bg-ghost" : "bg-lifted text-slate"}`}>
            {i + 1}. {s}
          </li>
        ))}
      </ol>
      <div className="mt-6 grid gap-4 rounded-stadium bg-lifted p-7">
        {step === 0 && (
          <>
            {textField("name", "Name")}
            {textField("website", "Website", "https://")}
            {textField("industry", "Industry")}
            {textField("india_markets", "Cities or regions in India (comma-separated)")}
          </>
        )}
        {step === 1 && (
          <>
            <fieldset>
              <legend className="text-[15px] font-medium">You sell a{badge("offering_type")}</legend>
              <div className="mt-2 flex gap-4">
                {(["service", "product"] as const).map((o) => (
                  <label key={o} className="flex min-h-11 items-center gap-2 text-[17px]">
                    <input type="radio" name="offering" className="size-5 accent-ink" checked={(get("offering_type") ?? "service") === o} onChange={() => set("offering_type", o)} />
                    {o}
                  </label>
                ))}
              </div>
            </fieldset>
            {textField("category", "Category")}
            {kind === "idea" ? (
              <>
                {textField("problem", "Problem you solve")}
                {textField("target_customer", "Target customer")}
                {textField("planned_features", "Planned features (comma-separated)")}
              </>
            ) : (
              textField("attributes", "Key attributes (comma-separated)")
            )}
            <div>
              <span className="text-[15px] font-medium">{kind === "idea" ? "Expected price" : "Your price"}{badge("price")}</span>
              <div className="mt-1 grid grid-cols-[1fr_auto_auto] gap-2">
                <input type="number" min={0} className={inputCls} value={price.amount ?? ""} aria-label="Amount"
                  onChange={(e) => setPrice({ amount: e.target.value === "" ? null : Number(e.target.value) })} />
                <select className={inputCls} value={price.currency ?? "INR"} aria-label="Currency" onChange={(e) => setPrice({ currency: e.target.value })}>
                  <option>INR</option><option>USD</option>
                </select>
                <select className={inputCls} value={price.period ?? "month"} aria-label="Billing period" onChange={(e) => setPrice({ period: e.target.value })}>
                  <option value="month">/month</option><option value="year">/year</option><option value="one_time">one-time</option>
                </select>
              </div>
            </div>
          </>
        )}
        {step === 2 && (
          <fieldset>
            <legend className="text-[15px] font-medium">Changes to watch</legend>
            {WATCH.map((w) => (
              <label key={w.key} className="flex min-h-11 items-center gap-3 text-[17px]">
                <input type="checkbox" className="size-5 accent-ink" checked={watch.includes(w.key)}
                  onChange={(e) => setCard((c) => ({ ...c, watch: { value: e.target.checked ? [...watch, w.key] : watch.filter((x) => x !== w.key), origin: "user" } }))} />
                {w.label}
              </label>
            ))}
          </fieldset>
        )}
      </div>
      {error && <p className="mt-4 rounded-btn bg-lifted p-4 text-charcoal">{error}</p>}
      <div className="mt-6 flex gap-3">
        <button type="button" onClick={() => (step === 0 ? setCard(null) : setStep(step - 1))}
          className="inline-flex min-h-11 items-center rounded-btn border-[1.5px] border-ink bg-white px-6 text-[16px] font-medium">Back</button>
        <button type="button" onClick={() => (step < 2 ? setStep(step + 1) : finish())}
          className="inline-flex min-h-11 items-center rounded-btn border-[1.5px] border-ink bg-ink px-6 text-[16px] font-medium text-canvas">
          {step < 2 ? "Next" : "Finish"}
        </button>
      </div>
    </section>
  );
}

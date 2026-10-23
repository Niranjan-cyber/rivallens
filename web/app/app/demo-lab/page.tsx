"use client";

import { useEffect, useState } from "react";
import { ButtonLink, SampleBadge } from "@/components/ui";
import { api, type Mock, type ProfileSummary } from "@/lib/api";

const SCENARIOS = [
  { id: "cosmetic", label: "Cosmetic-only redesign", hint: "Menu order, banner text, styling and a clock change. Should all be ignored." },
  { id: "price_cut_40", label: "Cut Pro price 40%", hint: "The middle plan drops 40%. Should be one meaningful change." },
  { id: "add_feature", label: "Add a feature", hint: "Adds “Mumbai region” to the middle plan." },
  { id: "positioning", label: "Change positioning", hint: "Replaces the headline with a new pitch." },
] as const;

// S-18: change the fictional competitors' pages on purpose, then run monitoring to see what is caught or ignored.
export default function DemoLab() {
  const [mocks, setMocks] = useState<Mock[] | null>(null);
  const [dashboard, setDashboard] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);

  useEffect(() => {
    api<{ mocks: Mock[] }>("/api/v1/demo/mocks").then((r) => setMocks(r.mocks), (e: Error) => setMessage(e.message));
    api<ProfileSummary[]>("/api/v1/profiles").then((ps) => {
      const p = ps.find((x) => x.name === "StackNest");
      if (p) setDashboard(`/app/${p.id}/dashboard`);
    }, () => {});
  }, []);

  async function apply(slug: string, scenario: string, label: string) {
    const r = await api<{ version: string[] }>(`/api/v1/demo/mocks/${slug}/scenario`, { method: "POST", body: JSON.stringify({ scenario }) })
      .catch((e: Error) => (setMessage(e.message), null));
    if (!r) return;
    setMocks((ms) => ms?.map((m) => (m.slug === slug ? { ...m, version: r.version } : m)) ?? null);
    setMessage(`Applied “${label}”. Now run monitor on the StackNest dashboard.`);
  }

  async function reset() {
    await api("/api/v1/demo/mocks/reset", { method: "POST", body: "{}" }).then(
      () => {
        setMocks((ms) => ms?.map((m) => ({ ...m, version: ["v1"] })) ?? null);
        setMessage("All demo pages are back to their original version.");
      },
      (e: Error) => setMessage(e.message),
    );
  }

  return (
    <section data-screen="S-18">
      <div className="flex flex-wrap items-center gap-3">
        <h1 className="text-[32px] leading-tight md:text-[40px]">Demo Lab</h1>
        <SampleBadge label="Fictional companies" />
      </div>
      <p className="mt-3 max-w-[40rem] text-[17px] text-charcoal">
        Change the fictional competitors&apos; pricing pages on purpose, then run monitoring to see what gets caught and what gets ignored.
        Changes stack until you reset.
      </p>
      <div className="mt-6 flex flex-wrap items-center gap-3">
        <button type="button" onClick={reset}
          className="inline-flex min-h-11 items-center rounded-btn border-[1.5px] border-ink bg-white px-6 text-[16px] font-medium">
          Reset all pages
        </button>
        {dashboard && <ButtonLink href={dashboard}>Open StackNest dashboard</ButtonLink>}
      </div>
      <p aria-live="polite" className="mt-4 min-h-6 text-[15px] text-charcoal">{message}</p>

      {!mocks ? (
        <div className="mt-6 h-64 rounded-stadium bg-lifted" aria-busy="true" />
      ) : mocks.length === 0 ? (
        <p className="mt-6 rounded-btn bg-lifted p-6 text-charcoal">The Demo Lab works with the demo account. Log out and choose Try demo account to use it.</p>
      ) : (
        <ul className="mt-6 grid gap-4">
          {mocks.map((m) => (
            <li key={m.slug} className="rounded-stadium bg-lifted p-7">
              <div className="flex flex-wrap items-center justify-between gap-3">
                <div>
                  <p className="text-[24px] font-medium tracking-[-0.02em]">{m.name}</p>
                  <p className="text-[14px] text-slate">
                    Showing: {m.version.length === 1 ? "original page" : m.version.slice(1).map((v) => SCENARIOS.find((s) => s.id === v)?.label ?? v).join(" + ")}
                  </p>
                </div>
                <a href={m.url} target="_blank" rel="noreferrer" className="rounded-pill border border-ink px-4 py-2 text-[15px] font-medium hover:bg-white">
                  View mock page
                </a>
              </div>
              <div className="mt-5 grid gap-3 sm:grid-cols-2">
                {SCENARIOS.map((s) => {
                  const on = m.version.includes(s.id);
                  return (
                    <button key={s.id} type="button" disabled={on} onClick={() => apply(m.slug, s.id, s.label)}
                      className="rounded-btn border-[1.5px] border-ink bg-white p-4 text-left hover:shadow-lift-1 disabled:border-dust disabled:bg-canvas">
                      <span className="block font-medium">{s.label}{on && " (applied)"}</span>
                      <span className="mt-1 block text-[14px] text-slate">{s.hint}</span>
                    </button>
                  );
                })}
              </div>
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}

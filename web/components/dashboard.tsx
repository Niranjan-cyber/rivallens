"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { MarketPulse, SimulateMove } from "@/components/market-extras";
import { RunMonitorButton } from "@/components/run-monitor";
import { SampleBadge } from "@/components/ui";
import { api, type ProfileSummary } from "@/lib/api";
import type { Simulation } from "@/components/simulator";

type RunSummary = { id: string; kind: string; started_at: string; counts: { sources?: number; meaningful?: number; ignored?: number } };

// S-09: the latest picture for one profile and the Run monitor button.
export function Dashboard({ profileId }: { profileId: string }) {
  const [profile, setProfile] = useState<ProfileSummary | null>(null);
  const [runs, setRuns] = useState<RunSummary[]>([]);
  const [unread, setUnread] = useState(0);
  const [sim, setSim] = useState<Simulation | null>(null);

  useEffect(() => {
    api<ProfileSummary[]>("/api/v1/profiles").then((ps) => setProfile(ps.find((p) => p.id === profileId) ?? null), () => {});
    api<RunSummary[]>(`/api/v1/profiles/${profileId}/runs?limit=5`).then(setRuns, () => {});
    api<{ id: string }[]>(`/api/v1/alerts?profile_id=${profileId}&unread=true`).then((a) => setUnread(a.length), () => {});
    api<Simulation>(`/api/v1/profiles/${profileId}/simulation`).then(setSim, () => {});
  }, [profileId]);

  const when = (ts: string) => new Date(ts).toLocaleString("en-IN", { dateStyle: "medium", timeStyle: "short" });

  return (
    <section data-screen="S-09">
      <div className="flex flex-wrap items-center gap-3">
        <h1 className="text-[32px] leading-tight md:text-[40px]">{profile ? `Market: ${profile.name}` : "Market"}</h1>
        {profile?.is_demo_data && <SampleBadge label="Demo data" />}
      </div>
      <p className="mt-2 text-[17px] text-charcoal">{profile?.note}</p>
      <SimulateMove />
      <div className="mt-6"><RunMonitorButton profileId={profileId} /></div>

      <div className="mt-8 grid gap-4 sm:grid-cols-3">
        <Link href={`/app/${profileId}/competitors`} className="rounded-stadium bg-lifted p-7 hover:shadow-lift-1">
          <p className="text-[48px] font-medium leading-none tracking-[-0.03em]">{profile?.competitors_monitored ?? "–"}</p>
          <p className="mt-2 text-[17px]">competitors watched</p>
        </Link>
        <Link href={`/app/${profileId}/alerts`} className="rounded-stadium bg-lifted p-7 hover:shadow-lift-1">
          <p className={`text-[48px] font-medium leading-none tracking-[-0.03em] ${unread ? "text-signal" : ""}`}>{unread}</p>
          <p className="mt-2 text-[17px]">unread alerts</p>
        </Link>
        <Link href={`/app/${profileId}/card`} className="rounded-stadium bg-lifted p-7 hover:shadow-lift-1">
          <p className="text-[24px] font-medium leading-tight tracking-[-0.02em]">Profile card</p>
          <p className="mt-2 text-[17px] text-charcoal">What we compare competitors against</p>
        </Link>
      </div>

      {sim && (
        <Link href={`/app/${profileId}/simulator`} className="mt-4 block rounded-stadium bg-ink p-7 text-canvas hover:shadow-lift-2">
          <p className="text-[15px] text-dust">Launch simulator · scenario model, not a forecast</p>
          <p className="mt-1 text-[28px] font-medium tracking-[-0.02em]">Recommended ₹{sim.recommended_price_inr.toLocaleString("en-IN")}{sim.price_unit ?? "/month"}</p>
          {sim.replanned && <p className="mt-1 text-[15px] text-signal-light">{sim.replanned.summary}</p>}
          {sim.viability_flags.length > 0 && <p className="mt-1 text-[15px] text-dust">{sim.viability_flags.length} viability flag{sim.viability_flags.length > 1 ? "s" : ""}</p>}
        </Link>
      )}

      <h2 className="mt-10 text-[24px] font-medium tracking-[-0.02em]">Recent checks</h2>
      {runs.length === 0 ? (
        <p className="mt-2 text-charcoal">No checks yet. Run monitor saves a baseline of every watched page.</p>
      ) : (
        <ul className="mt-3 divide-y divide-ghost rounded-btn bg-lifted px-6">
          {runs.map((r) => (
            <li key={r.id}>
              <Link href={`/app/${profileId}/run?id=${r.id}`} className="flex flex-wrap justify-between gap-2 py-4 hover:underline">
                <span>{when(r.started_at)}{r.kind === "baseline" && " · baseline"}</span>
                <span className="text-slate">
                  {r.kind === "baseline" ? `${r.counts.sources ?? 0} pages saved` : `${r.counts.meaningful ?? 0} meaningful · ${r.counts.ignored ?? 0} ignored`}
                </span>
              </Link>
            </li>
          ))}
        </ul>
      )}
      <MarketPulse profileId={profileId} />
    </section>
  );
}

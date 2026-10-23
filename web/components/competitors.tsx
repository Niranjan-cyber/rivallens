"use client";

import { useRouter, useSearchParams } from "next/navigation";
import { useCallback, useEffect, useRef, useState } from "react";
import { SampleBadge } from "@/components/ui";
import { api, type Candidate, type Competitor, type Job } from "@/lib/api";

const ORIGIN: Record<string, string> = { ai_suggested: "Found for you", added_by_user: "Added by you", seed: "Demo seed" };
const STEP_LABEL: Record<string, string> = {
  generate_candidates: "AI suggestions", search: "Web search", verify: "Reachable, robots-allowed, India-verified",
  rank: "Ranked by similarity", find_pages: "Pricing pages found", classify: "Comparable vs inspiration",
};
const btn = "inline-flex min-h-11 items-center rounded-btn border-[1.5px] border-ink px-6 text-[16px] font-medium disabled:opacity-50";

async function waitForJob(id: string, onSteps: (s: Job["steps"]) => void): Promise<Job> {
  for (let i = 0; i < 150; i++) {
    const job = await api<Job>(`/api/v1/jobs/${id}`);
    onSteps(job.steps);
    if (["done", "failed", "stale"].includes(job.status)) return job;
    await new Promise((r) => setTimeout(r, 1000));
  }
  throw new Error("This is taking longer than usual. Refresh in a minute.");
}

// S-07 (discovery progress) and S-08 (competitor list) for one profile.
export function Competitors({ profileId }: { profileId: string }) {
  const router = useRouter();
  const autoStart = useSearchParams().get("discover") === "1";
  const started = useRef(false);
  const [list, setList] = useState<Competitor[] | null>(null);
  const [cands, setCands] = useState<Candidate[]>([]);
  const [tab, setTab] = useState<"comparable" | "inspiration">("comparable");
  const [steps, setSteps] = useState<Job["steps"] | null>(null);
  const [busy, setBusy] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);
  const [url, setUrl] = useState("");

  const load = useCallback(() => {
    api<Competitor[]>(`/api/v1/profiles/${profileId}/competitors`).then(setList, (e: Error) => setMessage(e.message));
    api<Candidate[]>(`/api/v1/profiles/${profileId}/discovery-candidates`).then(setCands, () => {});
  }, [profileId]);

  const discover = useCallback(async () => {
    setMessage(null);
    setBusy("Finding competitors…");
    try {
      const { job_id } = await api<{ job_id: string }>(`/api/v1/profiles/${profileId}/discovery`, { method: "POST", body: "{}" });
      const job = await waitForJob(job_id, setSteps);
      if (job.status !== "done") throw new Error(job.error?.message ?? "Discovery stopped early. Add competitors by URL below.");
      const r = job.result as { verified?: number } | null;
      setMessage(r?.verified ? `${r.verified} competitors found and verified for India.` : "No competitor passed every check this time. Add one by URL below.");
    } catch (e) {
      setMessage((e as Error).message);
    }
    setBusy(null);
    load();
  }, [profileId, load]);

  useEffect(() => {
    load();
    if (autoStart && !started.current) {
      started.current = true;
      discover();
    }
  }, [load, autoStart, discover]);

  async function add() {
    setMessage(null);
    setBusy("Checking that page…");
    await api<Competitor>(`/api/v1/profiles/${profileId}/competitors`, { method: "POST", body: JSON.stringify({ url }) }).then(
      (c) => (setUrl(""), setTab(c.relation), setMessage(`${c.name} added.`)),
      (e: Error) => setMessage(e.message),
    );
    setBusy(null);
    load();
  }

  async function toggle(c: Competitor) {
    const u = await api<Competitor>(`/api/v1/competitors/${c.id}`, { method: "PATCH", body: JSON.stringify({ selected: !c.selected }) }).catch(() => null);
    if (u) setList((l) => l?.map((x) => (x.id === u.id ? u : x)) ?? null);
  }

  async function startMonitoring() {
    setMessage(null);
    setBusy("Saving a baseline of every selected page…");
    try {
      const { job_id } = await api<{ job_id: string }>(`/api/v1/profiles/${profileId}/monitoring/start`, { method: "POST", body: "{}" });
      const job = await waitForJob(job_id, () => {});
      if (job.status !== "done") throw new Error(job.error?.message ?? "The baseline run stopped early.");
      router.push(`/app/${profileId}/run?id=${(job.result as { run_id: string }).run_id}`);
    } catch (e) {
      setMessage((e as Error).message);
      setBusy(null);
    }
  }

  const shown = list?.filter((c) => c.relation === tab) ?? [];
  const rejected = cands.filter((c) => c.status === "rejected");

  return (
    <section data-screen="S-08">
      <h1 className="text-[32px] leading-tight md:text-[40px]">Competitors</h1>
      <p className="mt-3 max-w-[40rem] text-[17px] text-charcoal">
        Found automatically for the Indian market: each one was reachable, allowed us in robots.txt and showed India signals. Untick any you don&apos;t want watched.
      </p>
      <div className="mt-6 flex flex-wrap gap-3">
        <button type="button" onClick={discover} disabled={busy !== null} className={`${btn} bg-ink text-canvas`}>Find competitors</button>
        <button type="button" onClick={startMonitoring} disabled={busy !== null || !list?.some((c) => c.selected)} className={`${btn} bg-white`}>Start monitoring</button>
      </div>
      <p aria-live="polite" className="mt-3 min-h-6 text-[15px] text-charcoal">{busy ?? message}</p>

      {steps && steps.length > 0 && (
        <ol data-screen="S-07" className="mt-2 grid gap-1 rounded-btn bg-lifted p-5 text-[15px]">
          {Object.entries(steps.reduce<Record<string, Job["steps"][number]>>((acc, s) => ({ ...acc, [s.name]: s }), {})).map(([name, s]) => (
            <li key={name} className="flex justify-between gap-4">
              <span>{STEP_LABEL[name] ?? name}{s.status === "skipped" && " (skipped)"}</span>
              <span className="text-slate">{s.status === "running" ? "…" : s.count ?? ""}</span>
            </li>
          ))}
        </ol>
      )}

      <div role="tablist" className="mt-6 flex gap-2">
        {(["comparable", "inspiration"] as const).map((t) => (
          <button key={t} role="tab" aria-selected={tab === t} type="button" onClick={() => setTab(t)}
            className={`rounded-pill border px-4 py-1.5 text-[15px] capitalize ${tab === t ? "border-ink bg-ink text-canvas" : "border-ink/30 bg-white"}`}>
            {t} ({list?.filter((c) => c.relation === t).length ?? 0})
          </button>
        ))}
      </div>
      {!list ? (
        <div className="mt-4 h-40 rounded-stadium bg-lifted" aria-busy="true" />
      ) : shown.length === 0 ? (
        <p className="mt-4 rounded-btn bg-lifted p-6 text-charcoal">None yet. Find competitors, or add one by URL below.</p>
      ) : (
        <ul className="mt-4 grid gap-3">
          {shown.map((c) => (
            <li key={c.id} className="flex gap-4 rounded-btn bg-lifted p-5">
              <input type="checkbox" checked={c.selected} onChange={() => toggle(c)} aria-label={`Watch ${c.name}`} className="mt-1 size-5 shrink-0 accent-ink" />
              <div className="min-w-0">
                <p className="flex flex-wrap items-center gap-2 text-[18px] font-medium">
                  {c.name}
                  {c.is_demo_data && <SampleBadge label="Demo data" />}
                  <span className="text-[13px] font-normal text-slate">{ORIGIN[c.origin] ?? c.origin}</span>
                </p>
                <p className="text-[14px] text-slate">
                  {c.domain}
                  {c.similarity != null && ` · similarity ${c.similarity.toFixed(2)}`}
                  {c.india_signals?.hits?.length ? ` · India: ${c.india_signals.hits.join(", ")}` : c.origin === "added_by_user" ? " · India unverified" : ""}
                </p>
                {c.sources[0] && <p className="truncate text-[14px]"><a href={c.sources[0].url} target="_blank" rel="noreferrer" className="text-link underline">{c.sources[0].page_type} page</a></p>}
              </div>
            </li>
          ))}
        </ul>
      )}

      <div className="mt-8 max-w-[40rem]">
        <label className="text-[15px] font-medium" htmlFor="add-url">Add a competitor by URL</label>
        <div className="mt-1 flex gap-2">
          <input id="add-url" value={url} onChange={(e) => setUrl(e.target.value)} placeholder="https://competitor.com/pricing"
            className="min-w-0 flex-1 rounded-[14px] border border-ink/30 bg-white px-4 py-2.5 text-[16px]" />
          <button type="button" onClick={add} disabled={!url.trim() || busy !== null} className={`${btn} bg-white`}>Add</button>
        </div>
      </div>

      {rejected.length > 0 && (
        <details className="mt-8">
          <summary className="cursor-pointer text-[15px] font-medium">Checked and left out ({rejected.length})</summary>
          <ul className="mt-3 divide-y divide-ghost rounded-btn bg-lifted px-5">
            {rejected.map((c) => (
              <li key={c.id} className="py-3 text-[15px]">
                <span className="font-medium">{c.domain}</span>
                <span className="block text-slate">{c.reasons.join("; ")}</span>
              </li>
            ))}
          </ul>
        </details>
      )}
    </section>
  );
}

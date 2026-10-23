"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";
import { api, type Job } from "@/lib/api";

// S-09 "Run monitor": start a run, poll its job, then open the S-10 result.
export function RunMonitorButton({ profileId }: { profileId: string }) {
  const router = useRouter();
  const [progress, setProgress] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function start() {
    setError(null);
    setProgress("Starting…");
    try {
      const { job_id } = await api<{ job_id: string }>(`/api/v1/profiles/${profileId}/runs`, { method: "POST", body: "{}" });
      for (let i = 0; i < 90; i++) {
        const job = await api<Job>(`/api/v1/jobs/${job_id}`);
        const pages = job.steps.filter((s) => s.name === "source").length;
        const total = job.steps.find((s) => s.name === "fetch")?.count;
        setProgress(total ? `Checked ${pages} of ${total} pages` : "Starting…");
        if (job.status === "done") return router.push(`/app/${profileId}/run?id=${job.result?.run_id}`);
        if (job.status === "failed" || job.status === "stale") throw new Error(job.error?.message ?? "The check stopped before finishing.");
        await new Promise((r) => setTimeout(r, 1000));
      }
      throw new Error("The check is taking longer than usual. Open Monitoring run in a minute to see it.");
    } catch (e) {
      setError((e as Error).message);
      setProgress(null);
    }
  }

  return (
    <div className="flex flex-wrap items-center gap-4">
      <button type="button" onClick={start} disabled={progress !== null}
        className="inline-flex min-h-11 items-center justify-center rounded-btn border-[1.5px] border-ink bg-ink px-6 text-[16px] font-medium tracking-[-0.02em] text-canvas active:translate-y-px disabled:opacity-60">
        {progress ? "Checking pages…" : "Check competitors now"}
      </button>
      <p aria-live="polite" className="text-[15px] text-slate">{error ?? progress}</p>
    </div>
  );
}

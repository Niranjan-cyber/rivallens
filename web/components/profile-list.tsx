"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { SampleBadge } from "@/components/ui";
import { api, type ProfileSummary } from "@/lib/api";

export function ProfileList() {
  const [profiles, setProfiles] = useState<ProfileSummary[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api<ProfileSummary[]>("/api/v1/profiles").then(setProfiles, (e: Error) => setError(e.message));
  }, []);

  if (error) return <p className="mt-8 rounded-btn bg-lifted p-6 text-charcoal">{error}</p>;
  if (!profiles)
    return (
      <ul className="mt-8 grid gap-4 sm:grid-cols-2" aria-busy="true">
        {[0, 1, 2, 3].map((i) => <li key={i} className="h-36 rounded-stadium bg-lifted" />)}
      </ul>
    );

  return (
    <ul className="mt-8 grid gap-4 sm:grid-cols-2">
      {profiles.map((p) => (
        <li key={p.id}>
          <Link href={`/app/${p.id}/dashboard`} className="block rounded-stadium bg-lifted p-7 hover:shadow-lift-2">
            <div className="flex items-center justify-between gap-3">
              <p className="text-[14px] text-slate">
                {p.kind === "idea" ? "Idea" : "Business"} · {p.offering_type}
              </p>
              {p.is_demo_data && <SampleBadge label="Demo data" />}
            </div>
            <p className="mt-1 text-[24px] font-medium tracking-[-0.02em]">{p.name}</p>
            <p className="mt-1 text-charcoal">{p.note}</p>
            <p className="mt-4 text-[14px] text-slate">
              {p.competitors_monitored} competitors watched · {p.last_run_at ? `last checked ${new Date(p.last_run_at).toLocaleString("en-IN")}` : "not checked yet"}
            </p>
          </Link>
        </li>
      ))}
    </ul>
  );
}

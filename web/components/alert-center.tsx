"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { BucketPill } from "@/components/alert-bell";
import { SampleBadge } from "@/components/ui";
import { api, type Alert } from "@/lib/api";

const EMAIL = { sent: "Emailed", failed: "Email failed", skipped: "Email not set up", not_sent: "" };
const FILTERS = [
  { label: "All", q: "" },
  { label: "Unread", q: "&unread=true" },
  { label: "High", q: "&bucket=high" },
  { label: "Prices", q: "&type=price" },
  { label: "Features", q: "&type=feature" },
] as const;

// S-16: every alert for this profile, newest first, each linked to its receipt.
export function AlertCenter({ profileId }: { profileId: string }) {
  const [filter, setFilter] = useState<string>("");
  const [alerts, setAlerts] = useState<Alert[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api<Alert[]>(`/api/v1/alerts?profile_id=${profileId}${filter}`).then(setAlerts, (e: Error) => setError(e.message));
  }, [profileId, filter]);

  async function patch(a: Alert, body: object) {
    const updated = await api<Alert>(`/api/v1/alerts/${a.id}`, { method: "PATCH", body: JSON.stringify(body) }).catch((e: Error) => (setError(e.message), null));
    if (updated) setAlerts((all) => all?.map((x) => (x.id === a.id ? updated : x)) ?? null);
  }

  return (
    <section data-screen="S-16">
      <div className="flex flex-wrap items-center gap-3">
        <h1 className="text-[32px] leading-tight md:text-[40px]">Alerts</h1>
        <SampleBadge label="Demo data" />
      </div>
      <p className="mt-3 max-w-[40rem] text-[17px] text-charcoal">
        Changes that passed your rules, ranked by priority. A repeat of the same change is counted, not alerted again.
      </p>
      <div role="group" aria-label="Filter alerts" className="mt-6 flex flex-wrap gap-2">
        {FILTERS.map((f) => (
          <button key={f.label} type="button" onClick={() => setFilter(f.q)} aria-pressed={filter === f.q}
            className={`rounded-pill border px-4 py-1.5 text-[15px] ${filter === f.q ? "border-ink bg-ink text-canvas" : "border-ink/30 bg-white"}`}>
            {f.label}
          </button>
        ))}
      </div>
      {error && <p className="mt-4 rounded-btn bg-lifted p-4 text-charcoal">{error}</p>}
      {!alerts ? (
        <div className="mt-6 h-48 rounded-stadium bg-lifted" aria-busy="true" />
      ) : alerts.length === 0 ? (
        <p className="mt-6 rounded-btn bg-lifted p-6 text-charcoal">No alerts here. Try the Demo Lab: cut a price, then run monitor.</p>
      ) : (
        <ul className="mt-6 grid gap-3">
          {alerts.map((a) => (
            <li key={a.id} className={`rounded-btn p-5 ${a.read ? "bg-lifted" : "border-[1.5px] border-ink bg-white"}`}>
              <div className="flex flex-wrap items-center gap-2 text-[13px] text-slate">
                <BucketPill bucket={a.bucket} />
                <span>priority {a.priority}</span>
                {a.seen_again > 0 && <span>· seen again {a.seen_again}×</span>}
                {EMAIL[a.email_status] && <span>· {EMAIL[a.email_status]}</span>}
              </div>
              <Link href={`/app/${profileId}/receipt?id=${a.change_event_id}`} onClick={() => !a.read && patch(a, { read: true })}
                className="mt-2 block text-[17px] leading-snug hover:underline">
                {a.text}
              </Link>
              <div className="mt-3 flex flex-wrap gap-2 text-[14px]">
                <button type="button" onClick={() => patch(a, { read: !a.read })} className="rounded-pill border border-ink/30 px-3 py-1 hover:border-ink">
                  Mark {a.read ? "unread" : "read"}
                </button>
                <button type="button" onClick={() => patch(a, { mute: "competitor" })} className="rounded-pill border border-ink/30 px-3 py-1 hover:border-ink">
                  Mute this competitor
                </button>
              </div>
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}

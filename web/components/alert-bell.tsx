"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useEffect, useRef, useState } from "react";
import { api, type Alert } from "@/lib/api";

const BUCKET_STYLE = { high: "bg-signal text-white", medium: "bg-ghost text-ink", low: "bg-canvas text-slate" };

export function BucketPill({ bucket }: { bucket: Alert["bucket"] }) {
  return <span className={`rounded-pill px-2.5 py-0.5 text-[13px] font-medium capitalize ${BUCKET_STYLE[bucket]}`}>{bucket}</span>;
}

// Header bell: unread count polled every 15 s, top five alerts in a dropdown.
export function AlertBell() {
  const pathname = usePathname();
  const router = useRouter();
  const box = useRef<HTMLDetailsElement>(null);
  const [data, setData] = useState<{ count: number; top: Alert[] }>({ count: 0, top: [] });

  useEffect(() => {
    const load = () => api<{ count: number; top: Alert[] }>("/api/v1/alerts/unread-count").then(setData, () => {});
    load();
    const t = setInterval(load, 15000);
    return () => clearInterval(t);
  }, [pathname]);

  const profileId = pathname.match(/^\/app\/([0-9a-f-]{36})/)?.[1] ?? data.top[0]?.profile_id;

  async function open(a: Alert) {
    box.current?.removeAttribute("open");
    await api(`/api/v1/alerts/${a.id}`, { method: "PATCH", body: JSON.stringify({ read: true }) }).catch(() => {});
    setData((d) => ({ count: Math.max(d.count - 1, 0), top: d.top.filter((x) => x.id !== a.id) }));
    router.push(`/app/${a.profile_id}/receipt?id=${a.change_event_id}`);
  }

  return (
    <details ref={box} className="relative">
      <summary aria-label={`Alerts, ${data.count} unread`} className="relative flex size-11 cursor-pointer list-none items-center justify-center rounded-full border border-ink">
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" aria-hidden="true">
          <path d="M6 16V11a6 6 0 1 1 12 0v5l1.5 2h-15L6 16Z" />
          <path d="M10 20a2 2 0 0 0 4 0" />
        </svg>
        {data.count > 0 && (
          <span className="absolute -right-1 -top-1 flex min-w-5 items-center justify-center rounded-pill bg-signal px-1.5 text-[12px] font-bold leading-5 text-white">
            {data.count}
          </span>
        )}
      </summary>
      <div className="absolute right-0 z-20 mt-2 w-[min(22rem,calc(100vw-2rem))] rounded-[24px] bg-white p-3 shadow-lift-2">
        {data.top.length === 0 ? (
          <p className="px-3 py-4 text-[15px] text-slate">No unread alerts. Run monitor to check for changes.</p>
        ) : (
          <ul>
            {data.top.map((a) => (
              <li key={a.id}>
                <button type="button" onClick={() => open(a)} className="block w-full rounded-[16px] px-3 py-3 text-left hover:bg-canvas">
                  <span className="flex items-center gap-2"><BucketPill bucket={a.bucket} /><span className="text-[13px] text-slate">priority {a.priority}</span></span>
                  <span className="mt-1 block text-[15px] leading-snug">{a.text}</span>
                </button>
              </li>
            ))}
          </ul>
        )}
        {profileId && (
          <Link href={`/app/${profileId}/alerts`} onClick={() => box.current?.removeAttribute("open")}
            className="mt-1 block rounded-pill px-3 py-2 text-center text-[15px] font-medium hover:bg-canvas">
            View all alerts
          </Link>
        )}
      </div>
    </details>
  );
}

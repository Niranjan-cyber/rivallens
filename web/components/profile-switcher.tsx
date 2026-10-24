"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useEffect, useState } from "react";
import { api, type ProfileSummary } from "@/lib/api";
import { supabase } from "@/lib/supabase";

export function ProfileSwitcher() {
  const pathname = usePathname();
  const [profiles, setProfiles] = useState<ProfileSummary[]>([]);
  const [isGuest, setIsGuest] = useState(false);

  useEffect(() => {
    api<ProfileSummary[]>("/api/v1/profiles").then(setProfiles, () => setProfiles([]));
    supabase.auth.getUser().then(({ data }) => setIsGuest(Boolean(data.user?.is_anonymous)));
  }, [pathname]);

  const current = profiles.find((p) => pathname.startsWith(`/app/${p.id}`));

  return (
    <details className="relative">
      <summary className="cursor-pointer list-none rounded-pill border border-ink/20 px-4 py-2 text-[15px]">
        {current ? current.name : "All businesses"} ▾
      </summary>
      <div className="absolute right-0 mt-2 w-64 rounded-[24px] bg-white p-2 shadow-lift-2">
        <Link href="/app" className="block rounded-pill px-4 py-2 hover:bg-canvas">All businesses</Link>
        {profiles.map((p) => (
          <Link key={p.id} href={`/app/${p.id}/home`} className="block rounded-pill px-4 py-2 hover:bg-canvas">{p.name}</Link>
        ))}
        <Link href="/app/new" className="block rounded-pill px-4 py-2 hover:bg-canvas">Add a business</Link>
        {!isGuest && <Link href="/reset" className="block rounded-pill px-4 py-2 hover:bg-canvas">Change password</Link>}
        <button type="button" onClick={() => supabase.auth.signOut()} className="mt-1 block w-full rounded-pill px-4 py-2 text-left text-slate hover:bg-canvas">
          {isGuest ? "Leave demo" : "Log out"}
        </button>
      </div>
    </details>
  );
}

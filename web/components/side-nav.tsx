"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { SAMPLE_PROFILE, sections } from "@/lib/screens";

export function SideNav() {
  const parts = usePathname().split("/");
  const profileId = parts[2] && !["new", "demo-lab"].includes(parts[2]) ? parts[2] : SAMPLE_PROFILE;
  const active = parts[3];

  return (
    <nav aria-label="Profile sections" className="flex gap-2 overflow-x-auto md:flex-col md:overflow-visible">
      {sections.map((s) => {
        const on = active === s.slug;
        return (
          <Link
            key={s.slug}
            href={`/app/${profileId}/${s.slug}`}
            aria-current={on ? "page" : undefined}
            className={`shrink-0 rounded-pill px-5 py-2.5 text-[15px] font-medium tracking-[-0.02em] ${on ? "bg-ink text-canvas" : "hover:bg-white"}`}
          >
            {s.label}
          </Link>
        );
      })}
    </nav>
  );
}

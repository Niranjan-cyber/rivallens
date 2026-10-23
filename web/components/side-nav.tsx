"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { groupOf, groups, sections } from "@/lib/screens";

const groupHome: Record<string, string> = { home: "home", product: "product", money: "money", market: "dashboard", customers: "customers" };

// Four dashboards plus the overview; the active dashboard expands to its own pages.
export function SideNav() {
  const parts = usePathname().split("/");
  const profileId = parts[2] && !["new", "demo-lab"].includes(parts[2]) ? parts[2] : null;
  const active = parts[3];
  if (!profileId) return null; // onboarding and the business list have no dashboards yet
  const activeGroup = groupOf[active];
  const pill = (on: boolean) => `shrink-0 rounded-pill px-5 py-2.5 text-[15px] font-medium tracking-[-0.02em] ${on ? "bg-ink text-canvas" : "hover:bg-white"}`;

  return (
    <nav aria-label="Dashboards" className="flex gap-2 overflow-x-auto md:flex-col md:overflow-visible">
      {groups.map((g) => {
        const children = sections.filter((s) => groupOf[s.slug] === g.key && s.slug !== groupHome[g.key]);
        const open = activeGroup === g.key;
        return (
          <div key={g.key} className="contents md:block">
            <Link href={`/app/${profileId}/${groupHome[g.key]}`} aria-current={active === groupHome[g.key] ? "page" : undefined}
              className={pill(open && (active === groupHome[g.key] || children.length === 0))}>
              {g.label}
            </Link>
            {open && children.length > 0 && (
              <div className="contents md:ml-4 md:mt-1 md:flex md:flex-col md:gap-1">
                {children.map((s) => (
                  <Link key={s.slug} href={`/app/${profileId}/${s.slug}`} aria-current={active === s.slug ? "page" : undefined}
                    className={`shrink-0 rounded-pill px-4 py-2 text-[14px] ${active === s.slug ? "bg-ink text-canvas" : "text-charcoal hover:bg-white"}`}>
                    {s.label}
                  </Link>
                ))}
              </div>
            )}
          </div>
        );
      })}
    </nav>
  );
}

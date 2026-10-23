import type { ReactNode } from "react";
import { SampleBadge } from "@/components/ui";

// Placeholder for screens that later build steps make real.
export function StubPage({ title, purpose, screen, children }: { title: string; purpose: string; screen: string; children?: ReactNode }) {
  return (
    <section data-screen={screen}>
      <div className="flex flex-wrap items-center gap-3">
        <h1 className="text-[32px] leading-tight md:text-[40px]">{title}</h1>
        <SampleBadge />
      </div>
      <p className="mt-3 max-w-[40rem] text-[17px] text-charcoal">{purpose}</p>
      <div className="mt-8 grid gap-4 sm:grid-cols-2">
        <div className="h-40 rounded-stadium bg-lifted" />
        <div className="h-40 rounded-stadium bg-lifted" />
      </div>
      {children && <div className="mt-8 flex flex-wrap gap-3">{children}</div>}
    </section>
  );
}

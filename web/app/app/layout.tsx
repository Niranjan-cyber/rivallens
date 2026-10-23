import Link from "next/link";
import { Suspense } from "react";
import { SideNav } from "@/components/side-nav";
import { Logo } from "@/components/ui";

export default function AppLayout({ children }: LayoutProps<"/app">) {
  return (
    <div className="mx-auto w-full max-w-[1280px] px-4 pb-16 sm:px-8">
      <header className="sticky top-4 z-10 mt-4">
        <div className="flex items-center justify-between gap-3 rounded-pill bg-white px-5 py-2.5 shadow-lift-1 sm:px-8">
          <Logo />
          <div className="flex items-center gap-2">
            <Link href="/app" className="hidden rounded-pill border border-ink/20 px-4 py-2 text-[15px] sm:block">
              StackNest (demo) ▾
            </Link>
            <Link href="/app/demo-lab" className="rounded-pill px-4 py-2 text-[15px] font-medium hover:bg-canvas">
              Demo Lab
            </Link>
            <button type="button" aria-label="Alerts" className="flex size-11 items-center justify-center rounded-full border border-ink">
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" aria-hidden="true">
                <path d="M6 16V11a6 6 0 1 1 12 0v5l1.5 2h-15L6 16Z" />
                <path d="M10 20a2 2 0 0 0 4 0" />
              </svg>
            </button>
          </div>
        </div>
      </header>
      <div className="mt-8 grid gap-8 md:grid-cols-[200px_1fr]">
        <aside className="md:sticky md:top-28 md:self-start">
          <Suspense fallback={<div className="h-10 md:h-80" />}>
            <SideNav />
          </Suspense>
        </aside>
        <main>{children}</main>
      </div>
    </div>
  );
}

import { Suspense } from "react";
import { AlertBell } from "@/components/alert-bell";
import { AuthGate } from "@/components/auth-gate";
import { ProfileSwitcher } from "@/components/profile-switcher";
import { SideNav } from "@/components/side-nav";
import { Logo } from "@/components/ui";

export default function AppLayout({ children }: LayoutProps<"/app">) {
  return (
    <div className="mx-auto w-full max-w-[1280px] px-4 pb-16 sm:px-8">
      <header className="sticky top-4 z-10 mt-4 print:hidden">
        <div className="flex items-center justify-between gap-3 rounded-pill bg-white px-5 py-2.5 shadow-lift-1 sm:px-8">
          <Logo />
          <div className="flex items-center gap-2">
            <Suspense>
              <ProfileSwitcher />
            </Suspense>
            <Suspense fallback={<div className="size-11 rounded-full border border-ink" />}>
              <AlertBell />
            </Suspense>
          </div>
        </div>
      </header>
      <div className="mt-8 grid grid-cols-1 gap-8 md:grid-cols-[200px_1fr] print:mt-0 print:block">
        <aside className="min-w-0 md:sticky md:top-28 md:self-start print:hidden">
          <Suspense fallback={<div className="h-10 md:h-80" />}>
            <SideNav />
          </Suspense>
        </aside>
        <main className="min-w-0">
          <AuthGate>{children}</AuthGate>
        </main>
      </div>
    </div>
  );
}

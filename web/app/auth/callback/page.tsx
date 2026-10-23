"use client";

import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { Logo } from "@/components/ui";
import { supabase } from "@/lib/supabase";

// Landing page for email-confirmation and Google sign-in links. supabase-js reads the
// tokens (or ?code=) from the URL on load; we wait for the session and move on.
export default function AuthCallback() {
  const router = useRouter();
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const params = new URLSearchParams(window.location.hash.slice(1) || window.location.search);
    const failed = params.get("error_description");
    const code = new URLSearchParams(window.location.search).get("code");
    const ready = code ? supabase.auth.exchangeCodeForSession(code).then(({ error }) => error) : Promise.resolve(null);
    ready.then(async (err) => {
      if (failed) return setError(failed.replace(/\+/g, " "));
      const { data } = await supabase.auth.getSession();
      if (data.session) return router.replace("/app");
      setError(err?.message ?? "This sign-in link has expired or was already used. Log in again.");
    });
  }, [router]);

  return (
    <main data-screen="S-02" className="mx-auto flex w-full max-w-[440px] flex-1 flex-col justify-center px-4 py-16">
      <Logo />
      <div className="mt-10 rounded-stadium bg-white p-8 shadow-lift-2">
        {error ? (
          <>
            <h1 className="text-[22px]">Couldn&apos;t sign you in</h1>
            <p role="alert" className="mt-3 text-[15px] text-charcoal">{error}</p>
            <a href="/login" className="mt-6 inline-flex min-h-11 items-center rounded-btn border-[1.5px] border-ink bg-ink px-6 text-[16px] font-medium text-canvas">Back to log in</a>
          </>
        ) : (
          <p className="text-[16px]">Signing you in…</p>
        )}
      </div>
    </main>
  );
}

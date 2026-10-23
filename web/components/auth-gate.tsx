"use client";

import { useRouter } from "next/navigation";
import { useEffect, useState, type ReactNode } from "react";
import { supabase } from "@/lib/supabase";

// Client-side gate: app screens need a session (real or anonymous demo); otherwise go to /login.
export function AuthGate({ children }: { children: ReactNode }) {
  const router = useRouter();
  const [ready, setReady] = useState(false);

  useEffect(() => {
    supabase.auth.getSession().then(({ data }) => (data.session ? setReady(true) : router.replace("/login")));
    const { data } = supabase.auth.onAuthStateChange((_e, session) => {
      if (!session) router.replace("/login");
    });
    return () => data.subscription.unsubscribe();
  }, [router]);

  return ready ? children : <div className="h-40 rounded-stadium bg-lifted" aria-busy="true" />;
}

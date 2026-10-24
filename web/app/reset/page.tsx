"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useState, type FormEvent } from "react";
import { Logo } from "@/components/ui";
import { supabase } from "@/lib/supabase";

// Set a new password: from the reset email's link (the session arrives in the URL), or while signed in ("Change password").
export default function ResetPassword() {
  const router = useRouter();
  const [email, setEmail] = useState<string | null | undefined>(undefined); // undefined: still checking
  const [message, setMessage] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    supabase.auth.getSession().then(({ data }) => setEmail(data.session?.user.email ?? null));
    const { data } = supabase.auth.onAuthStateChange((_e, session) => setEmail(session?.user.email ?? null));
    return () => data.subscription.unsubscribe();
  }, []);

  async function submit(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    const f = new FormData(e.currentTarget);
    const password = String(f.get("password"));
    if (password !== String(f.get("confirm"))) return setMessage("The two passwords don't match.");
    setBusy(true);
    const { error } = await supabase.auth.updateUser({ password });
    setBusy(false);
    if (error) return setMessage(error.message);
    setMessage("Password changed. Taking you to your businesses…");
    setTimeout(() => router.push("/app"), 1200);
  }

  const field = "mt-1 w-full rounded-pill border border-ink/30 bg-white px-5 py-3 text-[16px] outline-none focus:border-ink";
  const demo = email?.endsWith("@rivallens.demo");
  return (
    <main data-screen="S-03" className="mx-auto flex w-full max-w-[440px] flex-1 flex-col justify-center px-4 py-16">
      <Logo />
      <div className="mt-10 rounded-stadium bg-white p-8 shadow-lift-2">
        <h1 className="text-[24px] font-medium tracking-[-0.02em]">Set a new password</h1>
        {email === undefined ? (
          <p className="mt-4 text-charcoal" aria-busy="true">Checking your link…</p>
        ) : email === null ? (
          <p className="mt-4 text-charcoal">This link has expired or was already used. <Link href="/login" className="underline">Request a new one</Link> from Log in.</p>
        ) : demo ? (
          <p className="mt-4 text-charcoal">Demo businesses are shared with every visitor, so their password can&apos;t be changed. <Link href="/app" className="underline">Back to the app</Link></p>
        ) : (
          <form onSubmit={submit} className="mt-4 space-y-4">
            <p className="text-[14px] text-slate">For {email}</p>
            <label className="block text-[14px] text-charcoal">New password<input name="password" type="password" required minLength={6} autoComplete="new-password" className={field} /></label>
            <label className="block text-[14px] text-charcoal">Type it again<input name="confirm" type="password" required minLength={6} autoComplete="new-password" className={field} /></label>
            <button disabled={busy} className="min-h-11 w-full rounded-btn border-[1.5px] border-ink bg-ink text-[16px] font-medium text-canvas disabled:opacity-60">
              {busy ? "Saving…" : "Save new password"}
            </button>
          </form>
        )}
        {message && <p role="alert" className="mt-4 rounded-btn bg-canvas p-4 text-[14px]">{message}</p>}
      </div>
    </main>
  );
}

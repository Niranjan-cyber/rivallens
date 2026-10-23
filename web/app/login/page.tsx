"use client";

import { useRouter } from "next/navigation";
import { useState, type FormEvent } from "react";
import { Logo } from "@/components/ui";
import { api } from "@/lib/api";
import { supabase } from "@/lib/supabase";

type Mode = "login" | "signup";

export default function Login() {
  const router = useRouter();
  const [mode, setMode] = useState<Mode>("login");
  const [busy, setBusy] = useState<"form" | "demo" | null>(null);
  const [message, setMessage] = useState<string | null>(null);
  const [unconfirmed, setUnconfirmed] = useState<string | null>(null);
  const callback = () => `${window.location.origin}/auth/callback`;

  async function submit(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    const f = new FormData(e.currentTarget);
    const email = String(f.get("email"));
    const password = String(f.get("password"));
    setBusy("form");
    setMessage(null);
    setUnconfirmed(null);
    const { data, error } =
      mode === "login"
        ? await supabase.auth.signInWithPassword({ email, password })
        : await supabase.auth.signUp({ email, password, options: { emailRedirectTo: callback(), data: { name: String(f.get("name") ?? "") } } });
    setBusy(null);
    if (error) {
      if (error.message.includes("already registered")) {
        setMode("login");
        return setMessage("That email already has an account. Log in instead.");
      }
      if (error.code === "email_not_confirmed") {
        setUnconfirmed(email);
        return setMessage("Confirm your email first. The link is in your inbox (check spam too).");
      }
      return setMessage(error.message);
    }
    if (!data.session) {
      setUnconfirmed(email);
      return setMessage(`We sent a confirmation link to ${email}. Open it to finish creating your account.`);
    }
    router.push("/app");
  }

  async function resend() {
    if (!unconfirmed) return;
    const { error } = await supabase.auth.resend({ type: "signup", email: unconfirmed, options: { emailRedirectTo: callback() } });
    setMessage(error ? error.message : `Sent again to ${unconfirmed}.`);
  }

  async function google() {
    setMessage(null);
    const { error } = await supabase.auth.signInWithOAuth({ provider: "google", options: { redirectTo: callback() } });
    if (error) setMessage(error.message.includes("not enabled") ? "Google sign-in isn't switched on yet. Use email for now." : error.message);
  }

  async function tryDemo() {
    setBusy("demo");
    setMessage(null);
    const { error } = await supabase.auth.signInAnonymously();
    if (error) {
      setBusy(null);
      return setMessage(`Demo unavailable: ${error.message}. You can still create an account.`);
    }
    try {
      await api("/api/v1/demo/guest-clone", { method: "POST" });
    } catch (err) {
      // already_cloned means this browser already has its demo copy; anything else is a real failure.
      if (!(err instanceof Error && err.message.includes("already loaded"))) {
        setBusy(null);
        return setMessage(`${(err as Error).message} You can still create an account.`);
      }
    }
    router.push("/app");
  }

  const field = "mt-1 w-full rounded-pill border border-ink/30 bg-white px-5 py-3 text-[16px] outline-none focus:border-ink";

  return (
    <main data-screen="S-02" className="mx-auto flex w-full max-w-[440px] flex-1 flex-col justify-center px-4 py-16">
      <Logo />
      <div className="mt-10 rounded-stadium bg-white p-8 shadow-lift-2">
        <div role="tablist" className="flex gap-2 rounded-pill bg-canvas p-1">
          {(["login", "signup"] as const).map((m) => (
            <button key={m} role="tab" aria-selected={mode === m} type="button" onClick={() => { setMode(m); setMessage(null); }}
              className={`flex-1 rounded-pill py-2 text-[15px] font-medium ${mode === m ? "bg-ink text-canvas" : ""}`}>
              {m === "login" ? "Log in" : "Create account"}
            </button>
          ))}
        </div>
        <form onSubmit={submit} className="mt-6 space-y-4">
          {mode === "signup" && (
            <label className="block text-[14px] text-charcoal">Name<input name="name" autoComplete="name" className={field} /></label>
          )}
          <label className="block text-[14px] text-charcoal">Email<input name="email" type="email" required autoComplete="email" className={field} /></label>
          <label className="block text-[14px] text-charcoal">
            Password
            <input name="password" type="password" required minLength={6} autoComplete={mode === "login" ? "current-password" : "new-password"} className={field} />
          </label>
          <button disabled={busy !== null} className="min-h-11 w-full rounded-btn border-[1.5px] border-ink bg-ink text-[16px] font-medium text-canvas disabled:opacity-60">
            {busy === "form" ? "Working…" : mode === "login" ? "Log in" : "Create account"}
          </button>
        </form>
        <button type="button" onClick={google} disabled={busy !== null}
          className="mt-3 flex min-h-11 w-full items-center justify-center gap-2 rounded-btn border-[1.5px] border-ink bg-white text-[16px] font-medium disabled:opacity-60">
          <svg aria-hidden viewBox="0 0 24 24" className="h-5 w-5"><path fill="#4285F4" d="M23.5 12.3c0-.8-.1-1.6-.2-2.3H12v4.4h6.5a5.6 5.6 0 0 1-2.4 3.6v3h3.9c2.3-2.1 3.5-5.2 3.5-8.7Z"/><path fill="#34A853" d="M12 24c3.2 0 6-1.1 8-2.9l-3.9-3c-1.1.7-2.5 1.2-4.1 1.2-3.1 0-5.8-2.1-6.7-5H1.3v3.1A12 12 0 0 0 12 24Z"/><path fill="#FBBC05" d="M5.3 14.3a7.2 7.2 0 0 1 0-4.6V6.6h-4a12 12 0 0 0 0 10.8l4-3.1Z"/><path fill="#EA4335" d="M12 4.8c1.8 0 3.4.6 4.6 1.8l3.4-3.4A12 12 0 0 0 1.3 6.6l4 3.1c.9-2.9 3.6-4.9 6.7-4.9Z"/></svg>
          Continue with Google
        </button>
        {message && (
          <p role="alert" className="mt-4 rounded-btn bg-canvas p-4 text-[14px]">
            {message}
            {unconfirmed && <> <button type="button" onClick={resend} className="font-medium underline">Resend the email</button></>}
          </p>
        )}
        <div className="mt-6 border-t border-ink/10 pt-6">
          <button type="button" onClick={tryDemo} disabled={busy !== null}
            className="min-h-11 w-full rounded-btn border-[1.5px] border-ink bg-white text-[16px] font-medium disabled:opacity-60">
            {busy === "demo" ? "Loading demo data…" : "Try demo account"}
          </button>
          <p className="mt-2 text-center text-[13px] text-slate">No sign-up. You get a private copy of four demo businesses.</p>
        </div>
      </div>
    </main>
  );
}

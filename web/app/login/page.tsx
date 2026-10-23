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

  // Email and password only, no confirmation email (D-83): the API creates the account, then we sign in with it.
  async function submit(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    const f = new FormData(e.currentTarget);
    const email = String(f.get("email")).trim();
    const password = String(f.get("password"));
    setBusy("form");
    setMessage(null);
    if (mode === "signup") {
      try {
        await api("/api/v1/accounts", { method: "POST", body: JSON.stringify({ email, password, name: String(f.get("name") ?? "") }) });
      } catch (err) {
        setBusy(null);
        if ((err as Error).message.includes("already has an account")) setMode("login");
        return setMessage((err as Error).message);
      }
    }
    const { error } = await supabase.auth.signInWithPassword({ email, password });
    setBusy(null);
    if (error) return setMessage(error.message === "Invalid login credentials" ? "Wrong email or password." : error.message);
    router.push("/app");
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
        {message && (
          <p role="alert" className="mt-4 rounded-btn bg-canvas p-4 text-[14px]">
            {message}
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

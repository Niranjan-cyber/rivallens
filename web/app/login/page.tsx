"use client";

import { useRouter } from "next/navigation";
import { useState, type FormEvent } from "react";
import { Logo } from "@/components/ui";
import { api } from "@/lib/api";
import { supabase } from "@/lib/supabase";

type Mode = "login" | "signup";
const DEMO_PASSWORD = "RivalLens-demo-2026";
const DEMOS = [
  { email: "stride@rivallens.demo", name: "Stride & Co.", what: "Running shoes, Pune" },
  { email: "bakery@rivallens.demo", name: "Kesar Bakehouse", what: "Bakery café, Pune" },
  { email: "stacknest@rivallens.demo", name: "StackNest", what: "App hosting SaaS, Pune" },
  { email: "quickkart@rivallens.demo", name: "QuickKart", what: "Quick commerce, Bengaluru" },
];

export default function Login() {
  const router = useRouter();
  const [mode, setMode] = useState<Mode>("login");
  const [busy, setBusy] = useState<"form" | "demo" | null>(null);
  const [message, setMessage] = useState<string | null>(null);

  // Email and password only, no confirmation email (D-83): the API creates the account, then we sign in with it.
  async function submit(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    const form = e.currentTarget;
    const f = new FormData(form);
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
    form.reset();
    setMode("login"); // Next keeps this page's state, so after logging out it should open clean on Log in
    router.push("/app");
  }

  // B14j: four demo businesses built from real data by api/scripts/build_demo.py (D-76); shared sign-ins, listed in the README.
  async function signInDemo(email: string) {
    setBusy("demo");
    setMessage(null);
    const { error } = await supabase.auth.signInWithPassword({ email, password: DEMO_PASSWORD });
    setBusy(null);
    if (error) return setMessage(`Demo unavailable: ${error.message}. You can still create an account.`);
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
          <p className="text-[14px] font-medium">Or open a demo business</p>
          <p className="mt-1 text-[13px] text-slate">Fictional businesses built from real datasets and public pages. Shared with other visitors.</p>
          <div className="mt-3 grid grid-cols-2 gap-2">
            {DEMOS.map((d) => (
              <button key={d.email} type="button" onClick={() => signInDemo(d.email)} disabled={busy !== null}
                className="rounded-btn border-[1.5px] border-ink bg-white p-3 text-left disabled:opacity-60">
                <span className="block text-[15px] font-medium">{d.name}</span>
                <span className="block text-[12px] text-slate">{d.what}</span>
              </button>
            ))}
          </div>
        </div>
      </div>
    </main>
  );
}

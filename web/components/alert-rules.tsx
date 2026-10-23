"use client";

import { useEffect, useState } from "react";
import { api, type AlertRules } from "@/lib/api";

const TYPES = [
  { key: "price", label: "Price changes" },
  { key: "plan", label: "Plans added or dropped" },
  { key: "feature", label: "Features added or removed" },
  { key: "positioning", label: "Positioning (headline) changes" },
] as const;

// S-17: which changes alert you, and how important they must be.
export function AlertRulesForm({ profileId }: { profileId: string }) {
  const [rules, setRules] = useState<AlertRules | null>(null);
  const [message, setMessage] = useState<string | null>(null);

  useEffect(() => {
    api<AlertRules>(`/api/v1/profiles/${profileId}/alert-rules`).then(setRules, (e: Error) => setMessage(e.message));
  }, [profileId]);

  async function save() {
    if (!rules) return;
    await api<AlertRules>(`/api/v1/profiles/${profileId}/alert-rules`, { method: "PUT", body: JSON.stringify(rules) }).then(
      (r) => (setRules(r), setMessage("Saved. New runs use these rules.")),
      (e: Error) => setMessage(e.message),
    );
  }

  return (
    <section data-screen="S-17">
      <h1 className="text-[32px] leading-tight md:text-[40px]">Settings</h1>
      <p className="mt-3 max-w-[40rem] text-[17px] text-charcoal">Choose which competitor changes alert you. Ignored differences still appear on each monitoring run.</p>
      {!rules ? (
        <div className="mt-6 h-64 rounded-stadium bg-lifted" aria-busy="true" />
      ) : (
        <div className="mt-6 max-w-[40rem] rounded-stadium bg-lifted p-7">
          <fieldset>
            <legend className="text-[20px] font-medium">Alert me about</legend>
            <div className="mt-3 grid gap-2">
              {TYPES.map((t) => (
                <label key={t.key} className="flex min-h-11 cursor-pointer items-center gap-3 text-[17px]">
                  <input type="checkbox" className="size-5 accent-ink" checked={rules.change_types[t.key] ?? true}
                    onChange={(e) => setRules({ ...rules, change_types: { ...rules.change_types, [t.key]: e.target.checked } })} />
                  {t.label}
                </label>
              ))}
            </div>
          </fieldset>
          <label className="mt-6 block">
            <span className="text-[20px] font-medium">Minimum priority: {rules.min_priority}</span>
            <span className="mt-1 block text-[15px] text-slate">High is 70 or more, medium 40 to 69. Changes below this are recorded but don&apos;t alert.</span>
            <input type="range" min={0} max={100} step={5} value={rules.min_priority} className="mt-3 w-full accent-ink"
              onChange={(e) => setRules({ ...rules, min_priority: Number(e.target.value) })} />
          </label>
          <label className="mt-6 flex min-h-11 cursor-pointer items-center gap-3 text-[17px]">
            <input type="checkbox" className="size-5 accent-ink" checked={rules.email_enabled}
              onChange={(e) => setRules({ ...rules, email_enabled: e.target.checked })} />
            Email me high-priority alerts
          </label>
          <div className="mt-6 flex flex-wrap items-center gap-4">
            <button type="button" onClick={save}
              className="inline-flex min-h-11 items-center rounded-btn border-[1.5px] border-ink bg-ink px-6 text-[16px] font-medium text-canvas active:translate-y-px">
              Save rules
            </button>
            <p aria-live="polite" className="text-[15px] text-charcoal">{message}</p>
          </div>
        </div>
      )}
    </section>
  );
}

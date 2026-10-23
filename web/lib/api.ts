import { supabase } from "@/lib/supabase";

// Browser → API calls go straight to Render (architecture §7), so Vercel function timeouts never apply.
export const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

export class ApiError extends Error {
  constructor(public status: number, public code: string, message: string) {
    super(message);
  }
}

export async function api<T>(path: string, init?: RequestInit): Promise<T> {
  const { data } = await supabase.auth.getSession();
  const auth: Record<string, string> = data.session ? { Authorization: `Bearer ${data.session.access_token}` } : {};
  let res: Response;
  try {
    res = await fetch(`${API_BASE}${path}`, { ...init, headers: { "Content-Type": "application/json", ...auth, ...init?.headers } });
  } catch {
    throw new ApiError(0, "network", "The server didn't respond. It may be waking up; try again in a minute.");
  }
  if (!res.ok) {
    const body = await res.json().catch(() => null);
    throw new ApiError(res.status, body?.error?.code ?? "http_error", body?.error?.message ?? `Request failed (${res.status}).`);
  }
  return (res.status === 204 ? undefined : res.json()) as Promise<T>;
}

export type ProfileSummary = {
  id: string;
  name: string;
  kind: "business" | "idea";
  offering_type: "product" | "service";
  note: string;
  competitors_monitored: number;
  unread_alerts: number;
  last_run_at: string | null;
  is_demo_data: boolean;
};

export type Job = {
  id: string;
  kind: string;
  status: "queued" | "running" | "done" | "failed" | "stale";
  steps: { name: string; status: string; count: number | null; detail: string | null; at: string }[];
  result: { run_id?: string } | null;
  error: { code: string; message: string } | null;
};

export type Run = {
  id: string;
  profile_id: string;
  status: string;
  kind: "baseline" | "run";
  started_at: string;
  finished_at: string | null;
  counts: { sources: number; diffs: number; ignored: number; meaningful: number; needs_review: number; failed: number };
  changes: { change_event_id: string; competitor: string; change_type: string; field: string; prev: string | null; curr: string | null; delta_pct: number | null; status: string }[];
  ledger: { source_id: string; competitor: string; section_key: string; reason: string; summary: string }[];
  failures: { source_id: string; status: string; url: string }[];
};

export type Mock = { slug: string; name: string; version: string[]; url: string };

export type Receipt = {
  id: string;
  profile_id: string;
  competitor: { id: string; name: string };
  source_url: string;
  change_type: string;
  field: string;
  prev_display: string | null;
  curr_display: string | null;
  delta_pct: number | null;
  status: "confirmed" | "needs_review";
  observed_at: string;
  prev_observed_at: string | null;
  published_at: string | null;
  wayback_url: string | null;
  is_demo_data: boolean;
  muted: boolean;
  priority: number | null;
  priority_breakdown: { m: number; r: number; s: number; undercut: boolean } | null;
  simulation_impact: { version: number; before: string | null; after: string; summary: string } | null;
};

export type EvidenceSide = { snapshot_id: string; observed_at: string; text_window: string; highlight: { start: number; end: number } | null };
export type Evidence = { before: EvidenceSide | null; after: EvidenceSide | null; sha256: { before: string | null; after: string | null }; evidence_missing: boolean };

export type Alert = {
  id: string;
  profile_id: string;
  change_event_id: string;
  bucket: "high" | "medium" | "low";
  priority: number;
  text: string;
  observed_at: string;
  read: boolean;
  seen_again: number;
  email_status: "not_sent" | "sent" | "failed" | "skipped";
};

export type AlertRules = { change_types: Record<string, boolean>; min_priority: number; email_enabled: boolean };

export type Candidate = { id: string; name: string; domain: string; origin: string; status: "verified" | "rejected"; reasons: string[]; india_signals: { score: number; hits: string[] }; similarity: number | null };
export type Competitor = {
  id: string; name: string; domain: string; relation: "comparable" | "inspiration"; origin: string; selected: boolean; monitorable: boolean;
  india_signals: { score?: number; hits?: string[] }; similarity: number | null; is_demo_data: boolean; sources: { id: string; url: string; page_type: string }[];
};

export type Product = {
  id: string;
  profile_id: string;
  name: string;
  stage: "existing" | "new";
  description: string | null;
  url: string | null;
  taxonomy_id: number | null;
  category_path: string | null;
  niche: string | null;
  category_source: "ai" | "top_match" | "user" | "none";
  price: number | null;
  currency: string;
  unit: string;
  unit_cost: number | null;
  features: string[];
  add_ons: string[];
  source: { url: string; observed_at: string; brand?: string | null; rating?: number | null; review_count?: number | null } | null;
  is_demo_data: boolean;
};

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

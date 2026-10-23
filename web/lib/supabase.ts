import { createClient } from "@supabase/supabase-js";

// Browser-only client with the publishable key. All user data goes through the FastAPI service.
export const supabase = createClient(
  process.env.NEXT_PUBLIC_SUPABASE_URL ?? "http://localhost:54321",
  process.env.NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY ?? "missing-key",
);

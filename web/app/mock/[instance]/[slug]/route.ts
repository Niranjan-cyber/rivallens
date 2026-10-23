import { mockSites, renderMockHtml } from "@/lib/mock-sites";

// S-19: a fictional competitor's pricing page. A route handler, not a page: the collector gets plain,
// deterministic HTML (no RSC payload or streaming), and every request reads the current Demo Lab state.
async function mockVersion(instance: string, slug: string): Promise<string[] | null> {
  const q = `instance_key=eq.${encodeURIComponent(instance)}&slug=eq.${encodeURIComponent(slug)}&select=version`;
  const res = await fetch(`${process.env.NEXT_PUBLIC_SUPABASE_URL}/rest/v1/mock_pages_public?${q}`, {
    headers: { apikey: process.env.NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY ?? "" },
    cache: "no-store",
  });
  if (!res.ok) return null;
  const rows: { version: string[] }[] = await res.json();
  return rows[0]?.version ?? null;
}

export async function GET(_: Request, ctx: RouteContext<"/mock/[instance]/[slug]">) {
  const { instance, slug } = await ctx.params;
  const site = mockSites[slug];
  const version = site && (await mockVersion(instance, slug));
  if (!site || !version) return new Response("Unknown demo page.", { status: 404, headers: { "Cache-Control": "no-store" } });
  return new Response(renderMockHtml(site, version), { headers: { "Content-Type": "text/html; charset=utf-8", "Cache-Control": "no-store" } });
}

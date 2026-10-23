import type { MetadataRoute } from "next";

// The collector honours robots.txt, so the mock competitor pages must stay allowed (specs §1 C-02).
export default function robots(): MetadataRoute.Robots {
  return { rules: { userAgent: "*", allow: ["/", "/mock/"], disallow: ["/app/"] } };
}

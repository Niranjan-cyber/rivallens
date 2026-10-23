import type { Metadata } from "next";
import { Sofia_Sans } from "next/font/google";
import "./globals.css";

const sofia = Sofia_Sans({ variable: "--font-sofia", subsets: ["latin"] });

export const metadata: Metadata = {
  title: "RivalLens",
  description:
    "Watches competitors' public pricing and feature pages in the Indian market, ignores redesign noise, and keeps a dated receipt for every real change.",
};

export default function RootLayout({ children }: LayoutProps<"/">) {
  return (
    <html lang="en" className={`${sofia.variable} h-full antialiased`}>
      <body className="min-h-full flex flex-col font-sans">{children}</body>
    </html>
  );
}

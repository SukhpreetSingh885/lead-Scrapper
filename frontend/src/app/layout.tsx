import "./globals.css";
import React from "react";
import type { Metadata, Viewport } from "next";
import { Providers } from "./providers";

export const metadata: Metadata = {
  title: "India Leads Platform | B2B Lead Generation & Enrichment",
  description: "India-only B2B Business Lead Generation & Data Enrichment SaaS Platform",
};

export const viewport: Viewport = {
  width: "device-width",
  initialScale: 1,
  maximumScale: 5,
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="h-full">
      <body className="antialiased min-h-screen bg-slate-50 font-sans overflow-x-hidden w-full max-w-full">
        <Providers>{children}</Providers>
      </body>
    </html>
  );
}

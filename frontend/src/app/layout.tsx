import "./globals.css";
import React from "react";
import type { Metadata } from "next";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { Providers } from "./providers";

export const metadata: Metadata = {
  title: "India Leads Platform | B2B Lead Generation & Enrichment",
  description: "India-only B2B Business Lead Generation & Data Enrichment SaaS Platform",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className="antialiased min-h-screen bg-slate-50 font-sans">
        <Providers>{children}</Providers>
      </body>
    </html>
  );
}


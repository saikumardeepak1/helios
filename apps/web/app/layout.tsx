import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Helios",
  description: "AI Agent Observability Platform",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className="min-h-screen bg-white text-slate-900 antialiased">
        {children}
      </body>
    </html>
  );
}

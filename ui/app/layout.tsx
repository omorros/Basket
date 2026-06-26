import "./globals.css";
import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Basket — Reformulation Sentinel",
  description: "Catch a botched product reformulation while the complaints are still fresh.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className="font-sans">{children}</body>
    </html>
  );
}

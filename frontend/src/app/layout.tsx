import type { Metadata } from "next";
import "./globals.css";
import { Header } from "@/components/common/Header";

export const metadata: Metadata = {
  title: "JATAYUV-AI | Aerial Intelligence & 3D Photogrammetry Platform",
  description:
    "Autonomous aerial intelligence platform for drone imagery ingestion, monocular depth estimation, semantic segmentation, building damage assessment, and 3D photogrammetry.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="dark">
      <body className="min-h-screen bg-background text-foreground antialiased flex flex-col">
        <Header />
        <main className="flex-1 flex flex-col">{children}</main>
      </body>
    </html>
  );
}


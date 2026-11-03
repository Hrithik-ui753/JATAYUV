"use client";

import React, { useState } from "react";
import dynamic from "next/dynamic";
import { LandingNav } from "@/components/landing/LandingNav";
import { CapabilitiesSection } from "@/components/landing/CapabilitiesSection";
import { WorkflowSection } from "@/components/landing/WorkflowSection";
import { TechnologySection } from "@/components/landing/TechnologySection";
import { DocumentationSection } from "@/components/landing/DocumentationSection";
import { LandingFooter } from "@/components/landing/LandingFooter";
import { Activity, ShieldCheck, Compass, ArrowRight, Radio } from "lucide-react";

// Lazy-load expensive 3D Hero scene with SSR disabled
const CinematicDroneHero = dynamic(
  () =>
    import("@/components/landing/CinematicDroneHero").then(
      (mod) => mod.CinematicDroneHero
    ),
  {
    ssr: false,
    loading: () => (
      <div className="w-full h-[680px] lg:h-[780px] bg-forest-950 flex flex-col items-center justify-center gap-3 border-b border-emerald-500/20 font-mono text-xs text-emerald-400">
        <div className="relative flex h-5 w-5">
          <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75" />
          <span className="relative inline-flex rounded-full h-5 w-5 bg-emerald-500" />
        </div>
        <div className="tracking-widest uppercase">INITIALIZING WEBGL 3D EXPERIENCE // SHADERS LOADING</div>
      </div>
    ),
  }
);

export default function LandingPage() {
  const [docsModalOpen, setDocsModalOpen] = useState(false);

  return (
    <div className="min-h-screen bg-forest-950 text-foreground flex flex-col selection:bg-emerald-500 selection:text-black">
      {/* 1. Aerospace Navigation Bar */}
      <LandingNav onOpenDocs={() => {
        const el = document.getElementById("documentation");
        el?.scrollIntoView({ behavior: "smooth" });
      }} />

      {/* 2. Cinematic 3D Three.js Hero Scene */}
      <CinematicDroneHero />

      {/* Real-time Aerospace Mission Status Ticker */}
      <div className="w-full border-b border-emerald-500/20 bg-forest-900/60 py-2.5 px-4 font-mono text-[11px] overflow-hidden select-none">
        <div className="max-w-7xl mx-auto flex flex-wrap items-center justify-between gap-4">
          <div className="flex items-center gap-4 text-muted-foreground">
            <span className="flex items-center gap-1.5 text-emerald-300 font-semibold">
              <Radio className="w-3.5 h-3.5 text-emerald-400" /> TELEMETRY BROADCAST:
            </span>
            <span>UAV-INGRESS 124m AGL</span>
            <span>•</span>
            <span>RTK POSITIONING: 3D FIX ±1.2cm</span>
            <span>•</span>
            <span className="hidden sm:inline">LIDAR RATE: 300,000 PTS/SEC</span>
            <span>•</span>
            <span className="hidden md:inline">GSD: 1.8 CM/PIXEL</span>
          </div>

          <div className="flex items-center gap-3 text-emerald-400 font-semibold">
            <span className="hidden lg:inline text-muted-foreground">CELERY DISPATCH:</span>
            <span>4 WORKERS ACTIVE</span>
            <span>•</span>
            <span>GPU LATENCY 14ms</span>
          </div>
        </div>
      </div>

      {/* 3. Capability Sections (Depth, Segmentation, Damage, Change, 3D SfM) */}
      <CapabilitiesSection />

      {/* 4. Workflow Section (5-Stage Operational Pipeline) */}
      <WorkflowSection />

      {/* 5. Technology Section (Depth Anything V2, SegFormer, xBD, Open3D, PyTorch, Celery) */}
      <TechnologySection />

      {/* 6. Documentation Section (Quickstart, REST Endpoints, System Architecture) */}
      <DocumentationSection />

      {/* 7. Comprehensive Aerospace Footer */}
      <LandingFooter />
    </div>
  );
}

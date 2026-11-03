"use client";

import React from "react";
import Link from "next/link";
import { 
  Compass, 
  Activity, 
  ShieldCheck, 
  Layers, 
  Box, 
  Github, 
  FileText, 
  Terminal,
  ExternalLink
} from "lucide-react";

export function LandingFooter() {
  return (
    <footer className="bg-forest-950 border-t border-emerald-500/20 py-12 relative font-mono text-xs text-muted-foreground">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-8 pb-10 border-b border-emerald-500/15">
          {/* Col 1 & 2: Brand & Mission */}
          <div className="lg:col-span-2 space-y-4">
            <Link href="/" className="flex items-center gap-2.5 group">
              <div className="h-8 w-8 rounded bg-emerald-950 border border-emerald-500/40 flex items-center justify-center text-emerald-400">
                <Compass className="h-4 w-4" />
              </div>
              <div className="flex flex-col">
                <span className="text-base font-black tracking-wider text-white">
                  JATAYUV<span className="text-emerald-400">AI</span>
                </span>
                <span className="text-[9px] uppercase tracking-widest text-muted-foreground">
                  AERIAL INTELLIGENCE PLATFORM
                </span>
              </div>
            </Link>

            <p className="text-xs text-gray-400 leading-relaxed max-w-sm">
              Autonomous aerial intelligence platform for drone imagery ingestion, monocular depth estimation, 8-class land cover segmentation, humanitarian building damage assessment, and 3D photogrammetry.
            </p>

            <div className="flex items-center gap-3 pt-1">
              <div className="flex items-center gap-1.5 px-2.5 py-1 rounded bg-forest-900 border border-emerald-500/20 text-[11px] text-emerald-300">
                <span className="relative flex h-2 w-2">
                  <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75" />
                  <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500" />
                </span>
                <span>SYSTEM ENGINE: OPERATIONAL</span>
              </div>
            </div>
          </div>

          {/* Col 3: Core AI Capabilities */}
          <div className="space-y-3">
            <div className="text-xs font-bold text-white uppercase tracking-wider">
              AI Capabilities
            </div>
            <ul className="space-y-2 text-xs">
              <li>
                <a href="#depth" className="hover:text-emerald-300 transition-colors">
                  Monocular Depth (Depth Anything)
                </a>
              </li>
              <li>
                <a href="#segmentation" className="hover:text-emerald-300 transition-colors">
                  8-Class Land Cover (SegFormer)
                </a>
              </li>
              <li>
                <a href="#damage" className="hover:text-emerald-300 transition-colors">
                  xBD Building Damage Triage
                </a>
              </li>
              <li>
                <a href="#change" className="hover:text-emerald-300 transition-colors">
                  Bi-Temporal Change Differencing
                </a>
              </li>
              <li>
                <a href="#reconstruction" className="hover:text-emerald-300 transition-colors">
                  Dense 3D Photogrammetry (SfM)
                </a>
              </li>
            </ul>
          </div>

          {/* Col 4: Platform Navigation */}
          <div className="space-y-3">
            <div className="text-xs font-bold text-white uppercase tracking-wider">
              Platform
            </div>
            <ul className="space-y-2 text-xs">
              <li>
                <Link href="/dashboard" className="hover:text-emerald-300 transition-colors">
                  Mission Control Dashboard
                </Link>
              </li>
              <li>
                <Link href="/projects" className="hover:text-emerald-300 transition-colors">
                  Survey Project Manager
                </Link>
              </li>
              <li>
                <Link href="/login" className="hover:text-emerald-300 transition-colors">
                  Lead Analyst Sign In
                </Link>
              </li>
              <li>
                <a href="#workflow" className="hover:text-emerald-300 transition-colors">
                  5-Stage Workflow Pipeline
                </a>
              </li>
              <li>
                <a href="#technology" className="hover:text-emerald-300 transition-colors">
                  Technology Frameworks
                </a>
              </li>
            </ul>
          </div>

          {/* Col 5: Documentation & Repo */}
          <div className="space-y-3">
            <div className="text-xs font-bold text-white uppercase tracking-wider">
              Documentation
            </div>
            <ul className="space-y-2 text-xs">
              <li>
                <a href="#documentation" className="hover:text-emerald-300 transition-colors">
                  REST API v1 Specification
                </a>
              </li>
              <li>
                <a href="#documentation" className="hover:text-emerald-300 transition-colors">
                  System Architecture Blueprint
                </a>
              </li>
              <li>
                <a href="#documentation" className="hover:text-emerald-300 transition-colors">
                  Analyst Seed Credentials
                </a>
              </li>
              <li>
                <span className="text-gray-400">
                  WGS84 &amp; UTM Coordinates
                </span>
              </li>
              <li>
                <span className="text-gray-400">
                  FEMA xBD Disaster Benchmark
                </span>
              </li>
            </ul>
          </div>
        </div>

        {/* Bottom Credits & Legal Notice */}
        <div className="pt-8 flex flex-col sm:flex-row items-center justify-between gap-4 text-[11px] text-muted-foreground">
          <div className="flex items-center gap-2">
            <span>© 2026 JATAYUV-AI Core Team. All rights reserved.</span>
            <span>•</span>
            <span className="text-emerald-400 font-semibold">MODULE 02: CINEMATIC 3D EXPERIENCE</span>
          </div>

          <div className="flex items-center gap-4">
            <span className="text-gray-400">PyTorch 2.15</span>
            <span>•</span>
            <span className="text-gray-400">FastAPI 0.115</span>
            <span>•</span>
            <span className="text-gray-400">Three.js 0.165</span>
            <span>•</span>
            <span className="text-gray-400">Next.js 14.2</span>
          </div>
        </div>
      </div>
    </footer>
  );
}


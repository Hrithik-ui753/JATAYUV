"use client";

import React, { useState } from "react";
import Link from "next/link";
import { 
  Compass, 
  Menu, 
  X, 
  Layers, 
  ShieldAlert, 
  Box, 
  Activity, 
  ArrowRight,
  Cpu,
  FileCode,
  ExternalLink,
  ChevronDown
} from "lucide-react";
import { Button } from "@/components/ui/Button";

interface LandingNavProps {
  onOpenDocs?: () => void;
}

export function LandingNav({ onOpenDocs }: LandingNavProps) {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [solutionsOpen, setSolutionsOpen] = useState(false);

  const solutions = [
    { title: "Disaster & Emergency Response", desc: "xBD 4-tier rapid damage evaluation for FEMA and civil protection.", href: "#damage" },
    { title: "Metropolitan Land-Use (LULC)", desc: "8-class automatic urban zoning and structural boundary mapping.", href: "#segmentation" },
    { title: "Topographic & Slope Stability", desc: "Zero-shot monocular depth and high-altitude relief mesh generation.", href: "#depth" },
    { title: "Infrastructure & Border Survey", desc: "Bi-temporal change detection and high-density 3D photogrammetry.", href: "#reconstruction" },
  ];

  return (
    <nav className="sticky top-0 z-50 w-full border-b border-emerald-500/20 bg-forest-950/90 backdrop-blur-md">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
        {/* Brand Logo & Military Callout */}
        <div className="flex items-center gap-8">
          <Link href="/" className="flex items-center gap-2.5 group">
            <div className="h-9 w-9 rounded bg-emerald-950 border border-emerald-500/40 flex items-center justify-center text-emerald-400 group-hover:bg-emerald-900/60 group-hover:border-emerald-400 transition-all shadow-md shadow-emerald-950/50">
              <Compass className="h-5 w-5" />
            </div>
            <div className="flex flex-col">
              <div className="flex items-center gap-1.5">
                <span className="text-base font-black tracking-wider text-white">
                  JATAYUV
                </span>
                <span className="text-[10px] font-mono px-1 py-0.2 rounded bg-emerald-500/15 text-emerald-400 border border-emerald-500/30">
                  AI-GEOINT
                </span>
              </div>
              <span className="text-[9px] font-mono text-muted-foreground uppercase tracking-widest">
                AEROSPACE INTELLIGENCE
              </span>
            </div>
          </Link>

          {/* Desktop Nav Links */}
          <div className="hidden md:flex items-center gap-1 text-xs font-mono">
            <a
              href="#capabilities"
              className="px-3 py-2 rounded text-muted-foreground hover:text-white hover:bg-forest-800/50 transition-colors"
            >
              CAPABILITIES
            </a>

            <a
              href="#workflow"
              className="px-3 py-2 rounded text-muted-foreground hover:text-white hover:bg-forest-800/50 transition-colors"
            >
              WORKFLOW
            </a>

            <a
              href="#technology"
              className="px-3 py-2 rounded text-muted-foreground hover:text-white hover:bg-forest-800/50 transition-colors"
            >
              TECHNOLOGY
            </a>

            {onOpenDocs ? (
              <button
                onClick={onOpenDocs}
                className="px-3 py-2 rounded text-muted-foreground hover:text-white hover:bg-forest-800/50 transition-colors flex items-center gap-1"
              >
                <FileCode className="w-3.5 h-3.5 text-emerald-400" /> DOCS
              </button>
            ) : (
              <a
                href="#documentation"
                className="px-3 py-2 rounded text-muted-foreground hover:text-white hover:bg-forest-800/50 transition-colors flex items-center gap-1"
              >
                <FileCode className="w-3.5 h-3.5 text-emerald-400" /> DOCS
              </a>
            )}
          </div>
        </div>

        {/* Right CTA Actions */}
        <div className="hidden sm:flex items-center gap-3">
          <Link href="/login">
            <Button variant="outline" size="sm">
              Sign In
            </Button>
          </Link>

          <Link href="/dashboard">
            <Button variant="primary" size="sm">
              Launch Dashboard <ArrowRight className="w-3.5 h-3.5 ml-1" />
            </Button>
          </Link>
        </div>

        {/* Mobile Hamburger Button */}
        <button
          onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
          className="lg:hidden p-2 rounded text-muted-foreground hover:text-white hover:bg-forest-800"
          aria-label="Toggle navigation menu"
        >
          {mobileMenuOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
        </button>
      </div>

      {/* Mobile Drawer */}
      {mobileMenuOpen && (
        <div className="lg:hidden px-4 pt-2 pb-6 space-y-3 bg-forest-950 border-b border-emerald-500/20 font-mono text-sm">
          <a
            href="#capabilities"
            onClick={() => setMobileMenuOpen(false)}
            className="block px-3 py-2 rounded hover:bg-forest-800 text-muted-foreground hover:text-white"
          >
            Capabilities
          </a>
          <a
            href="#workflow"
            onClick={() => setMobileMenuOpen(false)}
            className="block px-3 py-2 rounded hover:bg-forest-800 text-muted-foreground hover:text-white"
          >
            Workflow Pipeline
          </a>
          <a
            href="#technology"
            onClick={() => setMobileMenuOpen(false)}
            className="block px-3 py-2 rounded hover:bg-forest-800 text-muted-foreground hover:text-white"
          >
            Technologies
          </a>
          <a
            href="#documentation"
            onClick={() => setMobileMenuOpen(false)}
            className="block px-3 py-2 rounded hover:bg-forest-800 text-muted-foreground hover:text-white"
          >
            Documentation
          </a>

          <div className="pt-4 border-t border-emerald-500/20 flex flex-col gap-2">
            <Link href="/login" onClick={() => setMobileMenuOpen(false)}>
              <Button variant="outline" size="md" className="w-full justify-center">
                Sign In to Analyst Portal
              </Button>
            </Link>
            <Link href="/dashboard" onClick={() => setMobileMenuOpen(false)}>
              <Button variant="primary" size="md" className="w-full justify-center">
                Launch Mission Control
              </Button>
            </Link>
          </div>
        </div>
      )}
    </nav>
  );
}


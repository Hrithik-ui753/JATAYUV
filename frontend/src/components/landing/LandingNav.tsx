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
          <div className="hidden lg:flex items-center gap-1 text-xs font-mono">
            {/* Product capabilities link */}
            <a
              href="#capabilities"
              className="px-3 py-2 rounded text-muted-foreground hover:text-white hover:bg-forest-800/50 transition-colors"
            >
              CAPABILITIES
            </a>

            {/* Solutions Dropdown */}
            <div className="relative">
              <button
                onClick={() => setSolutionsOpen(!solutionsOpen)}
                onMouseEnter={() => setSolutionsOpen(true)}
                className="flex items-center gap-1 px-3 py-2 rounded text-muted-foreground hover:text-white hover:bg-forest-800/50 transition-colors"
              >
                SOLUTIONS <ChevronDown className="w-3 h-3 text-emerald-400" />
              </button>

              {solutionsOpen && (
                <div
                  onMouseLeave={() => setSolutionsOpen(false)}
                  className="absolute left-0 top-full mt-1 w-80 p-2 rounded-lg glass-panel border-emerald-500/30 shadow-2xl z-50 flex flex-col gap-1"
                >
                  {solutions.map((item) => (
                    <a
                      key={item.title}
                      href={item.href}
                      onClick={() => setSolutionsOpen(false)}
                      className="p-2.5 rounded hover:bg-forest-800/80 transition-colors text-left group"
                    >
                      <div className="text-xs font-medium text-white group-hover:text-emerald-300">
                        {item.title}
                      </div>
                      <div className="text-[11px] text-muted-foreground mt-0.5 leading-snug">
                        {item.desc}
                      </div>
                    </a>
                  ))}
                </div>
              )}
            </div>

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
          {/* Status Indicator */}
          <div className="hidden xl:flex items-center gap-2 px-2.5 py-1 rounded bg-forest-900 border border-emerald-500/20 font-mono text-[11px]">
            <span className="relative flex h-1.5 w-1.5">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75" />
              <span className="relative inline-flex rounded-full h-1.5 w-1.5 bg-emerald-500" />
            </span>
            <span className="text-muted-foreground">CLUSTER:</span>
            <span className="text-emerald-300 font-semibold">ONLINE (0.02s)</span>
          </div>

          <Link href="/login">
            <Button variant="outline" size="sm">
              Sign In
            </Button>
          </Link>

          <Link href="/dashboard">
            <Button variant="primary" size="sm">
              Launch Mission Control <ArrowRight className="w-3.5 h-3.5 ml-1" />
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


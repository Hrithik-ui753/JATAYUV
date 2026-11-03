"use client";

import React, { useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  Compass,
  Layers,
  ShieldAlert,
  Box,
  FolderKanban,
  Activity,
  User as UserIcon,
  Bell,
  ArrowLeft,
  Settings,
  Radio
} from "lucide-react";
import { cn } from "@/lib/utils";

export function Header() {
  const pathname = usePathname();
  const [activeJobsCount] = useState<number>(0);

  // Do not show the internal dashboard header on the landing page
  if (pathname === "/") {
    return null;
  }

  const navLinks = [
    { href: "/dashboard", label: "Dashboard", icon: Activity },
    { href: "/projects", label: "Projects", icon: FolderKanban },
  ];

  return (
    <header className="sticky top-0 z-50 w-full border-b border-emerald-500/20 bg-forest-950/90 backdrop-blur-md">
      <div className="flex h-14 items-center justify-between px-6">
        {/* Brand Logo & Name */}
        <div className="flex items-center gap-6">
          <Link href="/" className="flex items-center gap-2.5 group">
            <div className="flex h-8 w-8 items-center justify-center rounded bg-emerald-950 border border-emerald-500/40 text-emerald-400 group-hover:bg-emerald-900/60 transition-colors shadow-md shadow-emerald-950/50">
              <Compass className="h-4 w-4" />
            </div>
            <div className="flex flex-col">
              <span className="text-sm font-black tracking-wider text-white flex items-center gap-1.5">
                JATAYUV<span className="text-emerald-400 text-[10px] px-1 py-0.2 rounded bg-emerald-500/15 border border-emerald-500/30">AI</span>
              </span>
              <span className="text-[9px] text-muted-foreground uppercase tracking-widest font-mono">Mission Control</span>
            </div>
          </Link>

          {/* Navigation Links */}
          <nav className="flex items-center gap-1 text-xs font-mono">
            {navLinks.map((link) => {
              const Icon = link.icon;
              const isActive = pathname === link.href || (link.href !== "/dashboard" && pathname.startsWith(link.href));
              return (
                <Link
                  key={link.href}
                  href={link.href}
                  className={cn(
                    "flex items-center gap-1.5 px-3 py-1.5 rounded transition-all",
                    isActive
                      ? "bg-forest-800 text-emerald-300 font-semibold border border-emerald-500/30"
                      : "text-muted-foreground hover:bg-forest-900 hover:text-white"
                  )}
                >
                  <Icon className="w-3.5 h-3.5" />
                  {link.label}
                </Link>
              );
            })}
          </nav>
        </div>

        {/* Right Action Icons & Profile */}
        <div className="flex items-center gap-3 font-mono text-xs">
          {/* Back to Cinematic Landing */}
          <Link
            href="/"
            className="hidden sm:flex items-center gap-1 px-2.5 py-1 rounded bg-forest-900/80 border border-emerald-500/20 text-muted-foreground hover:text-emerald-300 hover:border-emerald-500/40 transition-all text-[11px]"
          >
            <ArrowLeft className="w-3 h-3" />
            <span>Cinematic Hero</span>
          </Link>

          {/* Engine Status */}
          <div className="flex items-center gap-2 px-2.5 py-1 rounded border border-emerald-500/20 bg-forest-900/60 text-[11px]">
            <span className="relative flex h-2 w-2">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75" />
              <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500" />
            </span>
            <span className="text-muted-foreground">ENGINE:</span>
            <span className="text-emerald-300 font-semibold">ONLINE</span>
          </div>

          {/* User Account / Profile */}
          <Link
            href="/login"
            className="flex items-center gap-2 p-1 pr-3 rounded border border-emerald-500/20 hover:bg-forest-900 transition-colors"
          >
            <div className="w-6 h-6 rounded bg-emerald-500/20 text-emerald-300 flex items-center justify-center font-bold text-xs">
              <UserIcon className="w-3.5 h-3.5" />
            </div>
            <span className="text-[11px] font-medium text-white hidden md:inline">Lead Analyst</span>
          </Link>
        </div>
      </div>
    </header>
  );
}

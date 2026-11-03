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
} from "lucide-react";
import { cn } from "@/lib/utils";

export function Header() {
  const pathname = usePathname();
  const [activeJobsCount] = useState<number>(0);

  const navLinks = [
    { href: "/", label: "Dashboard", icon: Activity },
    { href: "/projects", label: "Projects", icon: FolderKanban },
    { href: "/damage", label: "Damage Assessment", icon: ShieldAlert },
    { href: "/reconstruction", label: "3D Photogrammetry", icon: Box },
  ];

  return (
    <header className="sticky top-0 z-50 w-full border-b border-border bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/80">
      <div className="flex h-16 items-center justify-between px-6">
        {/* Brand Logo & Name */}
        <div className="flex items-center gap-8">
          <Link href="/" className="flex items-center gap-2.5">
            <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-gradient-to-tr from-sky-600 to-primary text-white shadow-md shadow-primary/20">
              <Compass className="h-6 w-6" />
            </div>
            <div className="flex flex-col">
              <span className="text-base font-bold tracking-tight text-white flex items-center gap-1.5">
                JATAYUV<span className="text-primary text-xs px-1.5 py-0.2 rounded bg-primary/10 border border-primary/20">AI</span>
              </span>
              <span className="text-[10px] text-muted-foreground uppercase tracking-widest font-mono">Aerial Intelligence</span>
            </div>
          </Link>

          {/* Navigation Links */}
          <nav className="hidden md:flex items-center gap-1 text-sm font-medium">
            {navLinks.map((link) => {
              const Icon = link.icon;
              const isActive = pathname === link.href || (link.href !== "/" && pathname.startsWith(link.href));
              return (
                <Link
                  key={link.href}
                  href={link.href}
                  className={cn(
                    "flex items-center gap-2 px-3 py-2 rounded-lg transition-colors",
                    isActive
                      ? "bg-secondary text-primary font-semibold"
                      : "text-muted-foreground hover:bg-secondary/50 hover:text-white"
                  )}
                >
                  <Icon className="w-4 h-4" />
                  {link.label}
                </Link>
              );
            })}
          </nav>
        </div>

        {/* Right Action Icons & Profile */}
        <div className="flex items-center gap-3">
          {/* Active Processing Tasks Indicator */}
          <div className="flex items-center gap-2 px-3 py-1.5 rounded-full border border-border bg-secondary/40 text-xs">
            <span className="relative flex h-2 w-2">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
              <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500"></span>
            </span>
            <span className="text-muted-foreground">Engine: <span className="text-white font-medium">Ready</span></span>
          </div>

          {/* Notifications */}
          <button className="p-2 rounded-lg border border-border hover:bg-secondary text-muted-foreground hover:text-white transition-colors relative">
            <Bell className="w-4 h-4" />
            {activeJobsCount > 0 && (
              <span className="absolute top-1 right-1 w-2 h-2 rounded-full bg-primary" />
            )}
          </button>

          {/* User Account / Profile */}
          <Link
            href="/login"
            className="flex items-center gap-2 p-1.5 pr-3 rounded-lg border border-border hover:bg-secondary transition-colors"
          >
            <div className="w-7 h-7 rounded-md bg-primary/20 text-primary flex items-center justify-center font-bold text-xs">
              <UserIcon className="w-4 h-4" />
            </div>
            <span className="text-xs font-medium text-white hidden sm:inline">Lead Analyst</span>
          </Link>
        </div>
      </div>
    </header>
  );
}

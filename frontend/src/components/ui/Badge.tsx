import React from "react";
import { cn } from "@/lib/utils";

export interface BadgeProps extends React.HTMLAttributes<HTMLDivElement> {
  variant?: "default" | "secondary" | "success" | "warning" | "danger" | "outline" | "tactical" | "mint";
}

export function Badge({ className, variant = "default", ...props }: BadgeProps) {
  const variants = {
    default: "bg-emerald-500/10 text-emerald-400 border-emerald-500/25",
    secondary: "bg-forest-800 text-foreground border-emerald-500/15",
    success: "bg-emerald-500/15 text-emerald-300 border-emerald-500/30",
    warning: "bg-amber-500/15 text-amber-300 border-amber-500/30",
    danger: "bg-rose-500/15 text-rose-300 border-rose-500/30",
    outline: "text-foreground border-emerald-500/20 bg-transparent",
    tactical: "bg-forest-900/90 text-emerald-400 border-emerald-500/30 font-mono tracking-wider uppercase text-[10px]",
    mint: "bg-emerald-400/20 text-emerald-200 border-emerald-400/40 font-mono text-[11px]",
  };

  return (
    <div
      className={cn(
        "inline-flex items-center rounded-sm border px-2 py-0.5 text-xs font-medium transition-colors focus:outline-none select-none",
        variants[variant],
        className
      )}
      {...props}
    />
  );
}

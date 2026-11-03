import React from "react";
import { cn } from "@/lib/utils";

interface ProgressProps extends React.HTMLAttributes<HTMLDivElement> {
  value: number; // 0 to 100
  indicatorColor?: string;
}

export function Progress({ value, className, indicatorColor = "bg-primary", ...props }: ProgressProps) {
  const clamped = Math.min(100, Math.max(0, value));
  return (
    <div
      className={cn("relative h-2 w-full overflow-hidden rounded-full bg-secondary", className)}
      {...props}
    >
      <div
        className={cn("h-full w-full flex-1 transition-all duration-300 ease-in-out", indicatorColor)}
        style={{ transform: `translateX(-${100 - clamped}%)` }}
      />
    </div>
  );
}

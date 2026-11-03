"use client";

import React, { useState } from "react";
import { cn } from "@/lib/utils";
import { Eye, EyeOff, Layers } from "lucide-react";

interface ClassMeta {
  id: string;
  label: string;
  color: string;
  percentage: number;
}

interface SegmentationOverlayProps {
  originalImage: string;
  overlayImage: string;
  classes?: ClassMeta[];
  className?: string;
}

const DEFAULT_CLASSES: ClassMeta[] = [
  { id: "building", label: "Buildings & Roofs", color: "#8b5cf6", percentage: 28.4 },
  { id: "vegetation", label: "Canopy & Trees", color: "#10b981", percentage: 34.1 },
  { id: "road", label: "Roads & Asphalt", color: "#64748b", percentage: 16.5 },
  { id: "water", label: "Water Surfaces", color: "#3b82f6", percentage: 8.2 },
  { id: "soil", label: "Bare Ground", color: "#f59e0b", percentage: 9.8 },
  { id: "vehicle", label: "Vehicles / Assets", color: "#ef4444", percentage: 3.0 },
];

export function SegmentationOverlay({
  originalImage,
  overlayImage,
  classes = DEFAULT_CLASSES,
  className,
}: SegmentationOverlayProps) {
  const [opacity, setOpacity] = useState(60);
  const [showMask, setShowMask] = useState(true);
  const [activeClasses, setActiveClasses] = useState<Record<string, boolean>>(
    classes.reduce((acc, c) => ({ ...acc, [c.id]: true }), {})
  );

  const toggleClass = (id: string) => {
    setActiveClasses((prev) => ({ ...prev, [id]: !prev[id] }));
  };

  return (
    <div className={cn("flex flex-col gap-3 rounded-xl border border-border bg-card p-4", className)}>
      {/* Control bar */}
      <div className="flex flex-wrap items-center justify-between gap-3 border-b border-border pb-3">
        <div className="flex items-center gap-3">
          <button
            onClick={() => setShowMask(!showMask)}
            className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium rounded-lg border border-border bg-secondary hover:bg-secondary/80 text-white"
          >
            {showMask ? <Eye className="w-3.5 h-3.5 text-primary" /> : <EyeOff className="w-3.5 h-3.5 text-muted-foreground" />}
            {showMask ? "Mask Enabled" : "Mask Hidden"}
          </button>

          <div className="flex items-center gap-2 text-xs text-muted-foreground">
            <span>Opacity: {opacity}%</span>
            <input
              type="range"
              min="0"
              max="100"
              value={opacity}
              onChange={(e) => setOpacity(Number(e.target.value))}
              disabled={!showMask}
              className="w-24 accent-primary h-1.5 bg-secondary rounded-lg appearance-none cursor-pointer disabled:opacity-40"
            />
          </div>
        </div>
      </div>

      {/* Main Viewport */}
      <div className="relative aspect-[16/10] overflow-hidden rounded-lg border border-border bg-black">
        <img
          src={originalImage}
          alt="Aerial Source"
          className="absolute inset-0 w-full h-full object-cover"
        />

        {showMask && (
          <img
            src={overlayImage}
            alt="Semantic Segmentation Mask"
            className="absolute inset-0 w-full h-full object-cover mix-blend-screen transition-opacity"
            style={{ opacity: opacity / 100 }}
          />
        )}
      </div>

      {/* Class Chips & Coverage */}
      <div className="flex flex-col gap-2 pt-1">
        <div className="text-xs font-semibold text-muted-foreground uppercase tracking-wide">
          Semantic Classes & Land Cover
        </div>
        <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-6 gap-2">
          {classes.map((c) => {
            const isEnabled = activeClasses[c.id] ?? true;
            return (
              <button
                key={c.id}
                onClick={() => toggleClass(c.id)}
                className={cn(
                  "flex items-center gap-2 p-2 rounded-lg border text-left transition-all",
                  isEnabled
                    ? "border-border bg-secondary/50 text-white"
                    : "border-transparent bg-secondary/20 text-muted-foreground opacity-50"
                )}
              >
                <div
                  className="w-3 h-3 rounded-full flex-shrink-0"
                  style={{ backgroundColor: c.color }}
                />
                <div className="flex flex-col truncate">
                  <span className="text-xs font-medium truncate">{c.label}</span>
                  <span className="text-[10px] text-muted-foreground">{c.percentage.toFixed(1)}%</span>
                </div>
              </button>
            );
          })}
        </div>
      </div>
    </div>
  );
}

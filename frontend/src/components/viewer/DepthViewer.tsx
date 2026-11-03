"use client";

import React, { useState } from "react";
import { cn } from "@/lib/utils";
import { Layers } from "lucide-react";
import { Button } from "@/components/ui/Button";

interface DepthViewerProps {
  originalImage: string;
  depthMapUrl: string;
  minDepth?: number;
  maxDepth?: number;
  meanDepth?: number;
  className?: string;
}

export function DepthViewer({
  originalImage,
  depthMapUrl,
  minDepth = 2.4,
  maxDepth = 85.6,
  meanDepth = 34.2,
  className,
}: DepthViewerProps) {
  const [viewMode, setViewMode] = useState<"side-by-side" | "depth" | "blend">("blend");
  const [blendOpacity, setBlendOpacity] = useState(65);

  return (
    <div className={cn("flex flex-col gap-3 rounded-lg border border-emerald-500/25 bg-forest-900/60 p-4 font-mono text-xs", className)}>
      {/* Controls Bar */}
      <div className="flex flex-wrap items-center justify-between gap-3 border-b border-emerald-500/15 pb-3">
        <div className="flex items-center gap-2">
          <Button
            size="sm"
            variant={viewMode === "blend" ? "primary" : "outline"}
            onClick={() => setViewMode("blend")}
          >
            <Layers className="w-3.5 h-3.5 mr-1" /> Blend View
          </Button>
          <Button
            size="sm"
            variant={viewMode === "depth" ? "primary" : "outline"}
            onClick={() => setViewMode("depth")}
          >
            Depth Map
          </Button>
          <Button
            size="sm"
            variant={viewMode === "side-by-side" ? "primary" : "outline"}
            onClick={() => setViewMode("side-by-side")}
          >
            Side-by-Side
          </Button>
        </div>

        {viewMode === "blend" && (
          <div className="flex items-center gap-3 text-xs text-muted-foreground">
            <span>Blend Opacity: {blendOpacity}%</span>
            <input
              type="range"
              min="0"
              max="100"
              value={blendOpacity}
              onChange={(e) => setBlendOpacity(Number(e.target.value))}
              className="w-28 accent-emerald-500 h-1.5 bg-forest-950 rounded appearance-none cursor-pointer"
            />
          </div>
        )}
      </div>

      {/* Main Display Viewport */}
      {viewMode === "side-by-side" ? (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3 aspect-[16/9]">
          <div className="relative overflow-hidden rounded border border-emerald-500/20 bg-forest-950">
            <img src={originalImage} alt="Original Aerial RGB" className="w-full h-full object-cover" />
            <span className="absolute bottom-2 left-2 px-2 py-0.5 text-[11px] bg-forest-950/80 rounded text-white border border-white/10">
              Original Nadir RGB
            </span>
          </div>
          <div className="relative overflow-hidden rounded border border-emerald-500/20 bg-forest-950">
            <img src={depthMapUrl} alt="Estimated Depth Map" className="w-full h-full object-cover" />
            <span className="absolute bottom-2 left-2 px-2 py-0.5 text-[11px] bg-forest-950/80 rounded text-emerald-300 border border-emerald-500/30">
              Monocular Depth (Depth Anything V2)
            </span>
          </div>
        </div>
      ) : (
        <div className="relative aspect-[16/10] overflow-hidden rounded border border-emerald-500/20 bg-forest-950">
          {/* Base RGB Image */}
          <img
            src={originalImage}
            alt="Aerial Base"
            className="absolute inset-0 w-full h-full object-cover"
          />

          {/* Depth Map Overlay with Opacity */}
          <img
            src={depthMapUrl}
            alt="Depth Map Overlay"
            className="absolute inset-0 w-full h-full object-cover mix-blend-screen transition-opacity"
            style={{
              opacity: viewMode === "depth" ? 1.0 : blendOpacity / 100,
            }}
          />

          {/* Colormap Elevation Legend */}
          <div className="absolute bottom-3 right-3 flex flex-col gap-1 p-2 bg-forest-950/90 backdrop-blur rounded border border-emerald-500/30 text-[11px] text-white">
            <div className="text-[10px] uppercase font-bold text-muted-foreground">Relative Elevation Profile</div>
            <div className="h-2.5 w-36 rounded bg-gradient-to-r from-blue-700 via-emerald-400 to-amber-300" />
            <div className="flex justify-between text-[9px] text-muted-foreground">
              <span>Low ({minDepth.toFixed(1)}m)</span>
              <span>High ({maxDepth.toFixed(1)}m)</span>
            </div>
          </div>
        </div>
      )}

      {/* Depth Statistics Bar */}
      <div className="grid grid-cols-3 gap-2 pt-1 text-center text-xs">
        <div className="p-2.5 rounded bg-forest-900 border border-emerald-500/20">
          <div className="text-muted-foreground text-[10px]">MIN ESTIMATED ELEVATION</div>
          <div className="text-sm font-semibold text-emerald-400 mt-0.5">{minDepth.toFixed(2)} m</div>
        </div>
        <div className="p-2.5 rounded bg-forest-900 border border-emerald-500/20">
          <div className="text-muted-foreground text-[10px]">MEAN GROUND ELEVATION</div>
          <div className="text-sm font-semibold text-white mt-0.5">{meanDepth.toFixed(2)} m</div>
        </div>
        <div className="p-2.5 rounded bg-forest-900 border border-emerald-500/20">
          <div className="text-muted-foreground text-[10px]">MAX CREST ELEVATION</div>
          <div className="text-sm font-semibold text-sky-400 mt-0.5">{maxDepth.toFixed(2)} m</div>
        </div>
      </div>
    </div>
  );
}

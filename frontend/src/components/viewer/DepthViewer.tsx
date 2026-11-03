"use client";

import React, { useState, useRef, useEffect } from "react";
import { cn } from "@/lib/utils";
import { Layers, Maximize2, RotateCcw, Box } from "lucide-react";
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
  const [colormap, setColormap] = useState<"turbo" | "viridis" | "magma">("turbo");
  const canvasRef = useRef<HTMLCanvasElement>(null);

  return (
    <div className={cn("flex flex-col gap-3 rounded-xl border border-border bg-card p-4", className)}>
      {/* Controls Bar */}
      <div className="flex flex-wrap items-center justify-between gap-3 border-b border-border pb-3">
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
              className="w-28 accent-primary h-1.5 bg-secondary rounded-lg appearance-none cursor-pointer"
            />
          </div>
        )}
      </div>

      {/* Main Display Viewport */}
      {viewMode === "side-by-side" ? (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3 aspect-[16/9]">
          <div className="relative overflow-hidden rounded-lg border border-border bg-black">
            <img src={originalImage} alt="Original Aerial RGB" className="w-full h-full object-cover" />
            <span className="absolute bottom-2 left-2 px-2 py-0.5 text-xs bg-black/60 rounded text-white">
              Original RGB
            </span>
          </div>
          <div className="relative overflow-hidden rounded-lg border border-border bg-black">
            <img src={depthMapUrl} alt="Estimated Depth Map" className="w-full h-full object-cover" />
            <span className="absolute bottom-2 left-2 px-2 py-0.5 text-xs bg-black/60 rounded text-white">
              Monocular Depth (Depth Anything V2)
            </span>
          </div>
        </div>
      ) : (
        <div className="relative aspect-[16/10] overflow-hidden rounded-lg border border-border bg-black">
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
          <div className="absolute bottom-3 right-3 flex flex-col gap-1 p-2 bg-black/80 backdrop-blur rounded-lg border border-white/10 text-xs text-white">
            <div className="text-[10px] uppercase font-semibold text-muted-foreground">Relative Depth / Elevation</div>
            <div className="h-3 w-36 rounded bg-gradient-to-r from-blue-700 via-emerald-400 to-amber-300" />
            <div className="flex justify-between text-[10px] text-muted-foreground">
              <span>Far / Low ({minDepth.toFixed(1)}m)</span>
              <span>Near / High ({maxDepth.toFixed(1)}m)</span>
            </div>
          </div>
        </div>
      )}

      {/* Depth Statistics Bar */}
      <div className="grid grid-cols-3 gap-2 pt-2 text-center text-xs">
        <div className="p-2 rounded bg-secondary/40 border border-border">
          <div className="text-muted-foreground">Min Estimated Depth</div>
          <div className="text-sm font-semibold text-white mt-0.5">{minDepth.toFixed(2)} m</div>
        </div>
        <div className="p-2 rounded bg-secondary/40 border border-border">
          <div className="text-muted-foreground">Mean Estimated Depth</div>
          <div className="text-sm font-semibold text-primary mt-0.5">{meanDepth.toFixed(2)} m</div>
        </div>
        <div className="p-2 rounded bg-secondary/40 border border-border">
          <div className="text-muted-foreground">Max Estimated Depth</div>
          <div className="text-sm font-semibold text-white mt-0.5">{maxDepth.toFixed(2)} m</div>
        </div>
      </div>
    </div>
  );
}

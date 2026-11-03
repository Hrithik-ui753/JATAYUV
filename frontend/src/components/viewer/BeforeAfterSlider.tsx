"use client";

import React, { useState, useRef, useCallback } from "react";
import { cn } from "@/lib/utils";
import { MoveHorizontal } from "lucide-react";

interface BeforeAfterSliderProps {
  beforeImage: string;
  afterImage: string;
  beforeLabel?: string;
  afterLabel?: string;
  className?: string;
}

export function BeforeAfterSlider({
  beforeImage,
  afterImage,
  beforeLabel = "Before (Pre-Event)",
  afterLabel = "After (Post-Event)",
  className,
}: BeforeAfterSliderProps) {
  const [sliderPosition, setSliderPosition] = useState(50);
  const [isDragging, setIsDragging] = useState(false);
  const containerRef = useRef<HTMLDivElement>(null);

  const handleMove = useCallback((clientX: number) => {
    if (!containerRef.current) return;
    const rect = containerRef.current.getBoundingClientRect();
    const x = clientX - rect.left;
    const position = Math.max(0, Math.min(100, (x / rect.width) * 100));
    setSliderPosition(position);
  }, []);

  const handleTouchMove = (e: React.TouchEvent) => {
    if (!isDragging) return;
    handleMove(e.touches[0].clientX);
  };

  const handleMouseMove = (e: React.MouseEvent) => {
    if (!isDragging) return;
    handleMove(e.clientX);
  };

  return (
    <div
      ref={containerRef}
      className={cn(
        "relative w-full aspect-[16/10] overflow-hidden rounded-lg border border-emerald-500/30 select-none cursor-ew-resize bg-forest-950",
        className
      )}
      onMouseDown={() => setIsDragging(true)}
      onMouseUp={() => setIsDragging(false)}
      onMouseLeave={() => setIsDragging(false)}
      onMouseMove={handleMouseMove}
      onTouchStart={() => setIsDragging(true)}
      onTouchEnd={() => setIsDragging(false)}
      onTouchMove={handleTouchMove}
    >
      {/* After Image (Full width background) */}
      <img
        src={afterImage}
        alt={afterLabel}
        className="absolute inset-0 w-full h-full object-cover pointer-events-none"
      />
      <span className="absolute top-3 right-3 px-2.5 py-1 text-xs font-mono font-semibold rounded bg-forest-950/80 backdrop-blur text-emerald-300 border border-emerald-500/30 z-10">
        {afterLabel}
      </span>

      {/* Before Image (Clipped overlay) */}
      <div
        className="absolute inset-0 overflow-hidden"
        style={{ width: `${sliderPosition}%` }}
      >
        <img
          src={beforeImage}
          alt={beforeLabel}
          className="absolute inset-0 w-full h-full object-cover pointer-events-none"
          style={{ width: containerRef.current?.clientWidth || "100%", maxWidth: "none" }}
        />
        <span className="absolute top-3 left-3 px-2.5 py-1 text-xs font-mono font-semibold rounded bg-forest-950/80 backdrop-blur text-gray-200 border border-white/20 z-10">
          {beforeLabel}
        </span>
      </div>

      {/* Slider Divider Line */}
      <div
        className="absolute top-0 bottom-0 w-0.5 bg-emerald-400 shadow-[0_0_12px_rgba(0,245,160,0.8)] z-20"
        style={{ left: `${sliderPosition}%` }}
      >
        <div className="absolute top-1/2 -translate-y-1/2 -translate-x-1/2 w-8 h-8 rounded-full bg-forest-900 border-2 border-emerald-400 flex items-center justify-center text-emerald-300 shadow-lg shadow-black">
          <MoveHorizontal className="w-4 h-4" />
        </div>
      </div>
    </div>
  );
}

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
        "relative w-full aspect-[16/10] overflow-hidden rounded-xl border border-border select-none cursor-ew-resize bg-secondary/50",
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
      <span className="absolute top-3 right-3 px-2.5 py-1 text-xs font-semibold rounded bg-black/70 backdrop-blur text-white border border-white/10 z-10">
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
        <span className="absolute top-3 left-3 px-2.5 py-1 text-xs font-semibold rounded bg-black/70 backdrop-blur text-white border border-white/10 z-10">
          {beforeLabel}
        </span>
      </div>

      {/* Slider Divider Line */}
      <div
        className="absolute top-0 bottom-0 w-0.5 bg-white shadow-[0_0_10px_rgba(0,0,0,0.5)] z-20"
        style={{ left: `${sliderPosition}%` }}
      >
        <div className="absolute top-1/2 -translate-y-1/2 -translate-x-1/2 w-8 h-8 rounded-full bg-primary border-2 border-white flex items-center justify-center text-white shadow-lg">
          <MoveHorizontal className="w-4 h-4" />
        </div>
      </div>
    </div>
  );
}

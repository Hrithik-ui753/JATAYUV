"use client";

import React from "react";
import { cn, getDamageColor } from "@/lib/utils";
import { AlertTriangle, Building, CheckCircle2, FileDown, ShieldAlert } from "lucide-react";
import { Button } from "@/components/ui/Button";
import { DamageLevel } from "@/types";

interface DamageStatsCardProps {
  totalBuildings: number;
  counts: Record<DamageLevel, number>;
  damagePercentage: number;
  severityIndex: number; // 0 to 1
  onDownloadReport?: () => void;
  className?: string;
}

export function DamageStatsCard({
  totalBuildings,
  counts,
  damagePercentage,
  severityIndex,
  onDownloadReport,
  className,
}: DamageStatsCardProps) {
  const levels: { key: DamageLevel; label: string; count: number; color: string }[] = [
    { key: "no_damage", label: "No Damage", count: counts.no_damage || 0, color: "#22c55e" },
    { key: "minor_damage", label: "Minor Damage", count: counts.minor_damage || 0, color: "#eab308" },
    { key: "major_damage", label: "Major Damage", count: counts.major_damage || 0, color: "#f97316" },
    { key: "destroyed", label: "Destroyed", count: counts.destroyed || 0, color: "#ef4444" },
  ];

  return (
    <div className={cn("flex flex-col gap-4 rounded-xl border border-border bg-card p-5", className)}>
      <div className="flex items-center justify-between border-b border-border pb-3">
        <div className="flex items-center gap-2">
          <ShieldAlert className="w-5 h-5 text-rose-500" />
          <h4 className="font-semibold text-white">xBD Humanitarian Damage Assessment</h4>
        </div>
        {onDownloadReport && (
          <Button size="sm" variant="outline" onClick={onDownloadReport}>
            <FileDown className="w-4 h-4 mr-1.5" /> Export GeoJSON
          </Button>
        )}
      </div>

      {/* Top metrics summary */}
      <div className="grid grid-cols-3 gap-3">
        <div className="p-3 rounded-lg bg-secondary/40 border border-border">
          <div className="text-xs text-muted-foreground">Total Structures Detected</div>
          <div className="text-xl font-bold text-white mt-1 flex items-center gap-1.5">
            <Building className="w-4 h-4 text-muted-foreground" />
            {totalBuildings}
          </div>
        </div>

        <div className="p-3 rounded-lg bg-secondary/40 border border-border">
          <div className="text-xs text-muted-foreground">Affected Structures</div>
          <div className="text-xl font-bold text-rose-400 mt-1">
            {damagePercentage.toFixed(1)}%
          </div>
        </div>

        <div className="p-3 rounded-lg bg-secondary/40 border border-border">
          <div className="text-xs text-muted-foreground">Damage Severity Index</div>
          <div className="text-xl font-bold text-amber-400 mt-1">
            {(severityIndex * 10).toFixed(1)} / 10
          </div>
        </div>
      </div>

      {/* Segmented Distribution Bar */}
      <div className="flex flex-col gap-1.5">
        <div className="flex justify-between text-xs text-muted-foreground">
          <span>Damage Distribution</span>
          <span>{totalBuildings} structures</span>
        </div>
        <div className="h-3 w-full rounded-full overflow-hidden flex bg-secondary">
          {levels.map((lvl) => {
            const pct = totalBuildings > 0 ? (lvl.count / totalBuildings) * 100 : 0;
            if (pct <= 0) return null;
            return (
              <div
                key={lvl.key}
                style={{ width: `${pct}%`, backgroundColor: lvl.color }}
                title={`${lvl.label}: ${lvl.count} (${pct.toFixed(1)}%)`}
              />
            );
          })}
        </div>
      </div>

      {/* Level by level breakdown table */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 pt-1">
        {levels.map((lvl) => {
          const pct = totalBuildings > 0 ? ((lvl.count / totalBuildings) * 100).toFixed(1) : "0.0";
          return (
            <div
              key={lvl.key}
              className="flex flex-col p-2.5 rounded-lg border border-border bg-secondary/20"
            >
              <div className="flex items-center gap-2">
                <span className="w-2.5 h-2.5 rounded-full" style={{ backgroundColor: lvl.color }} />
                <span className="text-xs text-muted-foreground">{lvl.label}</span>
              </div>
              <div className="text-lg font-semibold text-white mt-1">{lvl.count}</div>
              <div className="text-[10px] text-muted-foreground">{pct}% of area</div>
            </div>
          );
        })}
      </div>
    </div>
  );
}

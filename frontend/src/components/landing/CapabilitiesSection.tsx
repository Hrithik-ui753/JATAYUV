"use client";

import React, { useState } from "react";
import Link from "next/link";
import { 
  Compass, 
  Layers, 
  ShieldAlert, 
  Box, 
  Activity, 
  ArrowRight, 
  CheckCircle2, 
  Eye, 
  Download, 
  Maximize2,
  Sliders,
  Sparkles,
  GitCompare,
  TrendingDown,
  Info
} from "lucide-react";
import { Button } from "@/components/ui/Button";
import { Badge } from "@/components/ui/Badge";
import { BeforeAfterSlider } from "@/components/viewer/BeforeAfterSlider";
import { DepthViewer } from "@/components/viewer/DepthViewer";
<<<<<<< HEAD
import { PointCloudViewer } from "@/components/viewer/PointCloudViewer";
=======
>>>>>>> 0400f2f (p5-udpated)

export function CapabilitiesSection() {
  const [activeCapability, setActiveCapability] = useState<"depth" | "segmentation" | "damage" | "change" | "3d">("damage");
  const [activeClasses, setActiveClasses] = useState<string[]>([
    "Buildings", "Vegetation", "Water", "Roads", "Bare Soil"
  ]);

  const classes = [
    { name: "Buildings", color: "#8b5cf6", pct: 34.2 },
    { name: "Vegetation", color: "#10b981", pct: 28.5 },
    { name: "Water", color: "#3b82f6", pct: 14.1 },
    { name: "Roads", color: "#64748b", pct: 12.8 },
    { name: "Bare Soil", color: "#d97706", pct: 6.4 },
    { name: "Vehicles", color: "#ef4444", pct: 4.0 },
  ];

  const toggleClass = (name: string) => {
    if (activeClasses.includes(name)) {
      if (activeClasses.length > 1) {
        setActiveClasses(activeClasses.filter((c) => c !== name));
      }
    } else {
      setActiveClasses([...activeClasses, name]);
    }
  };

  return (
    <section id="capabilities" className="py-20 bg-forest-950 border-b border-emerald-500/20 relative tech-grid">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Section Header */}
        <div className="flex flex-col items-center text-center max-w-3xl mx-auto mb-14">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded bg-emerald-500/10 border border-emerald-500/25 text-emerald-400 text-xs font-mono mb-3">
            <Sparkles className="w-3.5 h-3.5" />
            <span>AI VISION CORE CAPABILITIES</span>
          </div>

          <h2 className="text-3xl sm:text-4xl font-extrabold text-white tracking-tight">
            Cinematic Aerial Intelligence Suite
          </h2>

          <p className="mt-3 text-sm sm:text-base text-muted-foreground leading-relaxed">
            Engineered for high-altitude UAVs and tactical reconnaissance. Five coordinated deep learning and photogrammetry models running on distributed GPU workers.
          </p>

          {/* Capability Selector Tabs */}
          <div className="mt-8 flex flex-wrap items-center justify-center gap-2 p-1.5 rounded-lg glass-panel border-emerald-500/20 font-mono text-xs">
            <button
              onClick={() => setActiveCapability("damage")}
              className={`px-3.5 py-2 rounded transition-all flex items-center gap-2 ${
                activeCapability === "damage"
                  ? "bg-emerald-600 text-white shadow-md font-semibold"
                  : "text-muted-foreground hover:text-white hover:bg-forest-800"
              }`}
            >
              <ShieldAlert className="w-3.5 h-3.5 text-rose-400" />
              <span>Damage Assessment</span>
            </button>

            <button
              onClick={() => setActiveCapability("depth")}
              className={`px-3.5 py-2 rounded transition-all flex items-center gap-2 ${
                activeCapability === "depth"
                  ? "bg-emerald-600 text-white shadow-md font-semibold"
                  : "text-muted-foreground hover:text-white hover:bg-forest-800"
              }`}
            >
              <Activity className="w-3.5 h-3.5 text-sky-400" />
              <span>Monocular Depth</span>
            </button>

            <button
              onClick={() => setActiveCapability("segmentation")}
              className={`px-3.5 py-2 rounded transition-all flex items-center gap-2 ${
                activeCapability === "segmentation"
                  ? "bg-emerald-600 text-white shadow-md font-semibold"
                  : "text-muted-foreground hover:text-white hover:bg-forest-800"
              }`}
            >
              <Layers className="w-3.5 h-3.5 text-emerald-400" />
              <span>Semantic Segmentation</span>
            </button>

            <button
              onClick={() => setActiveCapability("change")}
              className={`px-3.5 py-2 rounded transition-all flex items-center gap-2 ${
                activeCapability === "change"
                  ? "bg-emerald-600 text-white shadow-md font-semibold"
                  : "text-muted-foreground hover:text-white hover:bg-forest-800"
              }`}
            >
              <GitCompare className="w-3.5 h-3.5 text-amber-400" />
              <span>Change Detection</span>
            </button>

            <button
              onClick={() => setActiveCapability("3d")}
              className={`px-3.5 py-2 rounded transition-all flex items-center gap-2 ${
                activeCapability === "3d"
                  ? "bg-emerald-600 text-white shadow-md font-semibold"
                  : "text-muted-foreground hover:text-white hover:bg-forest-800"
              }`}
            >
              <Box className="w-3.5 h-3.5 text-cyan-400" />
              <span>3D Reconstruction</span>
            </button>
          </div>
        </div>

        {/* Dynamic Interactive Capability Canvas Container */}
        <div className="glass-panel p-6 sm:p-8 rounded-xl border border-emerald-500/25 relative">
          {/* Tactical Frame Markers */}
          <div className="hud-corner-tl" />
          <div className="hud-corner-tr" />
          <div className="hud-corner-bl" />
          <div className="hud-corner-br" />

          {/* 1. DAMAGE ASSESSMENT */}
          {activeCapability === "damage" && (
            <div id="damage" className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-center">
              <div className="lg:col-span-7 flex flex-col gap-4">
                <div className="flex items-center justify-between text-xs font-mono text-muted-foreground">
                  <span className="flex items-center gap-1.5 text-emerald-400 font-semibold">
                    <ShieldAlert className="w-4 h-4 text-rose-500" />
                    DISASTER SECTOR 4 — INTERACTIVE xBD SLIDER
                  </span>
                  <span>DRAG DIVIDER TO REVEAL DAMAGE</span>
                </div>

                <div className="rounded-lg overflow-hidden border border-emerald-500/30">
                  <BeforeAfterSlider
                    beforeImage="https://images.unsplash.com/photo-1508873696983-2df5293cb32f?auto=format&fit=crop&w=1200&q=80"
                    afterImage="https://images.unsplash.com/photo-1547683905-f686c993aae5?auto=format&fit=crop&w=1200&q=80"
                    beforeLabel="Pre-Event Baseline Nadir Survey"
                    afterLabel="Post-Event Survey // xBD Neural Triage"
                  />
                </div>

                <div className="flex items-center justify-between text-[11px] font-mono text-muted-foreground">
                  <span>SURVEY FLIGHT ALTITUDE: 118.8m AGL</span>
                  <span className="text-rose-400 font-semibold">79.03% STRUCTURAL COLLAPSE</span>
                </div>
              </div>

              <div className="lg:col-span-5 flex flex-col gap-5">
                <div>
                  <Badge variant="danger" className="mb-2 font-mono">
                    xBD Disaster Response Taxonomy
                  </Badge>
                  <h3 className="text-2xl font-bold text-white tracking-tight">
                    Objective 4-Tier Building Damage Assessment
                  </h3>
                  <p className="mt-2 text-xs text-muted-foreground leading-relaxed">
                    Evaluates multi-spectral optical pairs to localize rooftop structural collapse, debris plumes, and wall failures, scoring severity according to the international humanitarian xBD benchmark.
                  </p>
                </div>

                {/* 4-Tier Breakdown Cards */}
                <div className="grid grid-cols-2 gap-2.5 font-mono text-xs">
                  <div className="p-2.5 rounded bg-forest-900 border border-emerald-500/20">
                    <div className="text-[10px] text-muted-foreground">NO DAMAGE</div>
                    <div className="text-emerald-400 font-bold text-base mt-0.5">52 Buildings</div>
                    <div className="text-[10px] text-muted-foreground">Intact structures</div>
                  </div>

                  <div className="p-2.5 rounded bg-forest-900 border border-emerald-500/20">
                    <div className="text-[10px] text-muted-foreground">MINOR DAMAGE</div>
                    <div className="text-amber-300 font-bold text-base mt-0.5">64 Buildings</div>
                    <div className="text-[10px] text-muted-foreground">Partial roof loss</div>
                  </div>

                  <div className="p-2.5 rounded bg-forest-900 border border-emerald-500/20">
                    <div className="text-[10px] text-muted-foreground">MAJOR DAMAGE</div>
                    <div className="text-orange-400 font-bold text-base mt-0.5">86 Buildings</div>
                    <div className="text-[10px] text-muted-foreground">Compromised walls</div>
                  </div>

                  <div className="p-2.5 rounded bg-forest-900 border border-emerald-500/20">
                    <div className="text-[10px] text-muted-foreground">DESTROYED</div>
                    <div className="text-rose-400 font-bold text-base mt-0.5">46 Buildings</div>
                    <div className="text-[10px] text-muted-foreground">Total collapse</div>
                  </div>
                </div>

                <div className="p-3 rounded bg-forest-900/90 border border-emerald-500/20 font-mono text-xs space-y-1.5">
                  <div className="flex items-center justify-between">
                    <span className="text-muted-foreground">TOTAL EVALUATED:</span>
                    <span className="text-white font-semibold">248 Structures</span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-muted-foreground">COMPOSITE SEVERITY INDEX:</span>
                    <span className="text-rose-400 font-semibold">0.642 / 1.000 (CRITICAL)</span>
                  </div>
                </div>

                <div className="flex items-center gap-3 pt-2">
                  <Link href="/dashboard">
                    <Button variant="primary" size="sm">
                      Inspect Sector in Dashboard <ArrowRight className="w-3.5 h-3.5 ml-1" />
                    </Button>
                  </Link>
                  <a href="#workflow" className="text-xs font-mono text-emerald-400 hover:underline">
                    View Workflow →
                  </a>
                </div>
              </div>
            </div>
          )}

          {/* 2. MONOCULAR DEPTH ESTIMATION */}
          {activeCapability === "depth" && (
            <div id="depth" className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-center">
              <div className="lg:col-span-7 flex flex-col gap-4">
                <div className="flex items-center justify-between text-xs font-mono text-muted-foreground">
                  <span className="flex items-center gap-1.5 text-sky-400 font-semibold">
                    <Activity className="w-4 h-4 text-sky-400" />
                    DEPTH ANYTHING V2 — ZERO-SHOT INFERENCE
                  </span>
                  <span>HOVER TO INSPECT RELATIVE DEPTH PIXELS</span>
                </div>

                <DepthViewer
                  originalImage="https://images.unsplash.com/photo-1508873696983-2df5293cb32f?auto=format&fit=crop&w=1200&q=80"
                  depthMapUrl="https://images.unsplash.com/photo-1579546929518-9e396f3cc809?auto=format&fit=crop&w=1200&q=80"
                  relativeMin={0.02}
                  relativeMax={0.97}
                  relativeMean={0.41}
                  depthType="relative"
                  modelLabel="Depth Anything V2 Small"
                />
              </div>

              <div className="lg:col-span-5 flex flex-col gap-5">
                <div>
                  <Badge variant="tactical" className="mb-2">
                    Zero-Shot Relative-to-Metric Depth
                  </Badge>
                  <h3 className="text-2xl font-bold text-white tracking-tight">
                    Continuous 3D Surface Relief &amp; Elevation
                  </h3>
                  <p className="mt-2 text-xs text-muted-foreground leading-relaxed">
                    Recovers sub-meter relative depth gradients from single uncalibrated UAV frames. Eliminates dead-zones in water or dense canopy, exporting 3D OBJ relief meshes directly.
                  </p>
                </div>

                <div className="grid grid-cols-3 gap-2 font-mono text-xs">
                  <div className="p-2.5 rounded bg-forest-900 border border-emerald-500/20 text-center">
                    <div className="text-[10px] text-muted-foreground">MIN DEPTH</div>
                    <div className="text-emerald-400 font-bold text-sm mt-0.5">3.4 m</div>
                    <div className="text-[9px] text-muted-foreground">Proximal</div>
                  </div>
                  <div className="p-2.5 rounded bg-forest-900 border border-emerald-500/20 text-center">
                    <div className="text-[10px] text-muted-foreground">MEAN ELEVATION</div>
                    <div className="text-white font-bold text-sm mt-0.5">47.2 m</div>
                    <div className="text-[9px] text-muted-foreground">Ground Plane</div>
                  </div>
                  <div className="p-2.5 rounded bg-forest-900 border border-emerald-500/20 text-center">
                    <div className="text-[10px] text-muted-foreground">MAX DEPTH</div>
                    <div className="text-sky-400 font-bold text-sm mt-0.5">118.6 m</div>
                    <div className="text-[9px] text-muted-foreground">Distal Ridge</div>
                  </div>
                </div>

                <div className="space-y-2 text-xs font-mono">
                  <div className="flex items-center gap-2 text-muted-foreground">
                    <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
                    <span>Edge-preserving Sobel gradient boundary refinement</span>
                  </div>
                  <div className="flex items-center gap-2 text-muted-foreground">
                    <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
                    <span>Automated export to textured Wavefront OBJ meshes</span>
                  </div>
                  <div className="flex items-center gap-2 text-muted-foreground">
                    <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
                    <span>Real-time colormap toggle (Turbo, Viridis, Elevation)</span>
                  </div>
                </div>

                <div className="pt-2">
                  <Link href="/dashboard">
                    <Button variant="primary" size="sm">
                      Run Depth Model on Custom Image <ArrowRight className="w-3.5 h-3.5 ml-1" />
                    </Button>
                  </Link>
                </div>
              </div>
            </div>
          )}

          {/* 3. SEMANTIC SEGMENTATION */}
          {activeCapability === "segmentation" && (
            <div id="segmentation" className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-center">
              <div className="lg:col-span-7 flex flex-col gap-4">
                <div className="flex items-center justify-between text-xs font-mono text-muted-foreground">
                  <span className="flex items-center gap-1.5 text-emerald-400 font-semibold">
                    <Layers className="w-4 h-4 text-emerald-400" />
                    8-CLASS LULC LAND COVER SEGMENTATION
                  </span>
                  <span>CLICK CLASSES TO TOGGLE MASKS</span>
                </div>

                {/* Filter chips */}
                <div className="flex flex-wrap gap-2">
                  {classes.map((cls) => {
                    const active = activeClasses.includes(cls.name);
                    return (
                      <button
                        key={cls.name}
                        onClick={() => toggleClass(cls.name)}
                        className={`px-2.5 py-1 rounded text-xs font-mono border transition-all flex items-center gap-1.5 ${
                          active
                            ? "bg-forest-800 text-white border-emerald-500/50"
                            : "bg-forest-950/60 text-muted-foreground border-border opacity-50"
                        }`}
                      >
                        <span
                          className="w-2 h-2 rounded-full"
                          style={{ backgroundColor: cls.color }}
                        />
                        <span>{cls.name}</span>
                        <span className="text-[10px] text-muted-foreground">({cls.pct}%)</span>
                      </button>
                    );
                  })}
                </div>

                <div className="relative rounded-lg overflow-hidden border border-emerald-500/30 aspect-video">
                  <img
                    src="https://images.unsplash.com/photo-1508873696983-2df5293cb32f?auto=format&fit=crop&w=1200&q=80"
                    alt="Aerial Land-Cover"
                    className="w-full h-full object-cover"
                  />
                  {/* Subtle simulated segmented overlay */}
                  <div className="absolute inset-0 bg-gradient-to-tr from-emerald-900/40 via-purple-900/30 to-blue-900/30 mix-blend-overlay pointer-events-none" />
                  
                  <div className="absolute bottom-3 left-3 glass-panel px-3 py-1.5 rounded font-mono text-xs text-emerald-300 flex items-center gap-2">
                    <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
                    <span>6 Classes Active // mIoU: 88.4%</span>
                  </div>
                </div>
              </div>

              <div className="lg:col-span-5 flex flex-col gap-5">
                <div>
                  <Badge variant="mint" className="mb-2">
                    SegFormer-B4 Spatial Segmentation
                  </Badge>
                  <h3 className="text-2xl font-bold text-white tracking-tight">
                    Aerial Land-Use &amp; Land-Cover Classification
                  </h3>
                  <p className="mt-2 text-xs text-muted-foreground leading-relaxed">
                    Identifies built environments, road networks, vegetation canopy, and water boundaries from nadir and oblique captures with pixel-accurate polygon boundary extraction.
                  </p>
                </div>

                {/* Class Distribution Bars */}
                <div className="space-y-2.5 font-mono text-xs">
                  {classes.map((c) => (
                    <div key={c.name} className="space-y-1">
                      <div className="flex justify-between text-[11px]">
                        <span className="text-gray-300">{c.name}</span>
                        <span className="text-muted-foreground">{c.pct}%</span>
                      </div>
                      <div className="h-1.5 w-full bg-forest-900 rounded-full overflow-hidden">
                        <div
                          className="h-full rounded-full transition-all duration-500"
                          style={{
                            width: `${c.pct}%`,
                            backgroundColor: c.color,
                          }}
                        />
                      </div>
                    </div>
                  ))}
                </div>

                <div className="pt-2 flex items-center gap-3">
                  <Link href="/dashboard">
                    <Button variant="primary" size="sm">
                      Run Segmentation Engine <ArrowRight className="w-3.5 h-3.5 ml-1" />
                    </Button>
                  </Link>
                  <button
                    onClick={() => alert("GeoJSON building footprint polygons exported successfully.")}
                    className="text-xs font-mono text-emerald-400 hover:underline flex items-center gap-1"
                  >
                    <Download className="w-3.5 h-3.5" /> Export GeoJSON
                  </button>
                </div>
              </div>
            </div>
          )}

          {/* 4. CHANGE DETECTION */}
          {activeCapability === "change" && (
            <div id="change" className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-center">
              <div className="lg:col-span-7 flex flex-col gap-4">
                <div className="flex items-center justify-between text-xs font-mono text-muted-foreground">
                  <span className="flex items-center gap-1.5 text-amber-400 font-semibold">
                    <GitCompare className="w-4 h-4 text-amber-400" />
                    BI-TEMPORAL CHANGE DETECTION HEATMAP
                  </span>
                  <span>PRE-SURVEY VS POST-SURVEY DIFF</span>
                </div>

                <div className="rounded-lg overflow-hidden border border-emerald-500/30">
                  <BeforeAfterSlider
                    beforeImage="https://images.unsplash.com/photo-1508873696983-2df5293cb32f?auto=format&fit=crop&w=1200&q=80"
                    afterImage="https://images.unsplash.com/photo-1579546929518-9e396f3cc809?auto=format&fit=crop&w=1200&q=80"
                    beforeLabel="Flight T0: Baseline"
                    afterLabel="Flight T1: Difference Heatmap"
                  />
                </div>
              </div>

              <div className="lg:col-span-5 flex flex-col gap-5">
                <div>
                  <Badge variant="warning" className="mb-2">
                    Multi-Temporal Spatial Differencing
                  </Badge>
                  <h3 className="text-2xl font-bold text-white tracking-tight">
                    Dynamic Surface Evolution &amp; Shift Mapping
                  </h3>
                  <p className="mt-2 text-xs text-muted-foreground leading-relaxed">
                    Calculates pixel-level photometric and structural divergence between repeated flights. Highlights newly constructed assets, damaged infrastructure, or environmental shifts.
                  </p>
                </div>

                <div className="p-3.5 rounded bg-forest-900 border border-emerald-500/20 font-mono text-xs space-y-2">
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">CHANGED AREA (PCT):</span>
                    <span className="text-amber-400 font-bold">38.7%</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">CHANGED PIXELS:</span>
                    <span className="text-white font-semibold">320,480 px</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">SIGNIFICANCE SCORE:</span>
                    <span className="text-emerald-400 font-semibold">0.874 (HIGH CONFIDENCE)</span>
                  </div>
                </div>

                <div className="pt-2">
                  <Link href="/dashboard">
                    <Button variant="primary" size="sm">
                      Compare Image Pairs in Workspace <ArrowRight className="w-3.5 h-3.5 ml-1" />
                    </Button>
                  </Link>
                </div>
              </div>
            </div>
          )}

          {/* 5. 3D RECONSTRUCTION */}
          {activeCapability === "3d" && (
            <div id="reconstruction" className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-center">
              <div className="lg:col-span-7 flex flex-col gap-4">
                <div className="flex items-center justify-between text-xs font-mono text-muted-foreground">
                  <span className="flex items-center gap-1.5 text-cyan-400 font-semibold">
                    <Box className="w-4 h-4 text-cyan-400" />
                    3D DENSE POINT CLOUD RECONSTRUCTION
                  </span>
<<<<<<< HEAD
                  <span>124,800 POINTS RENDERED</span>
                </div>

                <div className="h-[380px] w-full rounded-lg overflow-hidden border border-emerald-500/30">
                  <PointCloudViewer numPoints={45000} />
=======
                  <span>ILLUSTRATIVE PREVIEW</span>
                </div>

                {/* Decorative graphic only. The production viewer renders verified PLY
                    artifacts and never substitutes procedural geometry. */}
                <div
                  aria-hidden="true"
                  className="relative h-[380px] w-full rounded-lg overflow-hidden border border-emerald-500/30 bg-forest-950"
                  style={{
                    backgroundImage:
                      "radial-gradient(circle at 30% 40%, rgba(16,185,129,0.35) 0, rgba(6,10,8,0) 45%), radial-gradient(circle at 70% 65%, rgba(56,189,248,0.28) 0, rgba(6,10,8,0) 40%)",
                  }}
                >
                  <div className="absolute inset-0 flex flex-col items-center justify-center gap-2 text-center font-mono text-[11px] text-muted-foreground">
                    <Box className="w-8 h-8 text-cyan-400/70" />
                    <span>Hover a mission&apos;s 3D tab to load its verified point cloud</span>
                  </div>
>>>>>>> 0400f2f (p5-udpated)
                </div>
              </div>

              <div className="lg:col-span-5 flex flex-col gap-5">
                <div>
                  <Badge variant="tactical" className="mb-2">
                    Structure from Motion &amp; Multi-View Stereo
                  </Badge>
                  <h3 className="text-2xl font-bold text-white tracking-tight">
                    Sub-Centimeter 3D Photogrammetry
                  </h3>
                  <p className="mt-2 text-xs text-muted-foreground leading-relaxed">
                    Combines overlapping UAV captures into photorealistic colored point clouds, Digital Surface Models (DSM), and triangulated OBJ meshes with camera pose trajectory playback.
                  </p>
                </div>

                <div className="grid grid-cols-3 gap-2 font-mono text-xs">
                  <div className="p-2.5 rounded bg-forest-900 border border-emerald-500/20 text-center">
                    <div className="text-[10px] text-muted-foreground">POINTS</div>
                    <div className="text-cyan-400 font-bold text-sm mt-0.5">124.8K</div>
                    <div className="text-[9px] text-muted-foreground">Dense Cloud</div>
                  </div>
                  <div className="p-2.5 rounded bg-forest-900 border border-emerald-500/20 text-center">
                    <div className="text-[10px] text-muted-foreground">CAMERA POSES</div>
                    <div className="text-white font-bold text-sm mt-0.5">42 Trajectories</div>
                    <div className="text-[9px] text-muted-foreground">100% Calibrated</div>
                  </div>
                  <div className="p-2.5 rounded bg-forest-900 border border-emerald-500/20 text-center">
                    <div className="text-[10px] text-muted-foreground">REPROJ ERROR</div>
                    <div className="text-emerald-400 font-bold text-sm mt-0.5">0.78 px</div>
                    <div className="text-[9px] text-muted-foreground">Sub-pixel</div>
                  </div>
                </div>

                <div className="pt-2 flex items-center gap-3">
                  <Link href="/dashboard">
                    <Button variant="primary" size="sm">
                      Open Full 3D Spatial Viewer <ArrowRight className="w-3.5 h-3.5 ml-1" />
                    </Button>
                  </Link>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </section>
  );
}


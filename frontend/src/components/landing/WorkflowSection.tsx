"use client";

import React, { useState } from "react";
import { 
  UploadCloud, 
  Cpu, 
  Sparkles, 
  Box, 
  Compass, 
  ArrowRight, 
  CheckCircle2, 
  Layers, 
  Activity, 
  ShieldCheck,
  FileCheck2
} from "lucide-react";
import { Badge } from "@/components/ui/Badge";

export function WorkflowSection() {
  const [activeStep, setActiveStep] = useState(0);

  const steps = [
    {
      num: "01",
      title: "Upload Aerial Imagery",
      subtitle: "Multi-Format UAV Ingestion",
      icon: UploadCloud,
      desc: "Ingest high-resolution aerial frames (TIFF, JPEG, PNG, DNG) from DJI, Wingtra, Skydio, or satellite sources. The pipeline immediately parses camera sensor geometry, focal length, GPS latitude/longitude, and barometric AGL altitude from EXIF headers.",
      details: [
        "EXIF & XMP metadata recovery",
        "Sensor pitch, roll & yaw extraction",
        "Automated high-fidelity thumbnail generation",
        "Geospatial bounding box computation"
      ],
      badge: "INGESTION PHASE"
    },
    {
      num: "02",
      title: "Process Imagery",
      subtitle: "Radiometric & Spatial Normalization",
      icon: Cpu,
      desc: "Performs radiometric calibration, lens distortion removal, atmospheric contrast balancing, and spatial alignment. Generates pyramid tiles and preprocessed tensors ready for zero-latency deep neural net inference.",
      details: [
        "Contrast Limited Adaptive Histogram Equalization",
        "Radial lens distortion rectification",
        "Multi-scale image pyramid synthesis",
        "Asynchronous disk caching"
      ],
      badge: "PRE-PROCESSING"
    },
    {
      num: "03",
      title: "Run AI Analysis",
      subtitle: "Parallel GPU Microservices",
      icon: Sparkles,
      desc: "Dispatches inference jobs to Celery workers executing Depth Anything V2 for dense elevation, SegFormer for 8-class land use segmentation, and xBD damage triage models across multi-temporal image pairs.",
      details: [
        "Zero-shot metric depth estimation",
        "8-class land-use / land-cover masks",
        "xBD 4-tier structural collapse scoring",
        "Bi-temporal photometric change differencing"
      ],
      badge: "AI INFERENCE"
    },
    {
      num: "04",
      title: "Reconstruct 3D Geometry",
      subtitle: "Dense SfM & Surface Meshing",
      icon: Box,
      desc: "Executes Structure from Motion (SfM) feature matching and multi-view bundle adjustment to triangulate sparse 3D tie points into dense colored point clouds (.ply) and continuous Digital Surface Models (DSM).",
      details: [
        "SIFT / ORB feature tracking & epipolar matching",
        "Camera pose & trajectory estimation",
        "Sub-pixel bundle adjustment (reprojection < 1px)",
        "Digital Surface Model (DSM) GeoTIFF generation"
      ],
      badge: "PHOTOGRAMMETRY"
    },
    {
      num: "05",
      title: "Explore Results",
      subtitle: "Cinematic 3D WebGL Inspection",
      icon: Compass,
      desc: "Interact with real-time 3D point clouds in the browser. Measure 3D distances in meters, toggle classification overlays, inspect damage severity heatmaps, and export GeoJSON polygons and PLY models.",
      details: [
        "Interactive 60fps orbit, pan, and zoom",
        "True color, elevation, & damage colormaps",
        "Euclidean point-to-point spatial measurement",
        "One-click GeoJSON, OBJ & PLY export"
      ],
      badge: "EXPLOITATION"
    },
  ];

  return (
    <section id="workflow" className="py-20 bg-forest-950/80 border-b border-emerald-500/20 relative">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Section Heading */}
        <div className="flex flex-col items-center text-center max-w-3xl mx-auto mb-16">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded bg-emerald-500/10 border border-emerald-500/25 text-emerald-400 text-xs font-mono mb-3">
            <Activity className="w-3.5 h-3.5" />
            <span>END-TO-END PIPELINE ARCHITECTURE</span>
          </div>

          <h2 className="text-3xl sm:text-4xl font-extrabold text-white tracking-tight">
            From Raw Drone Flights to Actionable 3D Spatial Intelligence
          </h2>

          <p className="mt-3 text-sm sm:text-base text-muted-foreground leading-relaxed">
            A military-grade geospatial workflow designed for rapid humanitarian disaster assessment, urban expansion planning, and tactical survey operations.
          </p>
        </div>

        {/* Step Progress Pipeline Indicator */}
        <div className="grid grid-cols-1 sm:grid-cols-5 gap-3 mb-10">
          {steps.map((s, idx) => {
            const Icon = s.icon;
            const isCurrent = activeStep === idx;
            return (
              <button
                key={s.num}
                onClick={() => setActiveStep(idx)}
                className={`p-4 rounded-lg text-left transition-all relative border ${
                  isCurrent
                    ? "bg-forest-900 border-emerald-500/60 shadow-lg shadow-emerald-950/80"
                    : "bg-forest-950/60 border-emerald-500/15 hover:border-emerald-500/35 hover:bg-forest-900/50"
                }`}
              >
                <div className="flex items-center justify-between font-mono text-xs mb-2">
                  <span className={isCurrent ? "text-emerald-400 font-bold" : "text-muted-foreground"}>
                    STEP {s.num}
                  </span>
                  <Icon className={`w-4 h-4 ${isCurrent ? "text-emerald-400" : "text-muted-foreground"}`} />
                </div>
                <div className={`text-xs font-semibold ${isCurrent ? "text-white" : "text-gray-300"}`}>
                  {s.title}
                </div>
                {isCurrent && (
                  <div className="absolute -bottom-1 left-4 right-4 h-0.5 bg-emerald-400 rounded-full" />
                )}
              </button>
            );
          })}
        </div>

        {/* Active Step Detailed Card */}
        <div className="glass-panel p-6 sm:p-10 rounded-xl border border-emerald-500/25 relative">
          <div className="hud-corner-tl" />
          <div className="hud-corner-tr" />
          <div className="hud-corner-bl" />
          <div className="hud-corner-br" />

          <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-center">
            <div className="lg:col-span-7 flex flex-col gap-4">
              <div className="flex items-center gap-3">
                <span className="font-mono text-2xl font-black text-emerald-400">
                  {steps[activeStep].num}
                </span>
                <div>
                  <Badge variant="tactical">
                    {steps[activeStep].badge}
                  </Badge>
                  <h3 className="text-2xl font-extrabold text-white mt-1">
                    {steps[activeStep].title}
                  </h3>
                </div>
              </div>

              <p className="text-sm text-gray-300 leading-relaxed">
                {steps[activeStep].desc}
              </p>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 pt-2 font-mono text-xs">
                {steps[activeStep].details.map((item) => (
                  <div key={item} className="flex items-center gap-2 text-muted-foreground">
                    <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400 shrink-0" />
                    <span>{item}</span>
                  </div>
                ))}
              </div>

              <div className="flex items-center gap-4 pt-4">
                <a
                  href="/dashboard"
                  className="inline-flex items-center justify-center h-9 px-4 text-xs font-semibold rounded bg-emerald-600 text-white hover:bg-emerald-500 transition-colors"
                >
                  Execute in Mission Control <ArrowRight className="w-3.5 h-3.5 ml-1.5" />
                </a>

                {activeStep < 4 ? (
                  <button
                    onClick={() => setActiveStep(activeStep + 1)}
                    className="text-xs font-mono text-emerald-400 hover:text-white transition-colors"
                  >
                    Next Stage: {steps[activeStep + 1].title} →
                  </button>
                ) : (
                  <button
                    onClick={() => setActiveStep(0)}
                    className="text-xs font-mono text-emerald-400 hover:text-white transition-colors"
                  >
                    ↺ Restart Pipeline Overview
                  </button>
                )}
              </div>
            </div>

            {/* Tactical Architecture Schematic Box */}
            <div className="lg:col-span-5 p-6 rounded-lg bg-forest-900 border border-emerald-500/20 font-mono text-xs space-y-3">
              <div className="flex items-center justify-between text-[11px] text-muted-foreground border-b border-emerald-500/20 pb-2">
                <span>STAGE LOGIC VERIFICATION</span>
                <span className="text-emerald-400">STATUS: READY</span>
              </div>

              <div className="p-3 rounded bg-forest-950 border border-emerald-500/10 space-y-1.5 text-[11px]">
                <div className="text-emerald-400 font-bold">
                  // FASTAPI + CELERY WORKER TASK
                </div>
                <div className="text-muted-foreground">
                  Task ID: <span className="text-white">celery-task-stage-{steps[activeStep].num}</span>
                </div>
                <div className="text-muted-foreground">
                  Concurrency: <span className="text-emerald-300">4 Workers (GPU Distributed)</span>
                </div>
                <div className="text-muted-foreground">
                  Execution Time: <span className="text-white">~1.4s per 4K Frame</span>
                </div>
              </div>

              <div className="flex items-center justify-between text-[11px] text-muted-foreground pt-1">
                <span>PRECISION / TOLERANCE</span>
                <span className="text-emerald-300 font-semibold">Sub-meter Metric Scaling</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}


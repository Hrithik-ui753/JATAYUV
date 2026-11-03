"use client";

import React from "react";
import { 
  Cpu, 
  Layers, 
  ShieldAlert, 
  Box, 
  Flame, 
  Server, 
  Zap, 
  Terminal,
  ExternalLink
} from "lucide-react";
import { Badge } from "@/components/ui/Badge";

export function TechnologySection() {
  const technologies = [
    {
      name: "Depth Anything V2",
      category: "Monocular Depth Model",
      icon: Cpu,
      desc: "Zero-shot relative-to-metric elevation recovery, generating continuous depth gradient fields and 3D relief OBJ meshes from standard RGB UAV frames.",
      specs: "ViT-Large backbone, 335M parameters, sub-meter accuracy",
      badge: "NEURAL ELEVATION"
    },
    {
      name: "Hugging Face SegFormer",
      category: "Land-Cover Segmentation",
      icon: Layers,
      desc: "Hierarchical Transformer architecture segmenting 8 aerial classes (Buildings, Roads, Vegetation, Water, Bare Soil, Vehicles, Pavement, Construction).",
      specs: "Mix Transformer (MiT-B4), 88.4% mIoU, polygon contour extraction",
      badge: "SEMANTIC VISION"
    },
    {
      name: "xBD Disaster Taxonomy",
      category: "Humanitarian Triage",
      icon: ShieldAlert,
      desc: "Standardized 4-tier building damage classification (None, Minor, Major, Destroyed) conforming to FEMA and international disaster evaluation guidelines.",
      specs: "Bi-temporal Siamese feature fusion, 0.642 severity index",
      badge: "EMERGENCY RESPONSE"
    },
    {
      name: "Open3D & SfM Photogrammetry",
      category: "Dense 3D Point Clouds",
      icon: Box,
      desc: "Bundle adjustment, sparse feature tracking, and multi-view stereo generating dense .PLY point clouds and Digital Surface Model (DSM) GeoTIFFs.",
      specs: "Reprojection error < 0.8px, 124K+ points/scene",
      badge: "SPATIAL GEOMETRY"
    },
    {
      name: "PyTorch 2.x & CUDA",
      category: "Tensor Acceleration",
      icon: Flame,
      desc: "Hardware-accelerated deep learning execution engine with automated mixed-precision (FP16/BF16) and optimized memory paging.",
      specs: "TorchScript & ONNX runtime fallback, CUDA 12.x",
      badge: "COMPUTE RUNTIME"
    },
    {
      name: "Celery & Redis Distributed Queue",
      category: "Task Orchestration",
      icon: Server,
      desc: "Asynchronous task broker managing long-running photogrammetry and multi-image inference jobs with real-time percentage progress reporting.",
      specs: "Concurrent worker pools, disk caching, task fault tolerance",
      badge: "DISTRIBUTED WORKERS"
    },
    {
      name: "FastAPI ASGI Engine",
      category: "High-Throughput REST API",
      icon: Zap,
      desc: "Modern asynchronous Python backend implementing Pydantic v2 schemas, JWT Bearer security, SQLite/PostgreSQL persistence, and static binary streaming.",
      specs: "Pydantic v2 strict typing, <12ms baseline latency",
      badge: "BACKEND CORE"
    },
    {
      name: "Three.js & WebGL 2.0",
      category: "In-Browser 3D Visualizer",
      icon: Terminal,
      desc: "Hardware-accelerated 3D scene rendering with OrbitControls, custom shader elevation colormaps, point-cloud LOD strategies, and measurement tools.",
      specs: "60 FPS rendering, PLY/OBJ loaders, zero memory leaks",
      badge: "CLIENT-SIDE 3D"
    },
  ];

  return (
    <section id="technology" className="py-20 bg-forest-950 border-b border-emerald-500/20 relative">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Section Heading */}
        <div className="flex flex-col items-center text-center max-w-3xl mx-auto mb-16">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded bg-emerald-500/10 border border-emerald-500/25 text-emerald-400 text-xs font-mono mb-3">
            <Cpu className="w-3.5 h-3.5" />
            <span>PRODUCTION TECHNOLOGY STACK</span>
          </div>

          <h2 className="text-3xl sm:text-4xl font-extrabold text-white tracking-tight">
            Engineered with Battle-Tested Geospatial &amp; AI Frameworks
          </h2>

          <p className="mt-3 text-sm sm:text-base text-muted-foreground leading-relaxed">
            Every component in JATAYUV-AI is selected for zero-compromise precision, high throughput, and strict reproducibility in defense, humanitarian, and civil domains.
          </p>
        </div>

        {/* 8 Tech Cards Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {technologies.map((tech) => {
            const Icon = tech.icon;
            return (
              <div
                key={tech.name}
                className="glass-panel p-5 rounded-lg border border-emerald-500/15 hover:border-emerald-500/35 transition-all flex flex-col justify-between group"
              >
                <div>
                  <div className="flex items-center justify-between mb-3">
                    <div className="h-9 w-9 rounded bg-forest-900 border border-emerald-500/30 flex items-center justify-center text-emerald-400 group-hover:bg-emerald-600/20 transition-colors">
                      <Icon className="w-4 h-4" />
                    </div>
                    <Badge variant="tactical">
                      {tech.badge}
                    </Badge>
                  </div>

                  <h3 className="text-base font-bold text-white group-hover:text-emerald-300 transition-colors">
                    {tech.name}
                  </h3>
                  <div className="text-[11px] font-mono text-muted-foreground mb-2">
                    {tech.category}
                  </div>

                  <p className="text-xs text-gray-300 leading-relaxed">
                    {tech.desc}
                  </p>
                </div>

                <div className="mt-4 pt-3 border-t border-emerald-500/15 font-mono text-[10px] text-emerald-400 flex items-center justify-between">
                  <span className="truncate">{tech.specs}</span>
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </section>
  );
}


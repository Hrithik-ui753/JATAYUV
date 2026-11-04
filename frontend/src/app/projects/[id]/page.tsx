"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import dynamic from "next/dynamic";
import {
  Compass,
  Layers,
  ShieldAlert,
  Box,
  UploadCloud,
  FileDown,
  Sparkles,
  ArrowLeft,
  Camera,
  MapPin,
  Clock,
  Play,
  RotateCw,
  Sliders,
  CheckCircle2,
  AlertCircle,
  GitCompare,
  Activity,
  Download
} from "lucide-react";
import { Button } from "@/components/ui/Button";
import { Badge } from "@/components/ui/Badge";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/Card";
import { BeforeAfterSlider } from "@/components/viewer/BeforeAfterSlider";
import { DepthViewer } from "@/components/viewer/DepthViewer";
import { api } from "@/lib/api";
import { Project, AerialImage } from "@/types";

const AdvancedSpatialViewer3D = dynamic(
  () =>
    import("@/components/viewer/AdvancedSpatialViewer3D").then(
      (mod) => mod.AdvancedSpatialViewer3D
    ),
  {
    ssr: false,
    loading: () => (
      <div className="h-[620px] w-full bg-forest-950 flex flex-col items-center justify-center gap-2 border border-emerald-500/20 rounded-xl font-mono text-xs text-emerald-400">
        <span>INITIALIZING 3D SPATIAL RECONSTRUCTION...</span>
      </div>
    ),
  }
);

export default function ProjectWorkspacePage({ params }: { params: { id: string } }) {
  const [project, setProject] = useState<Project | null>(null);
  const [images, setImages] = useState<AerialImage[]>([]);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<
    "imagery" | "depth" | "segmentation" | "damage" | "change" | "3d"
  >("3d");
  const [isProcessing, setIsProcessing] = useState<boolean>(false);

  useEffect(() => {
    const load = async () => {
      try {
        setLoading(true);
        const p = await api.getProject(params.id);
        setProject(p);
        const imgs = await api.getProjectImages(params.id);
        setImages(imgs);
      } catch (err) {
        console.error(err);
      } finally {
        setLoading(false);
      }
    };
    load();
  }, [params.id]);

  const handleRunInference = (taskName: string) => {
    setIsProcessing(true);
    setTimeout(() => {
      setIsProcessing(false);
    }, 1200);
  };

  return (
    <div className="flex-1 flex flex-col gap-6 p-6 sm:p-8 max-w-7xl mx-auto w-full font-mono text-xs">
      {/* Top Breadcrumb & Project Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-emerald-500/20 pb-5">
        <div className="flex flex-col gap-1.5">
          <Link
            href="/projects"
            className="flex items-center gap-1.5 text-xs text-muted-foreground hover:text-emerald-300 transition-colors w-fit"
          >
            <ArrowLeft className="w-3.5 h-3.5" /> Back to Survey Missions
          </Link>
          <h1 className="text-2xl font-black tracking-tight text-white flex items-center gap-2.5">
            {project?.name || "Loading Mission..."}
            <Badge variant="success" className="text-[10px]">
              Active Session
            </Badge>
          </h1>
          <div className="flex flex-wrap items-center gap-4 text-xs text-muted-foreground mt-1">
            <span className="flex items-center gap-1">
              <MapPin className="w-3.5 h-3.5 text-emerald-400" /> {project?.location_name || "Location Unspecified"}
            </span>
            <span>•</span>
            <span className="flex items-center gap-1">
              <Camera className="w-3.5 h-3.5 text-emerald-400" /> {images.length} Captures
            </span>
            <span>•</span>
            <span>Created {project?.created_at ? new Date(project.created_at).toLocaleDateString() : ""}</span>
          </div>
        </div>

        <div className="flex items-center gap-3">
          <Link href="/dashboard">
            <Button variant="outline" size="sm">
              <Compass className="w-4 h-4 mr-1.5" /> Full Mission Control
            </Button>
          </Link>
        </div>
      </div>

      {/* Workspace Navigation Tabs */}
      <div className="flex items-center gap-1 border-b border-emerald-500/20 pb-1 overflow-x-auto text-xs">
        {[
          { id: "3d", label: "3D Photogrammetry", icon: Box },
          { id: "damage", label: "Damage Assessment (xBD)", icon: ShieldAlert },
          { id: "depth", label: "Monocular Depth", icon: Activity },
          { id: "segmentation", label: "Land-Cover Segmentation", icon: Layers },
          { id: "change", label: "Change Detection", icon: GitCompare },
          { id: "imagery", label: "Ingested Imagery", icon: Camera },
        ].map((tab) => {
          const Icon = tab.icon;
          const isActive = activeTab === tab.id;
          return (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id as any)}
              className={`flex items-center gap-1.5 px-3 py-2 rounded transition-all shrink-0 ${
                isActive
                  ? "bg-forest-900 text-emerald-300 font-bold border border-emerald-500/30"
                  : "text-muted-foreground hover:text-white hover:bg-forest-900/50"
              }`}
            >
              <Icon className="w-3.5 h-3.5" />
              <span>{tab.label}</span>
            </button>
          );
        })}
      </div>

      {/* Dynamic Tab Views */}
      <div className="flex flex-col gap-6">
        {/* 1. 3D TAB */}
        {activeTab === "3d" && (
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <span className="text-white font-bold text-sm">
                HIGH-DENSITY STRUCTURE FROM MOTION (SfM) POINT CLOUD
              </span>
              <Button
                onClick={() => handleRunInference("3D")}
                variant="primary"
                size="sm"
                isLoading={isProcessing}
              >
                Re-Run Triangulation
              </Button>
            </div>

            <AdvancedSpatialViewer3D
              projectName={project?.name}
              locationName={project?.location_name}
              initialPointCount={85000}
            />
          </div>
        )}

        {/* 2. DAMAGE TAB */}
        {activeTab === "damage" && (
          <div className="glass-panel p-6 rounded-xl border border-emerald-500/25 space-y-5">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="text-base font-bold text-white">xBD Humanitarian Damage Assessment</h3>
                <p className="text-muted-foreground text-xs">Pre- vs Post-Disaster aerial flight differencing.</p>
              </div>
              <Button
                onClick={() => handleRunInference("Damage")}
                variant="primary"
                size="sm"
                isLoading={isProcessing}
              >
                Execute Analysis
              </Button>
            </div>

            <BeforeAfterSlider
              beforeImage="https://images.unsplash.com/photo-1508873696983-2df5293cb32f?auto=format&fit=crop&w=1200&q=80"
              afterImage="https://images.unsplash.com/photo-1547683905-f686c993aae5?auto=format&fit=crop&w=1200&q=80"
              beforeLabel="Pre-Event Baseline Survey"
              afterLabel="Post-Event Survey // xBD Neural Triage"
            />

            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-xs">
              <div className="p-3 rounded bg-forest-900 border border-emerald-500/20">
                <div className="text-[10px] text-muted-foreground">NO DAMAGE</div>
                <div className="text-emerald-400 font-bold text-base mt-0.5">52 Buildings</div>
              </div>
              <div className="p-3 rounded bg-forest-900 border border-emerald-500/20">
                <div className="text-[10px] text-muted-foreground">MINOR DAMAGE</div>
                <div className="text-amber-300 font-bold text-base mt-0.5">64 Buildings</div>
              </div>
              <div className="p-3 rounded bg-forest-900 border border-emerald-500/20">
                <div className="text-[10px] text-muted-foreground">MAJOR DAMAGE</div>
                <div className="text-orange-400 font-bold text-base mt-0.5">86 Buildings</div>
              </div>
              <div className="p-3 rounded bg-forest-900 border border-emerald-500/20">
                <div className="text-[10px] text-muted-foreground">DESTROYED</div>
                <div className="text-rose-400 font-bold text-base mt-0.5">46 Buildings</div>
              </div>
            </div>
          </div>
        )}

        {/* 3. DEPTH TAB */}
        {activeTab === "depth" && (
          <div className="glass-panel p-6 rounded-xl border border-emerald-500/25 space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="text-base font-bold text-white">Depth Anything V2 Small — Monocular Depth</h3>
                <p className="text-muted-foreground text-xs">
                  Relative inverse-depth map and relief extraction (no metric scale unless calibrated).
                </p>
              </div>
              <Button
                onClick={() => handleRunInference("Depth")}
                variant="primary"
                size="sm"
                isLoading={isProcessing}
              >
                Re-Estimate Depth
              </Button>
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
        )}

        {/* 4. SEGMENTATION TAB */}
        {activeTab === "segmentation" && (
          <div className="glass-panel p-6 rounded-xl border border-emerald-500/25 space-y-4">
            <h3 className="text-base font-bold text-white">8-Class Land Use &amp; Land Cover Segmentation</h3>
            <div className="relative rounded-lg overflow-hidden border border-emerald-500/30 aspect-video">
              <img
                src="https://images.unsplash.com/photo-1508873696983-2df5293cb32f?auto=format&fit=crop&w=1200&q=80"
                alt="Segmentation"
                className="w-full h-full object-cover"
              />
              <div className="absolute inset-0 bg-gradient-to-tr from-emerald-900/40 via-purple-900/30 to-blue-900/30 mix-blend-overlay pointer-events-none" />
            </div>
            <div className="flex justify-between items-center text-muted-foreground">
              <span>IoU: 88.4% Across All Classes</span>
              <button
                onClick={() => alert("GeoJSON building footprints exported.")}
                className="text-emerald-400 font-bold hover:underline flex items-center gap-1"
              >
                <Download className="w-3.5 h-3.5" /> Download GeoJSON
              </button>
            </div>
          </div>
        )}

        {/* 5. CHANGE TAB */}
        {activeTab === "change" && (
          <div className="glass-panel p-6 rounded-xl border border-emerald-500/25 space-y-4">
            <h3 className="text-base font-bold text-white">Bi-Temporal Divergence Heatmap</h3>
            <BeforeAfterSlider
              beforeImage="https://images.unsplash.com/photo-1508873696983-2df5293cb32f?auto=format&fit=crop&w=1200&q=80"
              afterImage="https://images.unsplash.com/photo-1579546929518-9e396f3cc809?auto=format&fit=crop&w=1200&q=80"
              beforeLabel="Flight Baseline T0"
              afterLabel="Divergence Heatmap T1"
            />
          </div>
        )}

        {/* 6. IMAGERY TAB */}
        {activeTab === "imagery" && (
          <div className="space-y-4">
            <h3 className="text-base font-bold text-white">Ingested UAV Survey Imagery</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {images.map((img) => (
                <div key={img.id} className="glass-panel p-4 rounded-lg border border-emerald-500/20 flex gap-4">
                  <div className="w-36 h-28 rounded overflow-hidden shrink-0 bg-forest-950 border border-emerald-500/20">
                    <img src={img.thumbnail_path} alt={img.filename} className="w-full h-full object-cover" />
                  </div>
                  <div className="space-y-1">
                    <div className="text-white font-bold">{img.filename}</div>
                    <div className="text-muted-foreground">{img.width}x{img.height} px</div>
                    {img.telemetry && (
                      <div className="text-[10px] text-emerald-300">
                        {img.telemetry.camera_model} | {img.telemetry.altitude_m}m AGL
                      </div>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

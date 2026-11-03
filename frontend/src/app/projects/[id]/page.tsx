"use client";

import React, { useState } from "react";
import Link from "next/link";
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
} from "lucide-react";
import { Button } from "@/components/ui/Button";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/Card";
import { PointCloudViewer } from "@/components/viewer/PointCloudViewer";
import { BeforeAfterSlider } from "@/components/viewer/BeforeAfterSlider";
import { DepthViewer } from "@/components/viewer/DepthViewer";
import { SegmentationOverlay } from "@/components/viewer/SegmentationOverlay";
import { DamageStatsCard } from "@/components/damage/DamageStatsCard";

export default function ProjectWorkspacePage({ params }: { params: { id: string } }) {
  const [activeTab, setActiveTab] = useState<
    "imagery" | "depth" | "segmentation" | "damage" | "change" | "3d" | "export"
  >("imagery");

  const [isProcessing, setIsProcessing] = useState<boolean>(false);

  // Sample project context
  const project = {
    id: params.id,
    name: "Coastal Sector 4 Post-Storm Survey",
    description: "Multi-temporal drone photogrammetry and damage assessment after Cyclone Hudhud landfall.",
    location: "Bhubaneswar Coastal Region (19.81° N, 85.83° E)",
    imageCount: 148,
    createdAt: "2026-11-02 18:30",
  };

  // Sample ingested aerial image
  const sampleImages = [
    {
      id: "img-001",
      filename: "DJI_0492_PreDisaster.JPG",
      width: 4000,
      height: 3000,
      altitude: 120.4,
      focalLength: "8.8mm (24mm eq.)",
      camera: "DJI FC330 (Mavic 3E)",
      preprocessed: true,
      url: "https://images.unsplash.com/photo-1508873696983-2df5293cb32f?auto=format&fit=crop&w=1200&q=80",
    },
    {
      id: "img-002",
      filename: "DJI_0548_PostDisaster.JPG",
      width: 4000,
      height: 3000,
      altitude: 120.1,
      focalLength: "8.8mm (24mm eq.)",
      camera: "DJI FC330 (Mavic 3E)",
      preprocessed: true,
      url: "https://images.unsplash.com/photo-1547683905-f686c993aae5?auto=format&fit=crop&w=1200&q=80",
    },
  ];

  const handleRunInference = (taskName: string) => {
    setIsProcessing(true);
    setTimeout(() => {
      setIsProcessing(false);
    }, 1500);
  };

  return (
    <div className="flex flex-col gap-6 p-6 max-w-7xl mx-auto w-full">
      {/* Top Breadcrumb & Project Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-border pb-5">
        <div className="flex flex-col gap-1.5">
          <Link
            href="/projects"
            className="flex items-center gap-1.5 text-xs text-muted-foreground hover:text-white transition-colors w-fit"
          >
            <ArrowLeft className="w-3.5 h-3.5" /> Back to Project Missions
          </Link>
          <h1 className="text-2xl font-extrabold tracking-tight text-white flex items-center gap-2.5">
            {project.name}
            <span className="text-xs font-semibold px-2 py-0.5 rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
              Active Session
            </span>
          </h1>
          <div className="flex flex-wrap items-center gap-4 text-xs text-muted-foreground mt-1">
            <span className="flex items-center gap-1">
              <MapPin className="w-3.5 h-3.5 text-primary" /> {project.location}
            </span>
            <span>•</span>
            <span className="flex items-center gap-1">
              <Camera className="w-3.5 h-3.5 text-primary" /> {project.imageCount} Geotagged Images
            </span>
            <span>•</span>
            <span className="flex items-center gap-1">
              <Clock className="w-3.5 h-3.5 text-primary" /> {project.createdAt}
            </span>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <Button variant="outline" size="sm" onClick={() => setActiveTab("export")}>
            <FileDown className="w-4 h-4 mr-1.5" /> Export Products
          </Button>
          <Button variant="primary" size="sm" onClick={() => setActiveTab("imagery")}>
            <UploadCloud className="w-4 h-4 mr-1.5" /> Ingest Imagery
          </Button>
        </div>
      </div>

      {/* Navigation Workflow Tabs */}
      <div className="flex items-center gap-1.5 overflow-x-auto border-b border-border pb-1">
        {[
          { id: "imagery", label: "Imagery & Ingestion", icon: Camera },
          { id: "depth", label: "Monocular Depth", icon: Layers },
          { id: "segmentation", label: "Semantic Segmentation", icon: Sliders },
          { id: "damage", label: "Damage Assessment (xBD)", icon: ShieldAlert },
          { id: "change", label: "Change Detection", icon: RotateCw },
          { id: "3d", label: "3D Photogrammetry", icon: Box },
          { id: "export", label: "Downloads & Reports", icon: FileDown },
        ].map((tab) => {
          const Icon = tab.icon;
          const isActive = activeTab === tab.id;
          return (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id as any)}
              className={`flex items-center gap-2 px-3.5 py-2 rounded-t-lg text-xs font-semibold whitespace-nowrap transition-colors border-b-2 ${
                isActive
                  ? "border-primary text-primary bg-secondary/30"
                  : "border-transparent text-muted-foreground hover:text-white hover:bg-secondary/20"
              }`}
            >
              <Icon className="w-4 h-4" />
              {tab.label}
            </button>
          );
        })}
      </div>

      {/* Tab 1: Imagery & Ingestion */}
      {activeTab === "imagery" && (
        <div className="flex flex-col gap-6">
          {/* Ingestion Dropzone */}
          <div className="border-2 border-dashed border-border hover:border-primary/50 transition-colors rounded-xl p-8 flex flex-col items-center justify-center gap-3 bg-card text-center cursor-pointer">
            <div className="w-12 h-12 rounded-full bg-primary/10 text-primary flex items-center justify-center">
              <UploadCloud className="w-6 h-6" />
            </div>
            <div>
              <p className="text-sm font-semibold text-white">Drag & drop aerial drone survey files here</p>
              <p className="text-xs text-muted-foreground mt-0.5">Supports RAW, JPG, TIFF, GeoTIFF with EXIF GPS telemetry</p>
            </div>
            <Button size="sm" variant="outline">Browse Local Files</Button>
          </div>

          {/* Ingested Images Gallery & Telemetry */}
          <div className="flex flex-col gap-3">
            <h3 className="text-sm font-bold text-white uppercase tracking-wider">Ingested Survey Captures ({sampleImages.length})</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {sampleImages.map((img) => (
                <Card key={img.id} className="overflow-hidden">
                  <div className="relative aspect-[16/9] bg-black">
                    <img src={img.url} alt={img.filename} className="w-full h-full object-cover" />
                    <span className="absolute top-2 right-2 px-2 py-0.5 rounded text-[11px] font-mono bg-black/80 text-white border border-white/10">
                      {img.width} x {img.height}
                    </span>
                  </div>
                  <CardContent className="p-4 flex flex-col gap-2">
                    <div className="flex items-center justify-between">
                      <span className="text-sm font-semibold text-white font-mono">{img.filename}</span>
                      <span className="inline-flex items-center gap-1 text-[11px] text-emerald-400 font-medium">
                        <CheckCircle2 className="w-3.5 h-3.5" /> Preprocessed
                      </span>
                    </div>
                    <div className="grid grid-cols-3 gap-2 text-[11px] text-muted-foreground bg-secondary/30 p-2.5 rounded-lg border border-border">
                      <div>
                        <span>Camera:</span>
                        <div className="font-medium text-white truncate">{img.camera}</div>
                      </div>
                      <div>
                        <span>Altitude (AGL):</span>
                        <div className="font-medium text-white">{img.altitude} m</div>
                      </div>
                      <div>
                        <span>Focal Length:</span>
                        <div className="font-medium text-white">{img.focalLength}</div>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* Tab 2: Monocular Depth */}
      {activeTab === "depth" && (
        <div className="flex flex-col gap-4">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-lg font-bold text-white flex items-center gap-2">
                <Layers className="w-5 h-5 text-primary" /> Monocular Depth Estimation
              </h2>
              <p className="text-xs text-muted-foreground">
                Inference powered by Depth Anything V2 with metric scaling and 3D terrain surface normals.
              </p>
            </div>
            <Button
              size="sm"
              variant="primary"
              isLoading={isProcessing}
              onClick={() => handleRunInference("depth")}
            >
              <Play className="w-4 h-4 mr-1.5" /> Re-estimate Depth
            </Button>
          </div>

          <DepthViewer
            originalImage={sampleImages[0].url}
            depthMapUrl="https://images.unsplash.com/photo-1579546929518-9e396f3cc809?auto=format&fit=crop&w=1200&q=80"
            minDepth={2.8}
            maxDepth={98.4}
            meanDepth={42.1}
          />
        </div>
      )}

      {/* Tab 3: Semantic Segmentation */}
      {activeTab === "segmentation" && (
        <div className="flex flex-col gap-4">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-lg font-bold text-white flex items-center gap-2">
                <Sliders className="w-5 h-5 text-primary" /> Aerial Semantic Segmentation
              </h2>
              <p className="text-xs text-muted-foreground">
                Fine-tuned SegFormer / Aerial Transformer parsing 8 land-use & land-cover classes.
              </p>
            </div>
            <Button
              size="sm"
              variant="primary"
              isLoading={isProcessing}
              onClick={() => handleRunInference("segmentation")}
            >
              <Play className="w-4 h-4 mr-1.5" /> Run Segmentation
            </Button>
          </div>

          <SegmentationOverlay
            originalImage={sampleImages[0].url}
            overlayImage="https://images.unsplash.com/photo-1547683905-f686c993aae5?auto=format&fit=crop&w=1200&q=80"
          />
        </div>
      )}

      {/* Tab 4: Damage Assessment */}
      {activeTab === "damage" && (
        <div className="flex flex-col gap-6">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-lg font-bold text-white flex items-center gap-2">
                <ShieldAlert className="w-5 h-5 text-rose-500" /> Building Damage Assessment (xBD)
              </h2>
              <p className="text-xs text-muted-foreground">
                Dual-stream multi-temporal transformer classifying structural collapse conforming to international relief standards.
              </p>
            </div>
            <Button
              size="sm"
              variant="primary"
              isLoading={isProcessing}
              onClick={() => handleRunInference("damage")}
            >
              <Play className="w-4 h-4 mr-1.5" /> Execute Assessment
            </Button>
          </div>

          <BeforeAfterSlider
            beforeImage={sampleImages[0].url}
            afterImage={sampleImages[1].url}
            beforeLabel="Pre-Cyclone Baseline (Oct 28)"
            afterLabel="Post-Cyclone Damage Pass (Nov 02)"
          />

          <DamageStatsCard
            totalBuildings={342}
            counts={{
              no_damage: 184,
              minor_damage: 76,
              major_damage: 54,
              destroyed: 28,
            }}
            damagePercentage={46.2}
            severityIndex={0.48}
            onDownloadReport={() => alert("Downloading GeoJSON vector damage polygon layer...")}
          />
        </div>
      )}

      {/* Tab 5: Change Detection */}
      {activeTab === "change" && (
        <div className="flex flex-col gap-4">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-lg font-bold text-white flex items-center gap-2">
                <RotateCw className="w-5 h-5 text-primary" /> Bi-Temporal Change Detection
              </h2>
              <p className="text-xs text-muted-foreground">
                Detects spatial, structural, and land cover deviations between survey flight passes.
              </p>
            </div>
            <Button
              size="sm"
              variant="primary"
              isLoading={isProcessing}
              onClick={() => handleRunInference("change")}
            >
              <Play className="w-4 h-4 mr-1.5" /> Compute Change Mask
            </Button>
          </div>

          <BeforeAfterSlider
            beforeImage={sampleImages[0].url}
            afterImage={sampleImages[1].url}
            beforeLabel="Survey Pass 1 (T0)"
            afterLabel="Survey Pass 2 (T1 - Diff Overlay)"
          />
        </div>
      )}

      {/* Tab 6: 3D Photogrammetry */}
      {activeTab === "3d" && (
        <div className="flex flex-col gap-4">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-lg font-bold text-white flex items-center gap-2">
                <Box className="w-5 h-5 text-primary" /> Multi-Image 3D Reconstruction
              </h2>
              <p className="text-xs text-muted-foreground">
                Structure from Motion (COLMAP / Open3D pipeline) generating dense point clouds, elevation meshes, and DSM.
              </p>
            </div>
            <Button
              size="sm"
              variant="primary"
              isLoading={isProcessing}
              onClick={() => handleRunInference("3d")}
            >
              <Play className="w-4 h-4 mr-1.5" /> Reconstruct Point Cloud
            </Button>
          </div>

          <PointCloudViewer numPoints={50000} />
        </div>
      )}

      {/* Tab 7: Downloads & Export */}
      {activeTab === "export" && (
        <div className="flex flex-col gap-4">
          <h2 className="text-lg font-bold text-white flex items-center gap-2">
            <FileDown className="w-5 h-5 text-primary" /> Download Analysis Products
          </h2>
          <p className="text-xs text-muted-foreground">
            Export standardized GIS, CAD, and 3D data formats for external decision-support systems.
          </p>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mt-2">
            <Card>
              <CardHeader>
                <CardTitle className="text-base flex items-center gap-2">
                  <ShieldAlert className="w-4 h-4 text-rose-500" /> Vector Damage Polygons (GeoJSON)
                </CardTitle>
                <CardDescription>
                  Building footprint polygons labeled with xBD damage severity and confidence scores.
                </CardDescription>
              </CardHeader>
              <CardContent>
                <Button size="sm" variant="outline" className="w-full">
                  <FileDown className="w-4 h-4 mr-1.5" /> Download GeoJSON (1.2 MB)
                </Button>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="text-base flex items-center gap-2">
                  <Box className="w-4 h-4 text-amber-400" /> 3D Dense Point Cloud (Stanford .PLY)
                </CardTitle>
                <CardDescription>
                  Full 3D coordinate point cloud with RGB vertex color and computed normal vectors.
                </CardDescription>
              </CardHeader>
              <CardContent>
                <Button size="sm" variant="outline" className="w-full">
                  <FileDown className="w-4 h-4 mr-1.5" /> Download PLY Point Cloud (48.6 MB)
                </Button>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="text-base flex items-center gap-2">
                  <Layers className="w-4 h-4 text-sky-400" /> Digital Surface Model (GeoTIFF)
                </CardTitle>
                <CardDescription>
                  32-bit float elevation raster with embedded geospatial projection coordinates.
                </CardDescription>
              </CardHeader>
              <CardContent>
                <Button size="sm" variant="outline" className="w-full">
                  <FileDown className="w-4 h-4 mr-1.5" /> Download GeoTIFF DSM (18.4 MB)
                </Button>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="text-base flex items-center gap-2">
                  <Sliders className="w-4 h-4 text-emerald-400" /> Executive Mission Summary (PDF)
                </CardTitle>
                <CardDescription>
                  Executive summary report containing damage analytics, class distributions, and aerial orthomosaic previews.
                </CardDescription>
              </CardHeader>
              <CardContent>
                <Button size="sm" variant="outline" className="w-full">
                  <FileDown className="w-4 h-4 mr-1.5" /> Download PDF Report (3.8 MB)
                </Button>
              </CardContent>
            </Card>
          </div>
        </div>
      )}
    </div>
  );
}

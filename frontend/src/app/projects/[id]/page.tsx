"use client";

<<<<<<< HEAD
import React, { useCallback, useEffect, useMemo, useState } from "react";
=======
<<<<<<< HEAD
import React, { useState, useEffect } from "react";
=======
import React, { useCallback, useEffect, useMemo, useState } from "react";
>>>>>>> 0400f2f (p5-udpated)
>>>>>>> origin/main
import Link from "next/link";
import dynamic from "next/dynamic";
import {
  Compass,
  Layers,
  ShieldAlert,
  Box,
<<<<<<< HEAD
=======
<<<<<<< HEAD
  UploadCloud,
  FileDown,
=======
>>>>>>> 0400f2f (p5-udpated)
>>>>>>> origin/main
  Sparkles,
  ArrowLeft,
  Camera,
  MapPin,
<<<<<<< HEAD
=======
<<<<<<< HEAD
  Clock,
  Play,
  RotateCw,
  Sliders,
  CheckCircle2,
  AlertCircle,
  GitCompare,
>>>>>>> origin/main
  Activity,
  AlertTriangle,
  GitCompare,
  Download,
  RefreshCw,
} from "lucide-react";
import { Button } from "@/components/ui/Button";
import { Badge } from "@/components/ui/Badge";
<<<<<<< HEAD
=======
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/Card";
=======
  Activity,
  AlertTriangle,
  GitCompare,
  Download,
  RefreshCw,
} from "lucide-react";
import { Button } from "@/components/ui/Button";
import { Badge } from "@/components/ui/Badge";
>>>>>>> 0400f2f (p5-udpated)
>>>>>>> origin/main
import { BeforeAfterSlider } from "@/components/viewer/BeforeAfterSlider";
import { DepthViewer } from "@/components/viewer/DepthViewer";
import { api } from "@/lib/api";
import { Project, AerialImage } from "@/types";
<<<<<<< HEAD
=======
<<<<<<< HEAD
=======
>>>>>>> origin/main
import type {
  ChangeDetectionResult,
  DamageAssessmentResult,
  DepthResult,
  Reconstruction3DResult,
  SegmentationResult,
} from "@/types";
<<<<<<< HEAD
=======
>>>>>>> 0400f2f (p5-udpated)
>>>>>>> origin/main

const AdvancedSpatialViewer3D = dynamic(
  () =>
    import("@/components/viewer/AdvancedSpatialViewer3D").then(
      (mod) => mod.AdvancedSpatialViewer3D
    ),
  {
    ssr: false,
    loading: () => (
      <div className="h-[620px] w-full bg-forest-950 flex flex-col items-center justify-center gap-2 border border-emerald-500/20 rounded-xl font-mono text-xs text-emerald-400">
<<<<<<< HEAD
        <span>INITIALIZING 3D VIEWER…</span>
=======
<<<<<<< HEAD
        <span>INITIALIZING 3D SPATIAL RECONSTRUCTION...</span>
=======
        <span>INITIALIZING 3D VIEWER…</span>
>>>>>>> 0400f2f (p5-udpated)
>>>>>>> origin/main
      </div>
    ),
  }
);

<<<<<<< HEAD
=======
<<<<<<< HEAD
=======
>>>>>>> origin/main
/** Empty state used wherever no verified result exists yet. */
function NoVerifiedResult({ label }: { label: string }) {
  return (
    <div className="flex flex-col items-center justify-center gap-2 p-8 rounded-lg border border-dashed border-emerald-500/25 bg-forest-950/60 text-center">
      <AlertTriangle className="w-6 h-6 text-amber-400" />
      <p className="text-muted-foreground text-xs max-w-md">
        No verified {label} result available for this mission yet. Run the analysis on an
        uploaded frame to generate one.
      </p>
    </div>
  );
}

<<<<<<< HEAD
=======
>>>>>>> 0400f2f (p5-udpated)
>>>>>>> origin/main
export default function ProjectWorkspacePage({ params }: { params: { id: string } }) {
  const [project, setProject] = useState<Project | null>(null);
  const [images, setImages] = useState<AerialImage[]>([]);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<
    "imagery" | "depth" | "segmentation" | "damage" | "change" | "3d"
  >("3d");
  const [isProcessing, setIsProcessing] = useState<boolean>(false);
<<<<<<< HEAD
=======
<<<<<<< HEAD
=======
>>>>>>> origin/main
  const [pageError, setPageError] = useState<string | null>(null);

  const [reconResult, setReconResult] = useState<Reconstruction3DResult | null>(null);
  const [depthResult, setDepthResult] = useState<DepthResult | null>(null);
  const [segmentationResult, setSegmentationResult] = useState<SegmentationResult | null>(null);
  const [damageResult, setDamageResult] = useState<DamageAssessmentResult | null>(null);
  const [changeResult, setChangeResult] = useState<ChangeDetectionResult | null>(null);

  const loadResults = useCallback(async () => {
    try {
      const recon = await api.get3DReconstructionResult(params.id);
      setReconResult(recon);
    } catch {
      // 404 simply means nothing has been reconstructed for this mission yet.
      setReconResult(null);
    }
  }, [params.id]);
<<<<<<< HEAD
=======
>>>>>>> 0400f2f (p5-udpated)
>>>>>>> origin/main

  useEffect(() => {
    const load = async () => {
      try {
        setLoading(true);
        const p = await api.getProject(params.id);
        setProject(p);
        const imgs = await api.getProjectImages(params.id);
        setImages(imgs);
<<<<<<< HEAD
        await loadResults();
      } catch (err: any) {
        setPageError(err?.message ?? "Failed to load mission data");
=======
<<<<<<< HEAD
      } catch (err) {
        console.error(err);
=======
        await loadResults();
      } catch (err: any) {
        setPageError(err?.message ?? "Failed to load mission data");
>>>>>>> 0400f2f (p5-udpated)
>>>>>>> origin/main
      } finally {
        setLoading(false);
      }
    };
    load();
<<<<<<< HEAD
  }, [params.id, loadResults]);
=======
<<<<<<< HEAD
  }, [params.id]);
>>>>>>> origin/main

  const preImage = images[0] ?? null;
  const postImage = images[1] ?? null;

  const runAction = async (label: string, action: () => Promise<void>) => {
    setIsProcessing(true);
    setPageError(null);
    try {
      await action();
    } catch (err: any) {
      setPageError(`${label} unavailable: ${err?.message ?? "request failed"}`);
    } finally {
      setIsProcessing(false);
    }
  };

<<<<<<< HEAD
=======
=======
  }, [params.id, loadResults]);

  const preImage = images[0] ?? null;
  const postImage = images[1] ?? null;

  const runAction = async (label: string, action: () => Promise<void>) => {
    setIsProcessing(true);
    setPageError(null);
    try {
      await action();
    } catch (err: any) {
      setPageError(`${label} unavailable: ${err?.message ?? "request failed"}`);
    } finally {
      setIsProcessing(false);
    }
  };

>>>>>>> origin/main
  const runReconstruction = () =>
    runAction("3D reconstruction", async () => {
      const result = await api.trigger3DReconstruction(params.id);
      setReconResult(result);
    });

  const runDepth = () =>
    runAction("Depth estimation", async () => {
      if (!preImage) throw new Error("Upload an aerial frame first.");
      setDepthResult(await api.triggerDepthEstimation(preImage.id));
    });

  const runSegmentation = () =>
    runAction("Segmentation", async () => {
      if (!preImage) throw new Error("Upload an aerial frame first.");
      setSegmentationResult(await api.triggerSegmentation(preImage.id));
    });

  const runDamage = () =>
    runAction("Damage assessment", async () => {
      if (!preImage || !postImage) {
        throw new Error("Two aligned pre/post aerial frames are required.");
      }
      setDamageResult(await api.triggerDamageAssessment(preImage.id, postImage.id));
    });

  const runChange = () =>
    runAction("Change detection", async () => {
      if (!preImage || !postImage) {
        throw new Error("Two aligned before/after aerial frames are required.");
      }
      setChangeResult(await api.triggerChangeDetection(preImage.id, postImage.id));
    });

  const depthOriginal = useMemo(() => {
    if (!depthResult) return "";
    const match = images.find((image) => image.id === depthResult.image_id);
    return match?.file_path ?? "";
  }, [depthResult, images]);

  const tabs = [
    { id: "3d", label: "3D Photogrammetry", icon: Box },
    { id: "damage", label: "Damage Assessment (xBD)", icon: ShieldAlert },
    { id: "depth", label: "Monocular Depth", icon: Activity },
    { id: "segmentation", label: "Land-Cover Segmentation", icon: Layers },
    { id: "change", label: "Change Detection", icon: GitCompare },
    { id: "imagery", label: "Ingested Imagery", icon: Camera },
  ] as const;

<<<<<<< HEAD
=======
>>>>>>> 0400f2f (p5-udpated)
>>>>>>> origin/main
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
<<<<<<< HEAD
            {project?.name || (loading ? "Loading Mission…" : "Mission")}
=======
<<<<<<< HEAD
            {project?.name || "Loading Mission..."}
=======
            {project?.name || (loading ? "Loading Mission…" : "Mission")}
>>>>>>> 0400f2f (p5-udpated)
>>>>>>> origin/main
            <Badge variant="success" className="text-[10px]">
              Active Session
            </Badge>
          </h1>
          <div className="flex flex-wrap items-center gap-4 text-xs text-muted-foreground mt-1">
            <span className="flex items-center gap-1">
<<<<<<< HEAD
              <MapPin className="w-3.5 h-3.5 text-emerald-400" />{" "}
              {project?.location_name || "Location Unspecified"}
=======
<<<<<<< HEAD
              <MapPin className="w-3.5 h-3.5 text-emerald-400" /> {project?.location_name || "Location Unspecified"}
=======
              <MapPin className="w-3.5 h-3.5 text-emerald-400" />{" "}
              {project?.location_name || "Location Unspecified"}
>>>>>>> 0400f2f (p5-udpated)
>>>>>>> origin/main
            </span>
            <span>•</span>
            <span className="flex items-center gap-1">
              <Camera className="w-3.5 h-3.5 text-emerald-400" /> {images.length} Captures
            </span>
            <span>•</span>
<<<<<<< HEAD
=======
<<<<<<< HEAD
            <span>Created {project?.created_at ? new Date(project.created_at).toLocaleDateString() : ""}</span>
=======
>>>>>>> origin/main
            <span>
              Created{" "}
              {project?.created_at ? new Date(project.created_at).toLocaleDateString() : ""}
            </span>
<<<<<<< HEAD
=======
>>>>>>> 0400f2f (p5-udpated)
>>>>>>> origin/main
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

<<<<<<< HEAD
      {pageError && (
        <div className="p-3 rounded bg-rose-950/60 border border-rose-500/40 text-rose-300 flex items-start gap-2">
          <AlertTriangle className="w-4 h-4 shrink-0" />
          <span>{pageError}</span>
          {images.length > 0 && (
            <button
              onClick={() => (activeTab === "3d" ? runReconstruction() : undefined)}
              className="ml-auto flex items-center gap-1 hover:underline"
            >
              <RefreshCw className="w-3.5 h-3.5" /> Retry
            </button>
          )}
        </div>
      )}

      {/* Workspace Navigation Tabs */}
      <div className="flex items-center gap-1 border-b border-emerald-500/20 pb-1 overflow-x-auto text-xs">
        {tabs.map((tab) => {
=======
<<<<<<< HEAD
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
=======
      {pageError && (
        <div className="p-3 rounded bg-rose-950/60 border border-rose-500/40 text-rose-300 flex items-start gap-2">
          <AlertTriangle className="w-4 h-4 shrink-0" />
          <span>{pageError}</span>
          {images.length > 0 && (
            <button
              onClick={() => (activeTab === "3d" ? runReconstruction() : undefined)}
              className="ml-auto flex items-center gap-1 hover:underline"
            >
              <RefreshCw className="w-3.5 h-3.5" /> Retry
            </button>
          )}
        </div>
      )}

      {/* Workspace Navigation Tabs */}
      <div className="flex items-center gap-1 border-b border-emerald-500/20 pb-1 overflow-x-auto text-xs">
        {tabs.map((tab) => {
>>>>>>> 0400f2f (p5-udpated)
>>>>>>> origin/main
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
<<<<<<< HEAD
                PHOTOGRAMMETRY POINT CLOUD (COLMAP)
=======
<<<<<<< HEAD
                HIGH-DENSITY STRUCTURE FROM MOTION (SfM) POINT CLOUD
>>>>>>> origin/main
              </span>
              <Button
                onClick={runReconstruction}
                variant="primary"
                size="sm"
                isLoading={isProcessing}
                disabled={images.length < 2}
                title={
                  images.length < 2
                    ? "At least two overlapping aerial frames are required"
                    : "Run COLMAP on this mission's frames"
                }
              >
<<<<<<< HEAD
                <Sparkles className="w-3.5 h-3.5 mr-1" /> Run Reconstruction
=======
                Re-Run Triangulation
=======
                PHOTOGRAMMETRY POINT CLOUD (COLMAP)
              </span>
              <Button
                onClick={runReconstruction}
                variant="primary"
                size="sm"
                isLoading={isProcessing}
                disabled={images.length < 2}
                title={
                  images.length < 2
                    ? "At least two overlapping aerial frames are required"
                    : "Run COLMAP on this mission's frames"
                }
              >
                <Sparkles className="w-3.5 h-3.5 mr-1" /> Run Reconstruction
>>>>>>> 0400f2f (p5-udpated)
>>>>>>> origin/main
              </Button>
            </div>

            <AdvancedSpatialViewer3D
              projectName={project?.name}
              locationName={project?.location_name}
<<<<<<< HEAD
              plyUrl={reconResult?.pointcloud_ply_path}
            />
=======
<<<<<<< HEAD
              initialPointCount={85000}
            />
=======
              plyUrl={reconResult?.pointcloud_ply_path}
            />
>>>>>>> origin/main

            {reconResult && (
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
                <div className="p-2.5 rounded bg-forest-900 border border-emerald-500/20">
                  <div className="text-[10px] text-muted-foreground">POINTS</div>
                  <div className="text-cyan-300 font-bold">
                    {reconResult.num_points.toLocaleString()}
                  </div>
                </div>
                <div className="p-2.5 rounded bg-forest-900 border border-emerald-500/20">
                  <div className="text-[10px] text-muted-foreground">CAMERAS</div>
                  <div className="text-white font-bold">{reconResult.camera_count}</div>
                </div>
                <div className="p-2.5 rounded bg-forest-900 border border-emerald-500/20">
                  <div className="text-[10px] text-muted-foreground">REPROJECTION ERROR</div>
                  <div className="text-emerald-300 font-bold">
                    {reconResult.reprojection_error_px === null ||
                    reconResult.reprojection_error_px === undefined
                      ? "not reported"
                      : `${reconResult.reprojection_error_px.toFixed(3)} px`}
                  </div>
                </div>
                <div className="p-2.5 rounded bg-forest-900 border border-emerald-500/20">
                  <div className="text-[10px] text-muted-foreground">GEOREFERENCED</div>
                  <div className="text-amber-300 font-bold">no (unscaled units)</div>
                </div>
              </div>
            )}
<<<<<<< HEAD
=======
>>>>>>> 0400f2f (p5-udpated)
>>>>>>> origin/main
          </div>
        )}

        {/* 2. DAMAGE TAB */}
        {activeTab === "damage" && (
          <div className="glass-panel p-6 rounded-xl border border-emerald-500/25 space-y-5">
            <div className="flex items-center justify-between">
              <div>
<<<<<<< HEAD
                <h3 className="text-base font-bold text-white">xBD Building Damage Assessment</h3>
                <p className="text-muted-foreground text-xs">
                  Pre- vs post-disaster aerial comparison. Requires a verified damage checkpoint.
                </p>
=======
<<<<<<< HEAD
                <h3 className="text-base font-bold text-white">xBD Humanitarian Damage Assessment</h3>
                <p className="text-muted-foreground text-xs">Pre- vs Post-Disaster aerial flight differencing.</p>
>>>>>>> origin/main
              </div>
              <Button
                onClick={runDamage}
                variant="primary"
                size="sm"
                isLoading={isProcessing}
<<<<<<< HEAD
                disabled={!preImage || !postImage}
=======
=======
                <h3 className="text-base font-bold text-white">xBD Building Damage Assessment</h3>
                <p className="text-muted-foreground text-xs">
                  Pre- vs post-disaster aerial comparison. Requires a verified damage checkpoint.
                </p>
              </div>
              <Button
                onClick={runDamage}
                variant="primary"
                size="sm"
                isLoading={isProcessing}
                disabled={!preImage || !postImage}
>>>>>>> 0400f2f (p5-udpated)
>>>>>>> origin/main
              >
                Execute Analysis
              </Button>
            </div>

<<<<<<< HEAD
            {damageResult ? (
              <>
                {preImage && postImage && (
                  <BeforeAfterSlider
                    beforeImage={preImage.file_path}
                    afterImage={damageResult.damage_overlay_path || postImage.file_path}
                    beforeLabel="Pre-event frame"
                    afterLabel="Damage overlay (this run)"
                  />
                )}

=======
<<<<<<< HEAD
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
=======
            {damageResult ? (
              <>
                {preImage && postImage && (
                  <BeforeAfterSlider
                    beforeImage={preImage.file_path}
                    afterImage={damageResult.damage_overlay_path || postImage.file_path}
                    beforeLabel="Pre-event frame"
                    afterLabel="Damage overlay (this run)"
                  />
                )}

>>>>>>> origin/main
                <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                  {(
                    [
                      ["no_damage", "NO DAMAGE", "text-emerald-400"],
                      ["minor_damage", "MINOR DAMAGE", "text-amber-300"],
                      ["major_damage", "MAJOR DAMAGE", "text-orange-400"],
                      ["destroyed", "DESTROYED", "text-rose-400"],
                    ] as const
                  ).map(([key, label, color]) => (
                    <div
                      key={key}
                      className="p-3 rounded bg-forest-900 border border-emerald-500/20"
                    >
                      <div className="text-[10px] text-muted-foreground">{label}</div>
                      <div className={`font-bold text-base mt-0.5 ${color}`}>
                        {damageResult.counts_by_level?.[key] ?? 0} footprints
                      </div>
                    </div>
                  ))}
                </div>

                <div className="flex flex-wrap justify-between gap-4 p-3 rounded bg-forest-900 border border-emerald-500/15">
                  <span>
                    AFFECTED AREA:{" "}
                    <span className="text-amber-400 font-bold">
                      {damageResult.damage_percentage}%
                    </span>
                  </span>
                  <span>
                    SEVERITY INDEX:{" "}
                    <span className="text-white font-semibold">{damageResult.severity_index}</span>
                  </span>
                  <span className="text-muted-foreground">
                    Footprints derived from a pre-image threshold heuristic.
                  </span>
                </div>
              </>
            ) : (
              <NoVerifiedResult label="damage assessment" />
            )}
<<<<<<< HEAD
=======
>>>>>>> 0400f2f (p5-udpated)
>>>>>>> origin/main
          </div>
        )}

        {/* 3. DEPTH TAB */}
        {activeTab === "depth" && (
          <div className="glass-panel p-6 rounded-xl border border-emerald-500/25 space-y-4">
            <div className="flex items-center justify-between">
              <div>
<<<<<<< HEAD
                <h3 className="text-base font-bold text-white">
                  Depth Anything V2 Small — Monocular Depth
                </h3>
                <p className="text-muted-foreground text-xs">
                  Relative inverse-depth map (no metric scale unless a calibration was fitted).
=======
<<<<<<< HEAD
                <h3 className="text-base font-bold text-white">Depth Anything V2 Small — Monocular Depth</h3>
                <p className="text-muted-foreground text-xs">
                  Relative inverse-depth map and relief extraction (no metric scale unless calibrated).
>>>>>>> origin/main
                </p>
              </div>
              <Button
                onClick={runDepth}
                variant="primary"
                size="sm"
                isLoading={isProcessing}
                disabled={!preImage}
              >
                Estimate Depth
              </Button>
            </div>

<<<<<<< HEAD
=======
            <DepthViewer
              originalImage="https://images.unsplash.com/photo-1508873696983-2df5293cb32f?auto=format&fit=crop&w=1200&q=80"
              depthMapUrl="https://images.unsplash.com/photo-1579546929518-9e396f3cc809?auto=format&fit=crop&w=1200&q=80"
              relativeMin={0.02}
              relativeMax={0.97}
              relativeMean={0.41}
              depthType="relative"
              modelLabel="Depth Anything V2 Small"
            />
=======
                <h3 className="text-base font-bold text-white">
                  Depth Anything V2 Small — Monocular Depth
                </h3>
                <p className="text-muted-foreground text-xs">
                  Relative inverse-depth map (no metric scale unless a calibration was fitted).
                </p>
              </div>
              <Button
                onClick={runDepth}
                variant="primary"
                size="sm"
                isLoading={isProcessing}
                disabled={!preImage}
              >
                Estimate Depth
              </Button>
            </div>

>>>>>>> origin/main
            {depthResult && depthOriginal ? (
              <DepthViewer
                originalImage={depthOriginal}
                depthMapUrl={depthResult.colormap_path}
                minDepth={depthResult.min_depth_m}
                maxDepth={depthResult.max_depth_m}
                meanDepth={depthResult.mean_depth_m}
                relativeMin={depthResult.relative_min}
                relativeMax={depthResult.relative_max}
                relativeMean={depthResult.relative_mean}
                depthType={depthResult.depth_type}
                modelLabel={depthResult.model_label}
              />
            ) : (
              <NoVerifiedResult label="depth estimation" />
            )}
<<<<<<< HEAD
=======
>>>>>>> 0400f2f (p5-udpated)
>>>>>>> origin/main
          </div>
        )}

        {/* 4. SEGMENTATION TAB */}
        {activeTab === "segmentation" && (
          <div className="glass-panel p-6 rounded-xl border border-emerald-500/25 space-y-4">
<<<<<<< HEAD
            <div className="flex items-center justify-between">
              <div>
                <h3 className="text-base font-bold text-white">
                  7-Class Land Use &amp; Land Cover Segmentation
                </h3>
                <p className="text-muted-foreground text-xs">
                  Requires a verified segmentation checkpoint; no accuracy figure is claimed.
                </p>
              </div>
              <Button
                onClick={runSegmentation}
                variant="primary"
                size="sm"
                isLoading={isProcessing}
                disabled={!preImage}
=======
<<<<<<< HEAD
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
>>>>>>> origin/main
              >
                Run Segmentation
              </Button>
            </div>
<<<<<<< HEAD
=======
=======
            <div className="flex items-center justify-between">
              <div>
                <h3 className="text-base font-bold text-white">
                  7-Class Land Use &amp; Land Cover Segmentation
                </h3>
                <p className="text-muted-foreground text-xs">
                  Requires a verified segmentation checkpoint; no accuracy figure is claimed.
                </p>
              </div>
              <Button
                onClick={runSegmentation}
                variant="primary"
                size="sm"
                isLoading={isProcessing}
                disabled={!preImage}
              >
                Run Segmentation
              </Button>
            </div>
>>>>>>> origin/main

            {segmentationResult ? (
              <>
                <div className="relative rounded-lg overflow-hidden border border-emerald-500/30 aspect-video">
                  <img
                    src={segmentationResult.overlay_path}
                    alt="Segmentation overlay from this run"
                    className="w-full h-full object-cover"
                  />
                </div>
                <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
                  {Object.entries(segmentationResult.class_distribution).map(([cls, pct]) => (
                    <div
                      key={cls}
                      className="p-2.5 rounded bg-forest-900 border border-emerald-500/15 text-center"
                    >
                      <div className="text-[10px] text-muted-foreground uppercase">{cls}</div>
                      <div className="text-emerald-400 font-bold text-sm mt-0.5">{pct}%</div>
                    </div>
                  ))}
                </div>
                {segmentationResult.geojson_path && (
                  <a
                    href={segmentationResult.geojson_path}
                    download
                    className="text-emerald-400 font-bold hover:underline flex items-center gap-1"
                  >
                    <Download className="w-3.5 h-3.5" /> Download GeoJSON
                  </a>
                )}
              </>
            ) : (
              <NoVerifiedResult label="segmentation" />
            )}
<<<<<<< HEAD
=======
>>>>>>> 0400f2f (p5-udpated)
>>>>>>> origin/main
          </div>
        )}

        {/* 5. CHANGE TAB */}
        {activeTab === "change" && (
          <div className="glass-panel p-6 rounded-xl border border-emerald-500/25 space-y-4">
<<<<<<< HEAD
=======
<<<<<<< HEAD
            <h3 className="text-base font-bold text-white">Bi-Temporal Divergence Heatmap</h3>
            <BeforeAfterSlider
              beforeImage="https://images.unsplash.com/photo-1508873696983-2df5293cb32f?auto=format&fit=crop&w=1200&q=80"
              afterImage="https://images.unsplash.com/photo-1579546929518-9e396f3cc809?auto=format&fit=crop&w=1200&q=80"
              beforeLabel="Flight Baseline T0"
              afterLabel="Divergence Heatmap T1"
            />
=======
>>>>>>> origin/main
            <div className="flex items-center justify-between">
              <div>
                <h3 className="text-base font-bold text-white">Bi-Temporal Divergence</h3>
                <p className="text-muted-foreground text-xs">
                  Pixel-level change between two aligned frames with statistics from this run.
                </p>
              </div>
              <Button
                onClick={runChange}
                variant="primary"
                size="sm"
                isLoading={isProcessing}
                disabled={!preImage || !postImage}
              >
                Run Change Detection
              </Button>
            </div>

            {changeResult && preImage ? (
              <>
                <BeforeAfterSlider
                  beforeImage={preImage.file_path}
                  afterImage={changeResult.heatmap_path}
                  beforeLabel="Baseline frame"
                  afterLabel="Divergence heatmap (this run)"
                />
                <div className="flex flex-wrap justify-between gap-4 p-3 rounded bg-forest-900 border border-emerald-500/15">
                  <span>
                    CHANGED AREA:{" "}
                    <span className="text-amber-400 font-bold">{changeResult.changed_area_pct}%</span>
                  </span>
                  <span>
                    CHANGED PIXELS:{" "}
                    <span className="text-white font-semibold">
                      {changeResult.changed_pixels.toLocaleString()} px
                    </span>
                  </span>
                  <span>
                    SIGNIFICANCE:{" "}
                    <span className="text-emerald-300 font-semibold">
                      {changeResult.significance_score}
                    </span>
                  </span>
                </div>
              </>
            ) : (
              <NoVerifiedResult label="change detection" />
            )}
<<<<<<< HEAD
=======
>>>>>>> 0400f2f (p5-udpated)
>>>>>>> origin/main
          </div>
        )}

        {/* 6. IMAGERY TAB */}
        {activeTab === "imagery" && (
          <div className="space-y-4">
            <h3 className="text-base font-bold text-white">Ingested UAV Survey Imagery</h3>
<<<<<<< HEAD
            {images.length === 0 ? (
              <NoVerifiedResult label="uploaded aerial" />
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {images.map((img) => (
                  <div
                    key={img.id}
                    className="glass-panel p-4 rounded-lg border border-emerald-500/20 flex gap-4"
                  >
                    <div className="w-36 h-28 rounded overflow-hidden shrink-0 bg-forest-950 border border-emerald-500/20">
                      <img
                        src={img.thumbnail_path}
                        alt={img.filename}
                        className="w-full h-full object-cover"
                      />
                    </div>
                    <div className="space-y-1">
                      <div className="text-white font-bold">{img.filename}</div>
                      <div className="text-muted-foreground">
                        {img.width}x{img.height} px
=======
<<<<<<< HEAD
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
>>>>>>> origin/main
                      </div>
                      {img.telemetry && (
                        <div className="text-[10px] text-emerald-300">
                          {img.telemetry.camera_model} | {img.telemetry.altitude_m ?? "n/a"}m AGL
                        </div>
                      )}
                    </div>
                  </div>
<<<<<<< HEAD
                ))}
              </div>
            )}
=======
                </div>
              ))}
            </div>
=======
            {images.length === 0 ? (
              <NoVerifiedResult label="uploaded aerial" />
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {images.map((img) => (
                  <div
                    key={img.id}
                    className="glass-panel p-4 rounded-lg border border-emerald-500/20 flex gap-4"
                  >
                    <div className="w-36 h-28 rounded overflow-hidden shrink-0 bg-forest-950 border border-emerald-500/20">
                      <img
                        src={img.thumbnail_path}
                        alt={img.filename}
                        className="w-full h-full object-cover"
                      />
                    </div>
                    <div className="space-y-1">
                      <div className="text-white font-bold">{img.filename}</div>
                      <div className="text-muted-foreground">
                        {img.width}x{img.height} px
                      </div>
                      {img.telemetry && (
                        <div className="text-[10px] text-emerald-300">
                          {img.telemetry.camera_model} | {img.telemetry.altitude_m ?? "n/a"}m AGL
                        </div>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            )}
>>>>>>> 0400f2f (p5-udpated)
>>>>>>> origin/main
          </div>
        )}
      </div>
    </div>
  );
}

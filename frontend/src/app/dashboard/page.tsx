"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import dynamic from "next/dynamic";
import {
  Activity,
  FolderKanban,
  UploadCloud,
  Sparkles,
  Box,
  History,
  Cpu,
  Settings,
  Plus,
  Trash2,
  CheckCircle2,
  Clock,
  AlertTriangle,
  Layers,
  ShieldAlert,
  GitCompare,
  ArrowRight,
  ExternalLink,
  MapPin,
  RefreshCw,
  FileCheck2,
  Download,
  Info,
  Radio,
  Sliders,
  Maximize2,
  Video,
  Film,
  Play,
  Compass,
  X
} from "lucide-react";
import { Button } from "@/components/ui/Button";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { BeforeAfterSlider } from "@/components/viewer/BeforeAfterSlider";
import { DepthViewer } from "@/components/viewer/DepthViewer";
import { SegmentationOverlay } from "@/components/viewer/SegmentationOverlay";
import { api } from "@/lib/api";
import { uploadOutcome } from "@/lib/integrity.mjs";
import {
  Project,
  AerialImage,
  AnalysisJob,
  DepthResult,
  SegmentationResult,
  DamageAssessmentResult,
  ChangeDetectionResult,
  Reconstruction3DResult
} from "@/types";

// Dynamic import for 3D visualizer
const AdvancedSpatialViewer3D = dynamic(
  () =>
    import("@/components/viewer/AdvancedSpatialViewer3D").then(
      (mod) => mod.AdvancedSpatialViewer3D
    ),
  {
    ssr: false,
    loading: () => (
      <div className="h-[620px] w-full bg-forest-950 flex flex-col items-center justify-center gap-2 border border-emerald-500/20 rounded-xl font-mono text-xs text-emerald-400">
        <div className="relative flex h-4 w-4">
          <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75" />
          <span className="relative inline-flex rounded-full h-4 w-4 bg-emerald-500" />
        </div>
        <span>SPATIAL POINT CLOUD VIEWER INITIALIZING...</span>
      </div>
    ),
  }
);

function toMediaUrl(path?: string | null): string {
  if (!path) return "";
  let clean = path.replace(/\\/g, "/");
  if (clean.startsWith("http://") || clean.startsWith("https://")) {
    return clean;
  }
  const storageIndex = clean.indexOf("storage/");
  if (storageIndex !== -1) {
    clean = "/" + clean.slice(storageIndex);
  } else if (!clean.startsWith("/")) {
    clean = "/" + clean;
  }
  return clean;
}

export default function DashboardPage() {
  const [activeTab, setActiveTab] = useState<
    "overview" | "projects" | "upload" | "ai" | "viewer3d" | "jobs" | "models" | "settings"
  >("overview");

  const [aiSubTab, setAiSubTab] = useState<"depth" | "segmentation" | "damage" | "change">("depth");

  // Core Data States
  const [projects, setProjects] = useState<Project[]>([]);
  const [selectedProjectId, setSelectedProjectId] = useState<string>("");
  const [selectedImageId, setSelectedImageId] = useState<string>("");
  const [selectedPostImageId, setSelectedPostImageId] = useState<string>("");
  const [uploadMode, setUploadMode] = useState<"video" | "images">("video");
  const [images, setImages] = useState<AerialImage[]>([]);
  const [jobs, setJobs] = useState<AnalysisJob[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);

  // Analysis Result States
  const [depthResult, setDepthResult] = useState<DepthResult | null>(null);
  const [segmentationResult, setSegmentationResult] = useState<SegmentationResult | null>(null);
  const [damageResult, setDamageResult] = useState<DamageAssessmentResult | null>(null);
  const [changeResult, setChangeResult] = useState<ChangeDetectionResult | null>(null);
  const [reconResult, setReconResult] = useState<Reconstruction3DResult | null>(null);
  const [activeInferencing, setActiveInferencing] = useState<string | null>(null);

  const [analysisError, setAnalysisError] = useState<string | null>(null);
  const [damageViewMode, setDamageViewMode] = useState<"overlay" | "slider">("overlay");
  const [changeViewMode, setChangeViewMode] = useState<"heatmap" | "mask" | "slider">("heatmap");

  // Upload state — a success message is only shown after the backend confirms stored frames.
  const [uploadFiles, setUploadFiles] = useState<File[]>([]);
  const [uploading, setUploading] = useState(false);
  const [uploadStatus, setUploadStatus] = useState<
    { kind: "success" | "error"; message: string } | null
  >(null);

  // Drone Video States
  const [videoFile, setVideoFile] = useState<File | null>(null);
  const [telemetryFile, setTelemetryFile] = useState<File | null>(null);
  const [videoUploading, setVideoUploading] = useState(false);
  const [projectVideos, setProjectVideos] = useState<any[]>([]);
  const [selectedVideo, setSelectedVideo] = useState<any | null>(null);
  const [processingVideo, setProcessingVideo] = useState(false);
  const [videoProcessStatus, setVideoProcessStatus] = useState<string | null>(null);

  // Create Project Modal
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [newProject, setNewProject] = useState({
    name: "",
    location_name: "",
    description: "",
    center_lat: 20.316,
    center_lon: 86.611,
  });

  // Settings State
  const [settingsState, setSettingsState] = useState({
    crs: "WGS84 (EPSG:4326)",
    apiEndpoint: "http://localhost:8000/api/v1",
    autoRefresh: true,
    lodLevel: "High (125k pts)",
    exportFormat: "PLY Point Cloud",
  });

  // Initial Fetch
  const fetchData = async () => {
    try {
      setRefreshing(true);
      const projList = await api.getProjects().catch(() => []);
      setProjects(projList);

      let activeId = selectedProjectId;
      if (!activeId || !projList.some((p) => p.id === activeId)) {
        activeId = projList[0]?.id || "";
      }
      setSelectedProjectId(activeId);

      if (!activeId) {
        setImages([]);
        setJobs([]);
        setProjectVideos([]);
        return;
      }

      const [imgList, jobList] = await Promise.all([
        api.getProjectImages(activeId).catch(() => []),
        api.getProjectJobs(activeId).catch(() => []),
      ]);
      setImages(imgList);
      setJobs(jobList);

      const img1 = imgList[0]?.id || "";
      const img2 = imgList[1]?.id || imgList[0]?.id || "";
      if (img1 && (!selectedImageId || !imgList.some((img) => img.id === selectedImageId))) {
        setSelectedImageId(img1);
      }
      if (img2 && (!selectedPostImageId || !imgList.some((img) => img.id === selectedPostImageId))) {
        setSelectedPostImageId(img2);
      }

      if (img1) {
        try {
          const dRes = await api.getDepthResult(img1);
          setDepthResult(dRes);
        } catch {
          setDepthResult(null);
        }
        try {
          const sRes = await api.getSegmentationResult(img1);
          setSegmentationResult(sRes);
        } catch {
          setSegmentationResult(null);
        }
      } else {
        setDepthResult(null);
        setSegmentationResult(null);
      }

      if (img1 && img2) {
        try {
          const dmgRes = await api.getDamageResult(img1, img2);
          setDamageResult(dmgRes);
        } catch {
          setDamageResult(null);
        }
        try {
          const cRes = await api.getChangeResult(img1, img2);
          setChangeResult(cRes);
        } catch {
          setChangeResult(null);
        }
      } else {
        setDamageResult(null);
        setChangeResult(null);
      }

      try {
        const rRes = await api.get3DReconstructionResult(activeId);
        setReconResult(rRes);
      } catch {
        setReconResult(null);
      }

      try {
        const vids = await api.getProjectVideos(activeId);
        setProjectVideos(vids);
        if (vids.length > 0) setSelectedVideo(vids[0]);
      } catch {
        setProjectVideos([]);
      }
    } catch (err) {
      console.error("Dashboard fetch error:", err);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  const handleVideoUploadSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!videoFile) return;
    setVideoUploading(true);
    setUploadStatus(null);
    try {
      const res = await api.uploadDroneVideo(selectedProjectId, videoFile, telemetryFile);
      setProjectVideos((prev) => [res, ...prev]);
      setSelectedVideo(res);
      setVideoFile(null);
      setTelemetryFile(null);
      setUploadStatus(uploadOutcome({ ok: true, uploadedCount: 1 }));
      setVideoProcessStatus("Single-pass drone video uploaded and validated. Ready for automated 3D reconstruction.");
    } catch (err: any) {
      setUploadStatus(
        uploadOutcome({
          ok: false,
          errorMessage: err.message || "Failed to upload drone video",
        })
      );
    } finally {
      setVideoUploading(false);
    }
  };

  const handleStartProcessingVideo = async (video: any) => {
    if (!video || !video.mission_id) return;
    setProcessingVideo(true);
    setVideoProcessStatus("Dispatching single-pass video pipeline (PyAV -> Sharpness Gate -> Perception -> 3D Surface)...");
    try {
      await api.enqueueVideoProcessing(video.mission_id, video.id);
      setVideoProcessStatus("Pipeline active: extracting keyframes, computing depth & building 3D model.");
      setTimeout(() => {
        fetchData();
      }, 3000);
    } catch (err: any) {
      setVideoProcessStatus(`Status: ${err.message || "Enqueued"}`);
    } finally {
      setProcessingVideo(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, [selectedProjectId]);

  // Automatically refresh AI analysis when the user selects a different image frame
  useEffect(() => {
    if (!selectedImageId) return;
    api.getDepthResult(selectedImageId).then(setDepthResult).catch(() => setDepthResult(null));
    api.getSegmentationResult(selectedImageId).then(setSegmentationResult).catch(() => setSegmentationResult(null));
  }, [selectedImageId]);

  useEffect(() => {
    if (!selectedImageId || !selectedPostImageId) return;
    api.getDamageResult(selectedImageId, selectedPostImageId).then(setDamageResult).catch(() => setDamageResult(null));
    api.getChangeResult(selectedImageId, selectedPostImageId).then(setChangeResult).catch(() => setChangeResult(null));
  }, [selectedImageId, selectedPostImageId]);

  // Project Change
  const handleSelectProject = (id: string) => {
    setSelectedProjectId(id);
  };

  // Create Project Handler
  const handleCreateProject = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newProject.name.trim()) return;
    try {
      const created = await api.createProject({
        name: newProject.name,
        location_name: newProject.location_name || "Custom Flight Sector",
        description: newProject.description || "UAV Photogrammetry Mission",
        center_lat: newProject.center_lat,
        center_lon: newProject.center_lon,
      });
      setProjects([created, ...projects]);
      setSelectedProjectId(created.id);
      setShowCreateModal(false);
      setNewProject({ name: "", location_name: "", description: "", center_lat: 20.316, center_lon: 86.611 });
    } catch (err: any) {
      alert("Failed to create project: " + err.message);
    }
  };

  // Delete Project Handler
  const handleDeleteProject = async (id: string) => {
    if (!confirm("Are you sure you want to permanently delete this aerial mission?")) return;
    try {
      await api.deleteProject(id);
      const remaining = projects.filter((p) => p.id !== id);
      setProjects(remaining);
      if (selectedProjectId === id && remaining.length > 0) {
        setSelectedProjectId(remaining[0].id);
      }
    } catch (err: any) {
      alert("Delete failed: " + err.message);
    }
  };

  // Image Upload Handler — success is only reported when the backend confirms records.
  const handleUploadSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (uploadFiles.length === 0) return;
    setUploading(true);
    setUploadStatus(null);
    try {
      const uploaded = await api.uploadImages(selectedProjectId, uploadFiles);
      setImages([...uploaded, ...images]);
      setUploadStatus(uploadOutcome({ ok: true, uploadedCount: uploaded.length }));
      // Keep the selection only when the backend stored nothing (retry path).
      if (uploaded.length > 0) setUploadFiles([]);
    } catch (err: any) {
      // The selection stays in place so the operator can retry the same upload.
      setUploadStatus(
        uploadOutcome({
          ok: false,
          errorMessage: err?.message ?? "No response from the backend",
        })
      );
    } finally {
      setUploading(false);
    }
  };

  // Trigger AI Depth
  const triggerDepth = async (imageId?: string) => {
    const targetId = imageId || selectedImageId || images[0]?.id;
    if (!targetId) {
      setAnalysisError("No aerial image available in this mission to estimate depth.");
      return;
    }
    setActiveInferencing("depth");
    setAnalysisError(null);
    try {
      const res = await api.triggerDepthEstimation(targetId);
      setDepthResult(res);
      fetchData();
    } catch (err: any) {
      setAnalysisError(err?.message ?? "Depth estimation failed");
    } finally {
      setActiveInferencing(null);
    }
  };

  // Trigger AI Segmentation
  const triggerSegmentation = async (imageId?: string) => {
    const targetId = imageId || selectedImageId || images[0]?.id;
    if (!targetId) {
      setAnalysisError("No aerial image available in this mission to segment.");
      return;
    }
    setActiveInferencing("segmentation");
    setAnalysisError(null);
    try {
      const res = await api.triggerSegmentation(targetId);
      setSegmentationResult(res);
      fetchData();
    } catch (err: any) {
      setSegmentationResult(null);
      setAnalysisError(err?.message ?? "Segmentation failed");
    } finally {
      setActiveInferencing(null);
    }
  };

  // Trigger Damage Assessment
  const triggerDamage = async (preId?: string, postId?: string) => {
    const pre = preId || selectedImageId || images[0]?.id;
    const post = postId || selectedPostImageId || images[1]?.id || images[0]?.id;
    if (!pre || !post) {
      setAnalysisError("Two aerial images (pre and post disaster) are required for damage evaluation.");
      return;
    }
    setActiveInferencing("damage");
    setAnalysisError(null);
    try {
      const res = await api.triggerDamageAssessment(pre, post);
      setDamageResult(res);
      fetchData();
    } catch (err: any) {
      setDamageResult(null);
      setAnalysisError(err?.message ?? "Damage assessment failed");
    } finally {
      setActiveInferencing(null);
    }
  };

  // Trigger Change Detection
  const triggerChange = async (beforeId?: string, afterId?: string) => {
    const before = beforeId || selectedImageId || images[0]?.id;
    const after = afterId || selectedPostImageId || images[1]?.id || images[0]?.id;
    if (!before || !after) {
      setAnalysisError("Two aerial images are required for change detection.");
      return;
    }
    setActiveInferencing("change");
    try {
      const res = await api.triggerChangeDetection(before, after);
      setChangeResult(res);
      fetchData();
    } catch (err: any) {
      setAnalysisError(err?.message ?? "Change detection failed");
    } finally {
      setActiveInferencing(null);
    }
  };

  // Trigger 3D Reconstruction
  const trigger3D = async () => {
    if (!selectedProjectId) {
      setAnalysisError("Please select a mission first.");
      return;
    }
    setActiveInferencing("3d");
    setAnalysisError(null);
    try {
      const res = await api.trigger3DReconstruction(selectedProjectId);
      setReconResult(res);
      fetchData();
    } catch (err: any) {
      // Reconstruction unavailability/failure is surfaced; no geometry is displayed.
      setReconResult(null);
      setAnalysisError(err?.message ?? "3D reconstruction failed");
    } finally {
      setActiveInferencing(null);
    }
  };

  const currentProject = projects.find((p) => p.id === selectedProjectId) || projects[0];
  const activeImage = images.find((i) => i.id === selectedImageId) || images[0];
  const activePostImage = images.find((i) => i.id === selectedPostImageId) || images[1] || images[0];

  return (
    <div className="flex-1 flex flex-col bg-forest-950 text-foreground min-h-[calc(100vh-3.5rem)] selection:bg-emerald-500 selection:text-black">
      {/* Top Aerospace Mission Selector & Control Bar */}
      <div className="border-b border-emerald-500/20 bg-forest-900/70 px-4 sm:px-6 py-3 flex flex-wrap items-center justify-between gap-4 font-mono text-xs">
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-2">
            <span className="text-muted-foreground text-[10px] uppercase">ACTIVE MISSION:</span>
            <select
              value={selectedProjectId}
              onChange={(e) => handleSelectProject(e.target.value)}
              className="bg-forest-950 border border-emerald-500/30 text-white rounded px-3 py-1 font-mono text-xs focus:outline-none focus:border-emerald-400"
            >
              {projects.map((p) => (
                <option key={p.id} value={p.id}>
                  {p.name}
                </option>
              ))}
            </select>
          </div>

          <div className="hidden lg:flex items-center gap-2 text-muted-foreground text-[11px]">
            <MapPin className="w-3.5 h-3.5 text-emerald-400" />
            <span>{currentProject?.location_name || "Location Unspecified"}</span>
          </div>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={fetchData}
            disabled={refreshing}
            className="flex items-center gap-1.5 px-2.5 py-1 rounded bg-forest-950 border border-emerald-500/20 hover:border-emerald-500/40 text-muted-foreground hover:text-white transition-all text-[11px]"
          >
            <RefreshCw className={`w-3 h-3 ${refreshing ? "animate-spin text-emerald-400" : ""}`} />
            <span>{refreshing ? "SYNCING..." : "SYNC DB"}</span>
          </button>

          <Button
            onClick={() => setShowCreateModal(true)}
            variant="tactical"
            size="sm"
            className="text-[11px]"
          >
            <Plus className="w-3.5 h-3.5 mr-1" /> NEW MISSION
          </Button>
        </div>
      </div>

      {/* Main Operational Container */}
      <div className="flex-1 max-w-7xl w-full mx-auto p-4 sm:p-6 flex flex-col gap-6">
        {/* Navigation Tabs Bar */}
        <div className="flex items-center gap-1 overflow-x-auto pb-1 border-b border-emerald-500/15 font-mono text-xs">
          {[
            { id: "overview", label: "Overview", icon: Activity },
            { id: "projects", label: "Projects", icon: FolderKanban },
            { id: "upload", label: "Drone Video Ingestion", icon: Video },
            { id: "ai", label: "AI Analysis Hub", icon: Sparkles },
            { id: "viewer3d", label: "3D Point Cloud", icon: Box },
            { id: "jobs", label: "Job History", icon: History },
            { id: "models", label: "Model Information", icon: Cpu },
            { id: "settings", label: "Settings", icon: Settings },
          ].map((tab) => {
            const Icon = tab.icon;
            const isActive = activeTab === tab.id;
            return (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id as any)}
                className={`flex items-center gap-2 px-3.5 py-2 rounded-t transition-all shrink-0 ${
                  isActive
                    ? "bg-forest-900 text-emerald-300 font-bold border-t-2 border-emerald-400 border-x border-emerald-500/20 shadow-sm"
                    : "text-muted-foreground hover:text-white hover:bg-forest-900/50"
                }`}
              >
                <Icon className={`w-3.5 h-3.5 ${isActive ? "text-emerald-400" : "text-muted-foreground"}`} />
                <span>{tab.label}</span>
              </button>
            );
          })}
        </div>

        {/* ============================================================== */}
        {/* TAB 1: OVERVIEW */}
        {/* ============================================================== */}
        {activeTab === "overview" && (
          <div className="flex flex-col gap-6">
            {/* KPI Cards */}
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
              <Card className="glass-panel border-emerald-500/20">
                <CardContent className="p-4 flex items-center justify-between">
                  <div>
                    <p className="text-[10px] font-mono uppercase tracking-wider text-muted-foreground">
                      ACTIVE MISSIONS
                    </p>
                    <h3 className="text-2xl font-black text-white mt-1">
                      {projects.length}
                    </h3>
                    <p className="text-[10px] font-mono text-emerald-400 mt-0.5">
                      Stored missions
                    </p>
                  </div>
                  <div className="h-10 w-10 rounded bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 flex items-center justify-center">
                    <FolderKanban className="w-5 h-5" />
                  </div>
                </CardContent>
              </Card>

              <Card className="glass-panel border-emerald-500/20">
                <CardContent className="p-4 flex items-center justify-between">
                  <div>
                    <p className="text-[10px] font-mono uppercase tracking-wider text-muted-foreground">
                      INGESTED DRONE FRAMES
                    </p>
                    <h3 className="text-2xl font-black text-white mt-1">
                      {images.length}
                    </h3>
                    <p className="text-[10px] font-mono text-emerald-400 mt-0.5">
                      Backend-confirmed uploads
                    </p>
                  </div>
                  <div className="h-10 w-10 rounded bg-sky-500/10 border border-sky-500/20 text-sky-400 flex items-center justify-center">
                    <UploadCloud className="w-5 h-5" />
                  </div>
                </CardContent>
              </Card>

              <Card className="glass-panel border-emerald-500/20">
                <CardContent className="p-4 flex items-center justify-between">
                  <div>
                    <p className="text-[10px] font-mono uppercase tracking-wider text-muted-foreground">
                      STRUCTURES ASSESSED (xBD)
                    </p>
                    <h3 className="text-2xl font-black text-rose-400 mt-1">
                      {damageResult ? damageResult.total_buildings : "—"}
                    </h3>
                    <p className="text-[10px] font-mono text-rose-300 mt-0.5">
                      {damageResult ? "4-Tier Classification" : "No verified assessment"}
                    </p>
                  </div>
                  <div className="h-10 w-10 rounded bg-rose-500/10 border border-rose-500/20 text-rose-400 flex items-center justify-center">
                    <ShieldAlert className="w-5 h-5" />
                  </div>
                </CardContent>
              </Card>

              <Card className="glass-panel border-emerald-500/20">
                <CardContent className="p-4 flex items-center justify-between">
                  <div>
                    <p className="text-[10px] font-mono uppercase tracking-wider text-muted-foreground">
                      3D POINT CLOUD ASSETS
                    </p>
                    <h3 className="text-2xl font-black text-cyan-400 mt-1">
                      {reconResult ? `${(reconResult.num_points / 1000).toFixed(0)}K pts` : "—"}
                    </h3>
                    <p className="text-[10px] font-mono text-cyan-300 mt-0.5">
                      {reconResult ? `${(reconResult.num_points / 1000).toFixed(0)}K pts · Verified 3D Surface` : "No verified reconstruction"}
                    </p>
                  </div>
                  <div className="h-10 w-10 rounded bg-cyan-500/10 border border-cyan-500/20 text-cyan-400 flex items-center justify-center">
                    <Box className="w-5 h-5" />
                  </div>
                </CardContent>
              </Card>
            </div>

            {/* Live 3D Surface Preview Card */}
            <Card className="glass-panel border-emerald-500/25">
              <CardHeader className="p-4 border-b border-emerald-500/15 flex flex-row items-center justify-between">
                <div>
                  <CardTitle className="text-sm font-bold font-mono flex items-center gap-2">
                    <Box className="w-4 h-4 text-emerald-400" />
                    PRIMARY 3D SPATIAL SURFACE // {currentProject?.name}
                  </CardTitle>
                  <CardDescription className="text-xs">
                    Multi-view dense photogrammetric point cloud and digital elevation surface.
                  </CardDescription>
                </div>
                <Button
                  onClick={() => setActiveTab("viewer3d")}
                  variant="tactical"
                  size="sm"
                >
                  <Maximize2 className="w-3.5 h-3.5 mr-1" /> FULLSCREEN VIEWER
                </Button>
              </CardHeader>
              <CardContent className="p-4">
                <AdvancedSpatialViewer3D
                  projectName={currentProject?.name}
                  locationName={currentProject?.location_name}
                  plyUrl={toMediaUrl(reconResult?.pointcloud_ply_path)}
                />
              </CardContent>
            </Card>

            {/* Active Survey Missions Table */}
            <div className="rounded-lg border border-emerald-500/20 overflow-hidden bg-forest-900/60 font-mono text-xs">
              <div className="p-3.5 border-b border-emerald-500/20 flex items-center justify-between bg-forest-900">
                <span className="font-bold text-white flex items-center gap-2">
                  <FolderKanban className="w-4 h-4 text-emerald-400" />
                  DATABASE SURVEY MISSIONS
                </span>
                <span className="text-[11px] text-muted-foreground">{projects.length} RECORDS CONNECTED</span>
              </div>
              <div className="overflow-x-auto">
                <table className="w-full text-left">
                  <thead className="bg-forest-950 text-[10px] uppercase text-muted-foreground border-b border-emerald-500/15">
                    <tr>
                      <th className="px-4 py-2.5">Mission Name</th>
                      <th className="px-4 py-2.5">Location</th>
                      <th className="px-4 py-2.5">Images</th>
                      <th className="px-4 py-2.5">Coordinates</th>
                      <th className="px-4 py-2.5">Created</th>
                      <th className="px-4 py-2.5 text-right">Actions</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-emerald-500/10">
                    {projects.map((p) => (
                      <tr
                        key={p.id}
                        className={`hover:bg-forest-800/40 transition-colors ${
                          p.id === selectedProjectId ? "bg-forest-800/30" : ""
                        }`}
                      >
                        <td className="px-4 py-3 font-semibold text-white">
                          <button
                            onClick={() => handleSelectProject(p.id)}
                            className="hover:text-emerald-300 text-left"
                          >
                            {p.name}
                          </button>
                        </td>
                        <td className="px-4 py-3 text-muted-foreground">{p.location_name}</td>
                        <td className="px-4 py-3 text-emerald-400 font-semibold">{p.image_count} captures</td>
                        <td className="px-4 py-3 text-muted-foreground text-[11px]">
                          {p.center_lat ? `${p.center_lat.toFixed(4)}°N, ${p.center_lon?.toFixed(4)}°E` : "N/A"}
                        </td>
                        <td className="px-4 py-3 text-muted-foreground text-[11px]">
                          {new Date(p.created_at).toLocaleDateString()}
                        </td>
                        <td className="px-4 py-3 text-right">
                          <Button
                            onClick={() => handleSelectProject(p.id)}
                            variant="outline"
                            size="sm"
                            className="text-[10px] h-7 px-2"
                          >
                            SELECT
                          </Button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        )}

        {/* ============================================================== */}
        {/* TAB 2: PROJECTS */}
        {/* ============================================================== */}
        {activeTab === "projects" && (
          <div className="flex flex-col gap-6">
            <div className="flex items-center justify-between">
              <div>
                <h2 className="text-xl font-bold text-white font-mono">Survey Mission Catalog</h2>
                <p className="text-xs text-muted-foreground">Manage UAV projects connected to SQLite / PostgreSQL storage.</p>
              </div>
              <Button onClick={() => setShowCreateModal(true)} variant="primary" size="sm">
                <Plus className="w-4 h-4 mr-1.5" /> Create New Mission
              </Button>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {projects.map((p) => (
                <div
                  key={p.id}
                  className={`glass-panel p-5 rounded-lg border transition-all flex flex-col justify-between ${
                    p.id === selectedProjectId
                      ? "border-emerald-500 shadow-lg shadow-emerald-950/60"
                      : "border-emerald-500/20 hover:border-emerald-500/40"
                  }`}
                >
                  <div className="space-y-3">
                    <div className="flex items-start justify-between gap-2">
                      <h3 className="text-base font-bold text-white font-mono leading-tight">
                        {p.name}
                      </h3>
                      {p.id === selectedProjectId && (
                        <Badge variant="success" className="text-[10px]">
                          ACTIVE
                        </Badge>
                      )}
                    </div>

                    <p className="text-xs text-muted-foreground line-clamp-2">
                      {p.description}
                    </p>

                    <div className="p-2.5 rounded bg-forest-900 border border-emerald-500/15 font-mono text-[11px] space-y-1">
                      <div className="flex justify-between">
                        <span className="text-muted-foreground">Location:</span>
                        <span className="text-emerald-300 truncate max-w-[150px]">{p.location_name}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-muted-foreground">Images:</span>
                        <span className="text-white font-semibold">{p.image_count}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-muted-foreground">Coordinates:</span>
                        <span className="text-muted-foreground text-[10px]">
                          {p.center_lat ? `${p.center_lat.toFixed(3)}N, ${p.center_lon?.toFixed(3)}E` : "N/A"}
                        </span>
                      </div>
                    </div>
                  </div>

                  <div className="pt-4 mt-3 border-t border-emerald-500/15 flex items-center justify-between gap-2">
                    <Button
                      onClick={() => handleSelectProject(p.id)}
                      variant={p.id === selectedProjectId ? "tactical" : "outline"}
                      size="sm"
                      className="text-xs flex-1"
                    >
                      {p.id === selectedProjectId ? "Engaged" : "Switch to Mission"}
                    </Button>

                    <button
                      onClick={() => handleDeleteProject(p.id)}
                      title="Delete Mission"
                      className="p-1.5 rounded hover:bg-rose-950 text-rose-400 hover:text-rose-200 transition-colors"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* ============================================================== */}
        {/* TAB 3: DRONE VIDEO & FRAME INGESTION PIPELINE */}
        {/* ============================================================== */}
        {activeTab === "upload" && (
          <div className="flex flex-col gap-6">
            <div className="flex flex-wrap items-center justify-between gap-4">
              <div>
                <h2 className="text-xl font-bold text-white font-mono flex items-center gap-2">
                  <Video className="w-5 h-5 text-emerald-400" />
                  Aerial Ingestion &amp; 3D Reconstruction Pipeline
                </h2>
                <p className="text-xs text-muted-foreground mt-1">
                  Ingest UAV video footage or batch aerial still frames for <span className="text-emerald-300 font-bold">{currentProject?.name}</span>.
                </p>
              </div>

              {/* Mode Toggle */}
              <div className="flex items-center gap-1.5 p-1 rounded-lg bg-forest-900 border border-emerald-500/25 font-mono text-xs">
                <button
                  type="button"
                  onClick={() => setUploadMode("video")}
                  className={`flex items-center gap-1.5 px-3.5 py-1.5 rounded transition-all font-bold ${
                    uploadMode === "video"
                      ? "bg-emerald-600 text-white shadow-md shadow-emerald-950/60"
                      : "text-muted-foreground hover:text-white"
                  }`}
                >
                  <Video className="w-3.5 h-3.5" /> Drone Video (.mp4 / .mov)
                </button>
                <button
                  type="button"
                  onClick={() => setUploadMode("images")}
                  className={`flex items-center gap-1.5 px-3.5 py-1.5 rounded transition-all font-bold ${
                    uploadMode === "images"
                      ? "bg-emerald-600 text-white shadow-md shadow-emerald-950/60"
                      : "text-muted-foreground hover:text-white"
                  }`}
                >
                  <UploadCloud className="w-3.5 h-3.5" /> Aerial Frames (.jpg / .tif)
                </button>
              </div>
            </div>

            {/* Mode 1: Drone Video Upload Form */}
            {uploadMode === "video" && (
              <form onSubmit={handleVideoUploadSubmit} className="glass-panel p-6 rounded-xl border border-emerald-500/25 space-y-4">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {/* Video File Dropzone */}
                  <div className="border-2 border-dashed border-emerald-500/30 rounded-lg p-6 flex flex-col items-center justify-center text-center hover:border-emerald-500/60 transition-colors bg-forest-950/40 relative">
                    <Film className="w-10 h-10 text-emerald-400 mb-2" />
                    <p className="text-sm font-bold text-white font-mono">
                      Select Single-Pass Drone Video
                    </p>
                    <p className="text-[11px] text-muted-foreground mt-1">
                      MP4, MOV, M4V, AVI, MKV (H.264, HEVC / 4K / 1080p)
                    </p>
                    <input
                      type="file"
                      accept="video/*,.mp4,.mov,.m4v,.avi,.mkv,.webm"
                      onChange={(e) => {
                        if (e.target.files && e.target.files[0]) {
                          setVideoFile(e.target.files[0]);
                        }
                      }}
                      className="mt-3 text-xs font-mono text-emerald-400 file:mr-3 file:py-1.5 file:px-3 file:rounded file:border-0 file:text-xs file:font-mono file:bg-emerald-600 file:text-white hover:file:bg-emerald-500 cursor-pointer"
                    />
                    {videoFile && (
                      <div className="mt-2 text-xs font-mono text-emerald-300 font-semibold">
                        Selected: {videoFile.name} ({(videoFile.size / 1024 / 1024).toFixed(1)} MB)
                      </div>
                    )}
                  </div>

                  {/* Optional Telemetry File Dropzone */}
                  <div className="border-2 border-dashed border-emerald-500/20 rounded-lg p-6 flex flex-col items-center justify-center text-center hover:border-emerald-500/40 transition-colors bg-forest-950/30 relative">
                    <Compass className="w-10 h-10 text-cyan-400 mb-2" />
                    <p className="text-sm font-bold text-white font-mono">
                      Flight Telemetry Log (Optional)
                    </p>
                    <p className="text-[11px] text-muted-foreground mt-1">
                      CSV, SRT, GPX, or embedded drone GPS flight log
                    </p>
                    <input
                      type="file"
                      accept=".csv,.srt,.gpx,.txt,.json"
                      onChange={(e) => {
                        if (e.target.files && e.target.files[0]) {
                          setTelemetryFile(e.target.files[0]);
                        }
                      }}
                      className="mt-3 text-xs font-mono text-cyan-400 file:mr-3 file:py-1.5 file:px-3 file:rounded file:border-0 file:text-xs file:font-mono file:bg-cyan-600 file:text-white hover:file:bg-cyan-500 cursor-pointer"
                    />
                    {telemetryFile && (
                      <div className="mt-2 text-xs font-mono text-cyan-300 font-semibold">
                        Selected: {telemetryFile.name} ({(telemetryFile.size / 1024).toFixed(1)} KB)
                      </div>
                    )}
                  </div>
                </div>

                <div className="p-3.5 rounded-lg bg-forest-900 border border-emerald-500/20 font-mono text-xs flex flex-wrap items-center justify-between gap-3">
                  <span className="text-emerald-300">
                    {videoFile
                      ? `Ready to ingest drone video: ${videoFile.name} (${(videoFile.size / 1024 / 1024).toFixed(1)} MB)`
                      : "Please choose a UAV flight video file to upload"}
                  </span>
                  <Button
                    type="submit"
                    variant="primary"
                    size="sm"
                    disabled={!videoFile || videoUploading}
                    isLoading={videoUploading}
                    className="font-bold font-mono"
                  >
                    <Video className="w-3.5 h-3.5 mr-1.5" />
                    {videoUploading ? "Ingesting Drone Video..." : "Upload Drone Video & Ingest"}
                  </Button>
                </div>

                {uploadStatus && (
                  <div
                    role="status"
                    aria-live="polite"
                    className={`p-3 rounded text-xs font-mono flex items-start gap-2 ${
                      uploadStatus.kind === "success"
                        ? "bg-forest-900/90 border border-emerald-500/30 text-emerald-300"
                        : "bg-rose-950/60 border border-rose-500/40 text-rose-300"
                    }`}
                  >
                    {uploadStatus.kind === "success" ? (
                      <CheckCircle2 className="w-4 h-4 shrink-0" />
                    ) : (
                      <AlertTriangle className="w-4 h-4 shrink-0" />
                    )}
                    <span>{uploadStatus.message}</span>
                  </div>
                )}
              </form>
            )}

            {/* Mode 2: Still Aerial Images Upload Form */}
            {uploadMode === "images" && (
              <form onSubmit={handleUploadSubmit} className="glass-panel p-6 rounded-xl border border-emerald-500/25 space-y-4">
                <div className="border-2 border-dashed border-emerald-500/30 rounded-lg p-8 flex flex-col items-center justify-center text-center hover:border-emerald-500/60 transition-colors bg-forest-950/40 relative">
                  <UploadCloud className="w-12 h-12 text-emerald-400 mb-2" />
                  <p className="text-sm font-bold text-white font-mono">
                    Select Aerial Frame Captures
                  </p>
                  <p className="text-[11px] text-muted-foreground mt-1 max-w-md">
                    JPEG, PNG, TIFF, DNG orthophotos or multi-view aerial camera snapshots
                  </p>
                  <input
                    type="file"
                    multiple
                    accept="image/*,.tif,.tiff,.dng"
                    onChange={(e) => {
                      if (e.target.files) {
                        setUploadFiles(Array.from(e.target.files));
                      }
                    }}
                    className="mt-4 text-xs font-mono text-emerald-400 file:mr-3 file:py-2 file:px-4 file:rounded file:border-0 file:text-xs file:font-mono file:bg-emerald-600 file:text-white hover:file:bg-emerald-500 cursor-pointer"
                  />
                  {uploadFiles.length > 0 && (
                    <div className="mt-3 text-xs font-mono text-emerald-300 font-semibold">
                      {uploadFiles.length} file(s) selected for ingestion
                    </div>
                  )}
                </div>

                <div className="p-3.5 rounded-lg bg-forest-900 border border-emerald-500/20 font-mono text-xs flex flex-wrap items-center justify-between gap-3">
                  <span className="text-emerald-300">
                    {uploadFiles.length > 0
                      ? `Ready to upload ${uploadFiles.length} frame(s) to ${currentProject?.name}`
                      : "Select one or more image files above"}
                  </span>
                  <Button
                    type="submit"
                    variant="primary"
                    size="sm"
                    disabled={uploadFiles.length === 0 || uploading}
                    isLoading={uploading}
                    className="font-bold font-mono"
                  >
                    <UploadCloud className="w-3.5 h-3.5 mr-1.5" />
                    {uploading ? "Uploading Frames..." : `Ingest ${uploadFiles.length || ""} Frame(s)`}
                  </Button>
                </div>

                {uploadStatus && (
                  <div
                    role="status"
                    aria-live="polite"
                    className={`p-3 rounded text-xs font-mono flex items-start gap-2 ${
                      uploadStatus.kind === "success"
                        ? "bg-forest-900/90 border border-emerald-500/30 text-emerald-300"
                        : "bg-rose-950/60 border border-rose-500/40 text-rose-300"
                    }`}
                  >
                    {uploadStatus.kind === "success" ? (
                      <CheckCircle2 className="w-4 h-4 shrink-0" />
                    ) : (
                      <AlertTriangle className="w-4 h-4 shrink-0" />
                    )}
                    <span>{uploadStatus.message}</span>
                  </div>
                )}
              </form>
            )}

            {/* Ingested Drone Videos & Pipeline Dispatcher */}
            {projectVideos.length > 0 && (
              <div className="space-y-4">
                <h3 className="text-sm font-bold text-white font-mono flex items-center gap-2">
                  <Film className="w-4 h-4 text-emerald-400" />
                  INGESTED DRONE FLIGHT VIDEOS ({projectVideos.length})
                </h3>

                <div className="grid grid-cols-1 gap-4">
                  {projectVideos.map((vid: any) => (
                    <div
                      key={vid.id}
                      className="glass-panel p-5 rounded-xl border border-emerald-500/30 flex flex-col md:flex-row gap-5 font-mono text-xs items-start md:items-center justify-between bg-forest-900/40"
                    >
                      <div className="space-y-1.5 flex-1">
                        <div className="flex items-center gap-2">
                          <span className="text-white font-bold text-sm">{vid.original_filename}</span>
                          <Badge variant="tactical" className="text-[10px]">
                            {vid.validation_status ? vid.validation_status.toUpperCase() : "VALID"}
                          </Badge>
                        </div>
                        <div className="text-[11px] text-muted-foreground flex flex-wrap gap-x-4 gap-y-1">
                          <span>Size: {(vid.file_size_bytes / 1024 / 1024).toFixed(1)} MB</span>
                          {vid.duration_seconds && <span>Duration: {vid.duration_seconds}s</span>}
                          {vid.width && vid.height && <span>Resolution: {vid.width}x{vid.height}</span>}
                          {vid.frame_rate && <span>FPS: {vid.frame_rate}</span>}
                          {vid.codec && <span>Codec: {vid.codec}</span>}
                          {vid.checksum_sha256 && (
                            <span className="text-muted-foreground/80">SHA: {vid.checksum_sha256.substring(0, 12)}...</span>
                          )}
                        </div>
                      </div>

                      <div className="flex flex-wrap gap-2 shrink-0">
                        <Button
                          onClick={() => handleStartProcessingVideo(vid)}
                          variant="tactical"
                          size="sm"
                          isLoading={processingVideo}
                          className="bg-emerald-600 hover:bg-emerald-500 text-white font-bold"
                        >
                          <Play className="w-3.5 h-3.5 mr-1" /> RUN 3D RECONSTRUCTION
                        </Button>
                        <Button
                          onClick={() => setActiveTab("viewer3d")}
                          variant="outline"
                          size="sm"
                        >
                          <Box className="w-3.5 h-3.5 mr-1" /> VIEW 3D MODEL
                        </Button>
                      </div>
                    </div>
                  ))}
                </div>

                {videoProcessStatus && (
                  <div className="p-4 rounded-lg bg-forest-950 border border-emerald-500/30 text-xs font-mono space-y-2">
                    <div className="flex items-center gap-2 text-emerald-400 font-bold">
                      <Radio className="w-4 h-4 animate-pulse" /> PIPELINE PROGRESS:
                    </div>
                    <div className="text-muted-foreground">{videoProcessStatus}</div>
                    <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 pt-2 text-[10px]">
                      <div className="p-2 rounded bg-forest-900 border border-emerald-500/20 text-emerald-300">1. PyAV Demuxing</div>
                      <div className="p-2 rounded bg-forest-900 border border-emerald-500/20 text-emerald-300">2. Blur/Exposure Filter</div>
                      <div className="p-2 rounded bg-forest-900 border border-emerald-500/20 text-emerald-300">3. Duplicate dHash Filter</div>
                      <div className="p-2 rounded bg-forest-900 border border-emerald-500/20 text-emerald-300">4. Depth Anything V2</div>
                      <div className="p-2 rounded bg-forest-900 border border-emerald-500/20 text-emerald-300">5. Dynamic YOLO Mask</div>
                      <div className="p-2 rounded bg-forest-900 border border-emerald-500/20 text-emerald-300">6. 3D Surface Photogrammetry</div>
                      <div className="p-2 rounded bg-forest-900 border border-emerald-500/20 text-emerald-300">7. Dense MVS Point Cloud</div>
                      <div className="p-2 rounded bg-forest-900 border border-emerald-500/20 text-emerald-300">8. Georeferenced Mesh</div>
                    </div>
                  </div>
                )}
              </div>
            )}

            {/* Extracted / Uploaded Frames Gallery */}
            <div className="space-y-4">
              <h3 className="text-sm font-bold text-white font-mono flex items-center justify-between">
                <span className="flex items-center gap-2">
                  <FileCheck2 className="w-4 h-4 text-emerald-400" />
                  INGESTED AERIAL FRAMES &amp; TELEMETRY ({images.length})
                </span>
                {images.length > 0 && (
                  <Button
                    onClick={() => setActiveTab("ai")}
                    variant="outline"
                    size="sm"
                    className="text-[11px]"
                  >
                    <Sparkles className="w-3.5 h-3.5 mr-1 text-emerald-400" /> Analyze in AI Hub
                  </Button>
                )}
              </h3>

              {images.length === 0 ? (
                <div className="p-8 rounded-lg border border-dashed border-emerald-500/20 text-center font-mono text-xs text-muted-foreground bg-forest-950/30">
                  No frames ingested yet for this mission. Upload a drone video or batch image frames above.
                </div>
              ) : (
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {images.map((img, idx) => (
                    <div key={img.id} className="glass-panel p-4 rounded-lg border border-emerald-500/20 flex flex-col sm:flex-row gap-4 font-mono text-xs">
                      <div className="w-full sm:w-44 h-32 rounded overflow-hidden shrink-0 bg-forest-950 border border-emerald-500/20">
                        <img
                          src={toMediaUrl(img.thumbnail_path || img.file_path)}
                          alt={img.filename}
                          className="w-full h-full object-cover"
                        />
                      </div>
                      <div className="flex-1 space-y-1.5 flex flex-col justify-between">
                        <div>
                          <div className="text-white font-bold text-xs truncate">
                            {img.filename}
                          </div>
                          <div className="text-[11px] text-muted-foreground">
                            {img.width}x{img.height} px | {(img.file_size_bytes / 1024 / 1024).toFixed(1)} MB | {img.format}
                          </div>
                          <div className="flex flex-wrap gap-1 mt-1.5">
                            {img.telemetry?.latitude && img.telemetry?.longitude ? (
                              <Badge variant="tactical" className="text-[10px]">
                                GPS: {img.telemetry.latitude.toFixed(4)}, {img.telemetry.longitude.toFixed(4)}
                              </Badge>
                            ) : (
                              <Badge variant="outline" className="text-[10px] text-muted-foreground">
                                Local Frame
                              </Badge>
                            )}
                            <Badge variant="outline" className="text-[10px] text-emerald-400">
                              Frame #{idx + 1}
                            </Badge>
                          </div>
                        </div>

                        <div className="flex items-center gap-2 pt-2 border-t border-emerald-500/15">
                          <Button
                            onClick={() => {
                              setSelectedImageId(img.id);
                              setActiveTab("ai");
                              setAiSubTab("depth");
                            }}
                            variant="tactical"
                            size="sm"
                            className="text-[10px] h-6 px-2"
                          >
                            Depth
                          </Button>
                          <Button
                            onClick={() => {
                              setSelectedImageId(img.id);
                              setActiveTab("ai");
                              setAiSubTab("segmentation");
                            }}
                            variant="outline"
                            size="sm"
                            className="text-[10px] h-6 px-2"
                          >
                            Segment
                          </Button>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        )}

        {/* ============================================================== */}
        {/* TAB 4: AI ANALYSIS HUB */}
        {/* ============================================================== */}
        {activeTab === "ai" && (
          <div className="flex flex-col gap-6">
            <div className="flex flex-wrap items-center justify-between gap-4 border-b border-emerald-500/15 pb-4">
              <div>
                <h2 className="text-xl font-bold text-white font-mono">Neural Inference Engine</h2>
                <p className="text-xs text-muted-foreground">
                  Execute deep learning pipelines on aerial captures for <span className="text-emerald-300 font-bold">{currentProject?.name}</span>.
                </p>
              </div>

              {analysisError && (
                <div className="w-full p-3 rounded bg-rose-950/60 border border-rose-500/40 text-rose-300 text-xs font-mono flex items-start gap-2">
                  <AlertTriangle className="w-4 h-4 shrink-0" />
                  <span>{analysisError}</span>
                </div>
              )}

              {/* Sub-tabs for Depth, Segmentation, Damage, Change */}
              <div className="flex items-center gap-1.5 glass-panel p-1 rounded font-mono text-xs">
                {(["depth", "segmentation", "damage", "change"] as const).map((sub) => (
                  <button
                    key={sub}
                    onClick={() => setAiSubTab(sub)}
                    className={`px-3 py-1.5 rounded uppercase transition-all font-bold ${
                      aiSubTab === sub
                        ? "bg-emerald-600 text-white"
                        : "text-muted-foreground hover:bg-forest-800 hover:text-white"
                    }`}
                  >
                    {sub}
                  </button>
                ))}
              </div>
            </div>

            {/* If no images exist in this mission, display helpful prompt */}
            {images.length === 0 ? (
              <div className="p-8 rounded-lg border border-dashed border-emerald-500/25 bg-forest-950/60 text-center font-mono">
                <AlertTriangle className="w-8 h-8 text-amber-400 mx-auto mb-2" />
                <h3 className="text-white font-bold text-sm">No Aerial Images in Active Mission</h3>
                <p className="text-muted-foreground text-xs mt-1 max-w-md mx-auto">
                  Upload a drone flight video or still aerial frames in the Ingestion tab first to run neural depth, segmentation, or damage evaluation.
                </p>
                <Button onClick={() => setActiveTab("upload")} variant="primary" size="sm" className="mt-4">
                  <Video className="w-4 h-4 mr-1.5" /> Go to Drone Ingestion
                </Button>
              </div>
            ) : (
              <>
                {/* Frame Selector Bar */}
                {(aiSubTab === "depth" || aiSubTab === "segmentation") && (
                  <div className="flex flex-wrap items-center justify-between gap-3 p-3 rounded-lg bg-forest-900/60 border border-emerald-500/20 font-mono text-xs">
                    <div className="flex items-center gap-2">
                      <span className="text-muted-foreground uppercase text-[11px]">ACTIVE FRAME:</span>
                      <select
                        value={selectedImageId}
                        onChange={(e) => setSelectedImageId(e.target.value)}
                        className="bg-forest-950 border border-emerald-500/30 text-emerald-300 rounded px-3 py-1 font-mono text-xs focus:outline-none focus:border-emerald-400"
                      >
                        {images.map((img, idx) => (
                          <option key={img.id} value={img.id}>
                            Frame #{idx + 1}: {img.filename}
                          </option>
                        ))}
                      </select>
                    </div>
                    <div className="text-[11px] text-muted-foreground">
                      {images.length} frame(s) connected to mission
                    </div>
                  </div>
                )}

                {(aiSubTab === "damage" || aiSubTab === "change") && (
                  <div className="flex flex-wrap items-center gap-4 p-3 rounded-lg bg-forest-900/60 border border-emerald-500/20 font-mono text-xs">
                    <div className="flex items-center gap-2">
                      <span className="text-muted-foreground uppercase text-[11px]">PRE-EVENT FRAME:</span>
                      <select
                        value={selectedImageId}
                        onChange={(e) => setSelectedImageId(e.target.value)}
                        className="bg-forest-950 border border-emerald-500/30 text-emerald-300 rounded px-2.5 py-1 text-xs"
                      >
                        {images.map((img, idx) => (
                          <option key={img.id} value={img.id}>
                            Frame #{idx + 1}: {img.filename}
                          </option>
                        ))}
                      </select>
                    </div>
                    <div className="flex items-center gap-2">
                      <span className="text-muted-foreground uppercase text-[11px]">POST-EVENT FRAME:</span>
                      <select
                        value={selectedPostImageId}
                        onChange={(e) => setSelectedPostImageId(e.target.value)}
                        className="bg-forest-950 border border-emerald-500/30 text-emerald-300 rounded px-2.5 py-1 text-xs"
                      >
                        {images.map((img, idx) => (
                          <option key={img.id} value={img.id}>
                            Frame #{idx + 1}: {img.filename}
                          </option>
                        ))}
                      </select>
                    </div>
                  </div>
                )}

                {/* AI SUB-TAB 1: DEPTH MAPS */}
                {aiSubTab === "depth" && (
                  <div className="space-y-4">
                    <div className="flex flex-wrap items-center justify-between gap-3">
                      <div className="font-mono text-xs">
                        <span className="text-sky-400 font-bold">DEPTH ANYTHING V2 SMALL:</span>
                        <span className="text-muted-foreground ml-2">
                          Relative inverse depth on {activeImage?.filename || "selected frame"}
                        </span>
                      </div>
                      <Button
                        onClick={() => triggerDepth(selectedImageId)}
                        variant="primary"
                        size="sm"
                        isLoading={activeInferencing === "depth"}
                      >
                        Run Depth Estimation
                      </Button>
                    </div>

                    {depthResult ? (
                      <div className="glass-panel p-6 rounded-xl border border-emerald-500/20 space-y-4">
                        <DepthViewer
                          originalImage={toMediaUrl(activeImage?.file_path || activeImage?.thumbnail_path)}
                          depthMapUrl={toMediaUrl(depthResult.colormap_path)}
                          minDepth={depthResult.min_depth_m}
                          maxDepth={depthResult.max_depth_m}
                          meanDepth={depthResult.mean_depth_m}
                          relativeMin={depthResult.relative_min}
                          relativeMax={depthResult.relative_max}
                          relativeMean={depthResult.relative_mean}
                          depthType={depthResult.depth_type}
                          modelLabel={depthResult.model_label}
                        />

                        <div className="p-3 rounded bg-forest-900 border border-emerald-500/15 font-mono text-xs flex flex-wrap items-center justify-between gap-4">
                          <div>RESULT ID: <span className="text-white">{depthResult.id}</span></div>
                          <div>JOB ID: <span className="text-emerald-300">{depthResult.job_id}</span></div>
                          {depthResult.mesh_obj_path && (
                            <div>SURFACE MESH: <span className="text-sky-300">{depthResult.mesh_obj_path}</span></div>
                          )}
                        </div>
                      </div>
                    ) : (
                      <div className="glass-panel p-8 rounded-xl border border-dashed border-emerald-500/20 text-center flex flex-col items-center justify-center gap-3">
                        {activeImage?.file_path && (
                          <div className="w-full max-w-lg aspect-video rounded-lg overflow-hidden border border-emerald-500/30 relative mb-2">
                            <img
                              src={toMediaUrl(activeImage.file_path)}
                              alt={activeImage.filename}
                              className="w-full h-full object-cover"
                            />
                            <div className="absolute inset-0 bg-black/40 flex items-center justify-center">
                              <span className="font-mono text-xs bg-forest-950/90 text-sky-300 border border-emerald-500/30 px-3 py-1.5 rounded">
                                Selected Frame: {activeImage.filename}
                              </span>
                            </div>
                          </div>
                        )}
                        <p className="text-sm font-mono text-muted-foreground">
                          Depth map not yet computed for this frame. Run Depth Anything V2 Small neural estimation to compute relative inverse depth and 3D reliefs.
                        </p>
                        <Button
                          onClick={() => triggerDepth(selectedImageId)}
                          variant="primary"
                          size="sm"
                          isLoading={activeInferencing === "depth"}
                        >
                          <Sparkles className="w-3.5 h-3.5 mr-1" /> Run Depth Estimation
                        </Button>
                      </div>
                    )}
                  </div>
                )}

                {/* AI SUB-TAB 2: SEGMENTATION */}
                {aiSubTab === "segmentation" && (
                  <div className="space-y-4">
                    <div className="flex flex-wrap items-center justify-between gap-3">
                      <div className="font-mono text-xs">
                        <span className="text-emerald-400 font-bold">AERIAL LAND-COVER SEGMENTATION:</span>
                        <span className="text-muted-foreground ml-2">
                          7-class aerial categorization on {activeImage?.filename || "selected frame"}
                        </span>
                      </div>
                      <Button
                        onClick={() => triggerSegmentation(selectedImageId)}
                        variant="primary"
                        size="sm"
                        isLoading={activeInferencing === "segmentation"}
                      >
                        Run Segmentation
                      </Button>
                    </div>

                    {segmentationResult ? (
                      <div className="glass-panel p-6 rounded-xl border border-emerald-500/20 space-y-4">
                        <SegmentationOverlay
                          originalImage={toMediaUrl(activeImage?.file_path || activeImage?.thumbnail_path)}
                          overlayImage={toMediaUrl(segmentationResult.overlay_path)}
                          classes={
                            segmentationResult.class_distribution
                              ? Object.entries(segmentationResult.class_distribution).map(([cls, pct]) => ({
                                  id: cls,
                                  label: cls.charAt(0).toUpperCase() + cls.slice(1),
                                  color:
                                    cls === "building"
                                      ? "#ec4899"
                                      : cls === "vegetation" || cls === "forest"
                                      ? "#10b981"
                                      : cls === "road"
                                      ? "#3b82f6"
                                      : cls === "water"
                                      ? "#06b6d4"
                                      : cls === "barren" || cls === "soil"
                                      ? "#f59e0b"
                                      : cls === "agricultural"
                                      ? "#84cc16"
                                      : cls === "vehicle"
                                      ? "#ef4444"
                                      : "#94a3b8",
                                  percentage: Number(pct),
                                }))
                              : undefined
                          }
                        />

                        <div className="flex items-center justify-between pt-2 font-mono text-xs text-muted-foreground">
                          <span>VECTOR GEODATA: {segmentationResult.geojson_path || "Building footprints vectorized"}</span>
                          {segmentationResult.geojson_path && (
                            <a
                              href={toMediaUrl(segmentationResult.geojson_path)}
                              download
                              className="text-emerald-400 hover:underline flex items-center gap-1 font-bold"
                            >
                              <Download className="w-3.5 h-3.5" /> Download GeoJSON
                            </a>
                          )}
                        </div>
                      </div>
                    ) : (
                      <div className="glass-panel p-8 rounded-xl border border-dashed border-emerald-500/20 text-center flex flex-col items-center justify-center gap-3">
                        {activeImage?.file_path && (
                          <div className="w-full max-w-lg aspect-video rounded-lg overflow-hidden border border-emerald-500/30 relative mb-2">
                            <img
                              src={toMediaUrl(activeImage.file_path)}
                              alt={activeImage.filename}
                              className="w-full h-full object-cover"
                            />
                            <div className="absolute inset-0 bg-black/40 flex items-center justify-center">
                              <span className="font-mono text-xs bg-forest-950/90 text-emerald-300 border border-emerald-500/30 px-3 py-1.5 rounded">
                                Target Frame: {activeImage.filename}
                              </span>
                            </div>
                          </div>
                        )}
                        <p className="text-sm font-mono text-muted-foreground">
                          No segmentation performed yet for this frame. Run LoveDA 7-class semantic analysis to extract terrain, structures, and roads.
                        </p>
                        <Button
                          onClick={() => triggerSegmentation(selectedImageId)}
                          variant="primary"
                          size="sm"
                          isLoading={activeInferencing === "segmentation"}
                        >
                          <Sparkles className="w-3.5 h-3.5 mr-1" /> Run Land-Cover Segmentation
                        </Button>
                      </div>
                    )}
                  </div>
                )}

                {/* AI SUB-TAB 3: DAMAGE ASSESSMENT */}
                {aiSubTab === "damage" && (
                  <div className="space-y-4">
                    <div className="flex flex-wrap items-center justify-between gap-3">
                      <div className="font-mono text-xs">
                        <span className="text-rose-400 font-bold">xBD DISASTER TRIAGE:</span>
                        <span className="text-muted-foreground ml-2">4-tier structural collapse classification</span>
                      </div>
                      <div className="flex items-center gap-2">
                        {damageResult && (
                          <div className="flex items-center rounded-lg border border-emerald-500/30 bg-forest-950 p-0.5 text-xs font-mono">
                            <button
                              onClick={() => setDamageViewMode("overlay")}
                              className={`px-2.5 py-1 rounded transition-colors ${
                                damageViewMode === "overlay"
                                  ? "bg-rose-500/20 text-rose-300 font-bold"
                                  : "text-muted-foreground hover:text-white"
                              }`}
                            >
                              Triage Overlay
                            </button>
                            <button
                              onClick={() => setDamageViewMode("slider")}
                              className={`px-2.5 py-1 rounded transition-colors ${
                                damageViewMode === "slider"
                                  ? "bg-rose-500/20 text-rose-300 font-bold"
                                  : "text-muted-foreground hover:text-white"
                              }`}
                            >
                              Pre/Post Slider
                            </button>
                          </div>
                        )}
                        <Button
                          onClick={() => triggerDamage(selectedImageId, selectedPostImageId)}
                          variant="primary"
                          size="sm"
                          isLoading={activeInferencing === "damage"}
                        >
                          Run Damage Evaluation
                        </Button>
                      </div>
                    </div>

                    {damageResult ? (
                      <div className="glass-panel p-6 rounded-xl border border-emerald-500/20 space-y-4">
                        {damageViewMode === "overlay" ? (
                          <div className="relative rounded-lg overflow-hidden border border-rose-500/30 aspect-video bg-black flex items-center justify-center">
                            <img
                              src={toMediaUrl(damageResult.damage_overlay_path || activePostImage?.file_path)}
                              alt="xBD Damage Classification Overlay"
                              className="w-full h-full object-cover"
                            />
                            <div className="absolute top-3 left-3 bg-forest-950/90 border border-rose-500/40 rounded px-2.5 py-1 font-mono text-[11px] text-rose-300 flex items-center gap-1.5">
                              <span className="h-2 w-2 rounded-full bg-rose-500 animate-pulse" />
                              xBD Structural Triage Overlay
                            </div>
                          </div>
                        ) : (
                          <BeforeAfterSlider
                            beforeImage={toMediaUrl(activeImage?.file_path || activeImage?.thumbnail_path)}
                            afterImage={toMediaUrl(damageResult.damage_overlay_path || activePostImage?.file_path)}
                            beforeLabel="Pre-Disaster Baseline"
                            afterLabel="Damage Assessment Overlay"
                          />
                        )}

                        {damageResult.counts_by_level && (
                          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 font-mono text-xs">
                            <div className="p-3 rounded bg-forest-900 border border-emerald-500/20">
                              <div className="text-[10px] text-muted-foreground">NO DAMAGE</div>
                              <div className="text-emerald-400 font-bold text-base mt-0.5">
                                {damageResult.counts_by_level.no_damage} Buildings
                              </div>
                            </div>
                            <div className="p-3 rounded bg-forest-900 border border-emerald-500/20">
                              <div className="text-[10px] text-muted-foreground">MINOR DAMAGE</div>
                              <div className="text-amber-300 font-bold text-base mt-0.5">
                                {damageResult.counts_by_level.minor_damage} Buildings
                              </div>
                            </div>
                            <div className="p-3 rounded bg-forest-900 border border-emerald-500/20">
                              <div className="text-[10px] text-muted-foreground">MAJOR DAMAGE</div>
                              <div className="text-orange-400 font-bold text-base mt-0.5">
                                {damageResult.counts_by_level.major_damage} Buildings
                              </div>
                            </div>
                            <div className="p-3 rounded bg-forest-900 border border-emerald-500/20">
                              <div className="text-[10px] text-muted-foreground">DESTROYED</div>
                              <div className="text-rose-400 font-bold text-base mt-0.5">
                                {damageResult.counts_by_level.destroyed} Buildings
                              </div>
                            </div>
                          </div>
                        )}

                        <div className="p-3 rounded bg-forest-900/90 border border-emerald-500/15 font-mono text-xs flex flex-wrap items-center justify-between gap-2">
                          <span className="text-muted-foreground">COMPOSITE SEVERITY INDEX:</span>
                          <span className="text-rose-400 font-bold">
                            {damageResult.severity_index} ({damageResult.damage_percentage}% altered) · {damageResult.total_buildings || 0} Total Buildings Assessed
                          </span>
                        </div>
                      </div>
                    ) : (
                      <div className="glass-panel p-8 rounded-xl border border-dashed border-emerald-500/20 text-center flex flex-col items-center justify-center gap-3">
                        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 w-full max-w-xl mb-2">
                          {activeImage?.file_path && (
                            <div className="aspect-video rounded-lg overflow-hidden border border-emerald-500/30 relative">
                              <img
                                src={toMediaUrl(activeImage.file_path)}
                                alt={activeImage.filename}
                                className="w-full h-full object-cover"
                              />
                              <div className="absolute inset-0 bg-black/40 flex items-center justify-center">
                                <span className="font-mono text-[10px] bg-forest-950/90 text-emerald-300 border border-emerald-500/30 px-2 py-1 rounded">
                                  Pre: {activeImage.filename}
                                </span>
                              </div>
                            </div>
                          )}
                          {activePostImage?.file_path && (
                            <div className="aspect-video rounded-lg overflow-hidden border border-emerald-500/30 relative">
                              <img
                                src={toMediaUrl(activePostImage.file_path)}
                                alt={activePostImage.filename}
                                className="w-full h-full object-cover"
                              />
                              <div className="absolute inset-0 bg-black/40 flex items-center justify-center">
                                <span className="font-mono text-[10px] bg-forest-950/90 text-rose-300 border border-rose-500/30 px-2 py-1 rounded">
                                  Post: {activePostImage.filename}
                                </span>
                              </div>
                            </div>
                          )}
                        </div>
                        <p className="text-sm font-mono text-muted-foreground">
                          Damage evaluation has not yet been computed for this frame pair. Run the xBD Siamese model to classify building structural collapse into 4 severity levels.
                        </p>
                        <Button
                          onClick={() => triggerDamage(selectedImageId, selectedPostImageId)}
                          variant="primary"
                          size="sm"
                          isLoading={activeInferencing === "damage"}
                        >
                          <ShieldAlert className="w-3.5 h-3.5 mr-1" /> Run Damage Evaluation
                        </Button>
                      </div>
                    )}
                  </div>
                )}

                {/* AI SUB-TAB 4: CHANGE DETECTION */}
                {aiSubTab === "change" && (
                  <div className="space-y-4">
                    <div className="flex flex-wrap items-center justify-between gap-3">
                      <div className="font-mono text-xs">
                        <span className="text-amber-400 font-bold">BI-TEMPORAL DIFFERENCING:</span>
                        <span className="text-muted-foreground ml-2">Photometric and structural shift heatmap</span>
                      </div>
                      <div className="flex items-center gap-2">
                        {changeResult && (
                          <div className="flex items-center rounded-lg border border-emerald-500/30 bg-forest-950 p-0.5 text-xs font-mono">
                            <button
                              onClick={() => setChangeViewMode("heatmap")}
                              className={`px-2.5 py-1 rounded transition-colors ${
                                changeViewMode === "heatmap"
                                  ? "bg-amber-500/20 text-amber-300 font-bold"
                                  : "text-muted-foreground hover:text-white"
                              }`}
                            >
                              Heatmap
                            </button>
                            <button
                              onClick={() => setChangeViewMode("mask")}
                              className={`px-2.5 py-1 rounded transition-colors ${
                                changeViewMode === "mask"
                                  ? "bg-amber-500/20 text-amber-300 font-bold"
                                  : "text-muted-foreground hover:text-white"
                              }`}
                            >
                              Diff Mask
                            </button>
                            <button
                              onClick={() => setChangeViewMode("slider")}
                              className={`px-2.5 py-1 rounded transition-colors ${
                                changeViewMode === "slider"
                                  ? "bg-amber-500/20 text-amber-300 font-bold"
                                  : "text-muted-foreground hover:text-white"
                              }`}
                            >
                              Pre vs Post
                            </button>
                          </div>
                        )}
                        <Button
                          onClick={() => triggerChange(selectedImageId, selectedPostImageId)}
                          variant="primary"
                          size="sm"
                          isLoading={activeInferencing === "change"}
                        >
                          Run Change Differencing
                        </Button>
                      </div>
                    </div>

                    {changeResult ? (
                      <div className="glass-panel p-6 rounded-xl border border-emerald-500/20 space-y-4">
                        {changeViewMode === "heatmap" ? (
                          <BeforeAfterSlider
                            beforeImage={toMediaUrl(activeImage?.file_path || activeImage?.thumbnail_path)}
                            afterImage={toMediaUrl(changeResult.heatmap_path)}
                            beforeLabel="Pre-Event Baseline"
                            afterLabel="Change Intensity Heatmap"
                          />
                        ) : changeViewMode === "mask" ? (
                          <BeforeAfterSlider
                            beforeImage={toMediaUrl(activeImage?.file_path || activeImage?.thumbnail_path)}
                            afterImage={toMediaUrl(changeResult.diff_mask_path || changeResult.heatmap_path)}
                            beforeLabel="Pre-Event Baseline"
                            afterLabel="Binary Differencing Mask"
                          />
                        ) : (
                          <BeforeAfterSlider
                            beforeImage={toMediaUrl(activeImage?.file_path || activeImage?.thumbnail_path)}
                            afterImage={toMediaUrl(activePostImage?.file_path || activePostImage?.thumbnail_path)}
                            beforeLabel="Pre-Disaster (T0)"
                            afterLabel="Post-Disaster (T1)"
                          />
                        )}

                        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 font-mono text-xs">
                          <div className="p-3 rounded bg-forest-900 border border-emerald-500/20">
                            <div className="text-[10px] text-muted-foreground">CHANGED AREA</div>
                            <div className="text-amber-400 font-bold text-base mt-0.5">
                              {changeResult.changed_area_pct}%
                            </div>
                          </div>
                          <div className="p-3 rounded bg-forest-900 border border-emerald-500/20">
                            <div className="text-[10px] text-muted-foreground">CHANGED PIXELS</div>
                            <div className="text-white font-bold text-base mt-0.5">
                              {changeResult.changed_pixels?.toLocaleString() || "0"} px
                            </div>
                          </div>
                          <div className="p-3 rounded bg-forest-900 border border-emerald-500/20">
                            <div className="text-[10px] text-muted-foreground">SHIFT SIGNIFICANCE</div>
                            <div className="text-emerald-400 font-bold text-base mt-0.5">
                              {(changeResult.significance_score * 100).toFixed(1)}%
                            </div>
                          </div>
                          <div className="p-3 rounded bg-forest-900 border border-emerald-500/20">
                            <div className="text-[10px] text-muted-foreground">DETECTED CLUSTERS</div>
                            <div className="text-sky-300 font-bold text-base mt-0.5">
                              {changeResult.detected_regions_count || 1} Regions
                            </div>
                          </div>
                        </div>

                        <div className="p-3 rounded bg-forest-900/90 border border-emerald-500/15 font-mono text-xs flex justify-between">
                          <span className="text-muted-foreground">HEATMAP ARTIFACT:</span>
                          <span className="text-amber-300 truncate max-w-[400px]">
                            {changeResult.heatmap_path}
                          </span>
                        </div>
                      </div>
                    ) : (
                      <div className="glass-panel p-8 rounded-xl border border-dashed border-emerald-500/20 text-center flex flex-col items-center justify-center gap-3">
                        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 w-full max-w-xl mb-2">
                          {activeImage?.file_path && (
                            <div className="aspect-video rounded-lg overflow-hidden border border-emerald-500/30 relative">
                              <img
                                src={toMediaUrl(activeImage.file_path)}
                                alt={activeImage.filename}
                                className="w-full h-full object-cover"
                              />
                              <div className="absolute inset-0 bg-black/40 flex items-center justify-center">
                                <span className="font-mono text-[10px] bg-forest-950/90 text-emerald-300 border border-emerald-500/30 px-2 py-1 rounded">
                                  T0 Baseline: {activeImage.filename}
                                </span>
                              </div>
                            </div>
                          )}
                          {activePostImage?.file_path && (
                            <div className="aspect-video rounded-lg overflow-hidden border border-emerald-500/30 relative">
                              <img
                                src={toMediaUrl(activePostImage.file_path)}
                                alt={activePostImage.filename}
                                className="w-full h-full object-cover"
                              />
                              <div className="absolute inset-0 bg-black/40 flex items-center justify-center">
                                <span className="font-mono text-[10px] bg-forest-950/90 text-amber-300 border border-amber-500/30 px-2 py-1 rounded">
                                  T1 Comparison: {activePostImage.filename}
                                </span>
                              </div>
                            </div>
                          )}
                        </div>
                        <p className="text-sm font-mono text-muted-foreground">
                          Bi-temporal change differencing not yet computed. Run pixel differencing to detect structural shifts and terrain disruption.
                        </p>
                        <Button
                          onClick={() => triggerChange(selectedImageId, selectedPostImageId)}
                          variant="primary"
                          size="sm"
                          isLoading={activeInferencing === "change"}
                        >
                          <GitCompare className="w-3.5 h-3.5 mr-1" /> Run Change Differencing
                        </Button>
                      </div>
                    )}
                  </div>
                )}
              </>
            )}
          </div>
        )}

        {/* ============================================================== */}
        {/* TAB 5: 3D POINT CLOUD VIEWER */}
        {/* ============================================================== */}
        {activeTab === "viewer3d" && (
          <div className="flex flex-col gap-6">
            <div className="flex items-center justify-between">
              <div>
                <h2 className="text-xl font-bold text-white font-mono">3D Point Cloud Viewer</h2>
                <p className="text-xs text-muted-foreground">
                  Inspect reconstructed 3D assets and exported PLY geometry.
                </p>
              </div>
              <Button onClick={trigger3D} variant="primary" size="sm" isLoading={activeInferencing === "3d"}>
                <Sparkles className="w-4 h-4 mr-1" /> Reconstruct 3D
              </Button>
            </div>

            <Card className="glass-panel border-emerald-500/25">
              <CardHeader className="p-4 border-b border-emerald-500/15">
                <CardTitle className="text-sm font-bold font-mono flex items-center gap-2">
                  <Box className="w-4 h-4 text-emerald-400" />
                  PRIMARY 3D SPATIAL SURFACE // {currentProject?.name}
                </CardTitle>
                <CardDescription className="text-xs">
                  Multi-view dense photogrammetric point cloud and digital elevation surface.
                </CardDescription>
              </CardHeader>
              <CardContent className="p-4">
                <AdvancedSpatialViewer3D
                  projectName={currentProject?.name}
                  locationName={currentProject?.location_name}
                  plyUrl={toMediaUrl(reconResult?.pointcloud_ply_path)}
                />
              </CardContent>
            </Card>

            {reconResult &&
              <div className="glass-panel p-4 rounded-xl border border-emerald-500/20 font-mono text-xs">
                <h4 className="text-white font-bold mb-2">Reconstruction summary</h4>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  <div>
                    <span className="text-muted-foreground">Points:</span>{" "}
                    <span className="text-white">{reconResult.num_points.toLocaleString()}</span>
                  </div>
                  <div>
                    <span className="text-muted-foreground">PLY:</span>{" "}
                    <span className="text-emerald-300 break-all">{reconResult.pointcloud_ply_path}</span>
                  </div>
                  <div>
                    <span className="text-muted-foreground">OBJ:</span>{" "}
                    <span className="text-emerald-300 break-all">{reconResult.mesh_obj_path}</span>
                  </div>
                </div>
              </div>
            }

            {analysisError &&
              <div className="p-4 rounded bg-rose-950/60 border border-rose-500/40 text-rose-300 text-xs font-mono">
                <AlertTriangle className="w-4 h-4 inline mr-2" />
                {analysisError}
              </div>
            }
          </div>
        )}

        {/* ============================================================== */}
        {/* TAB 6: JOB HISTORY */}
        {/* ============================================================== */}
        {activeTab === "jobs" && (
          <div className="flex flex-col gap-6">
            <div className="flex items-center justify-between">
              <div>
                <h2 className="text-xl font-bold text-white font-mono">Job History</h2>
                <p className="text-xs text-muted-foreground">
                  Recent analysis and processing jobs for the active mission.
                </p>
              </div>
              <Button variant="tactical" size="sm">
                <RefreshCw className="w-3.5 h-3.5 mr-1" /> Refresh
              </Button>
            </div>

            <Card className="glass-panel border-emerald-500/20">
              <CardHeader className="p-4 border-b border-emerald-500/15">
                <CardTitle className="text-sm font-bold font-mono">Jobs for {currentProject?.name}</CardTitle>
              </CardHeader>
              <CardContent className="p-4">
                {jobs.length === 0 ? (
                  <div className="text-muted-foreground text-xs">
                    No jobs recorded for this mission yet.
                  </div>
                ) : (
                  <table className="w-full text-xs font-mono text-left">
                    <thead className="text-muted-foreground uppercase border-b border-emerald-500/15">
                      <tr>
                        <th className="py-2 pr-4">ID</th>
                        <th className="py-2 pr-4">Type</th>
                        <th className="py-2 pr-4">Status</th>
                        <th className="py-2">Created</th>
                      </tr>
                    </thead>
                    <tbody>
                      {jobs.map((job) => (
                        <tr key={job.id} className="border-b border-emerald-500/10">
                          <td className="py-2 pr-4 text-emerald-300">{job.id}</td>
                          <td className="py-2 pr-4">{job.job_type}</td>
                          <td className="py-2 pr-4">
                            <Badge variant={job.status === "completed" ? "success" : "warning"}>
                              {job.status}
                            </Badge>
                          </td>
                          <td className="py-2 text-muted-foreground">
                            {new Date(job.created_at).toLocaleString()}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                )}
              </CardContent>
            </Card>
          </div>
        )}

        {/* ============================================================== */}
        {/* TAB 7: MODEL INFORMATION */}
        {/* ============================================================== */}
        {activeTab === "models" && (
          <div className="flex flex-col gap-6">
            <div className="flex items-center justify-between">
              <div>
                <h2 className="text-xl font-bold text-white font-mono">Model Information</h2>
                <p className="text-xs text-muted-foreground">
                  Trained model versions and inference backend details.
                </p>
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <Card className="glass-panel border-emerald-500/20">
                <CardHeader className="p-4 border-b border-emerald-500/15">
                  <CardTitle className="text-sm font-bold font-mono">Depth Model</CardTitle>
                </CardHeader>
                <CardContent className="p-4 font-mono text-xs space-y-2">
                  <div>Model: <span className="text-white">Depth Anything V2 Small</span></div>
                  <div>Purpose: Relative monocular depth estimation</div>
                  <div>Metric: Relative only (no absolute scale unless calibrated)</div>
                </CardContent>
              </Card>

              <Card className="glass-panel border-emerald-500/20">
                <CardHeader className="p-4 border-b border-emerald-500/15">
                  <CardTitle className="text-sm font-bold font-mono">Segmentation Model</CardTitle>
                </CardHeader>
                <CardContent className="p-4 font-mono text-xs space-y-2">
                  <div>Model: <span className="text-white">Aerial land-cover segmenter</span></div>
                  <div>Purpose: 7-class land-cover categorization</div>
                  <div>Requires: Verified checkpoint for authoritative results</div>
                </CardContent>
              </Card>
            </div>
          </div>
        )}

        {/* ============================================================== */}
        {/* TAB 8: SETTINGS */}
        {/* ============================================================== */}
        {activeTab === "settings" && (
          <div className="flex flex-col gap-6">
            <div className="flex items-center justify-between">
              <div>
                <h2 className="text-xl font-bold text-white font-mono">Settings</h2>
                <p className="text-xs text-muted-foreground">
                  API configuration and environment preferences.
                </p>
              </div>
            </div>

            <Card className="glass-panel border-emerald-500/20">
              <CardHeader className="p-4 border-b border-emerald-500/15">
                <CardTitle className="text-sm font-bold font-mono">Environment</CardTitle>
              </CardHeader>
              <CardContent className="p-4 font-mono text-xs space-y-3">
                <div>API endpoint: <span className="text-emerald-300">{settingsState.apiEndpoint}</span></div>
                <div>CRS: <span className="text-white">{settingsState.crs}</span></div>
                <div>Auto-refresh: <span className="text-white">{String(settingsState.autoRefresh)}</span></div>
                <div>Export format: <span className="text-white">{settingsState.exportFormat}</span></div>
              </CardContent>
            </Card>
          </div>
        )}
      </div>

      {/* CREATE MISSION MODAL */}
      {showCreateModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm">
          <div className="glass-panel w-full max-w-lg p-6 rounded-xl border border-emerald-500/40 shadow-2xl relative font-mono text-xs">
            <div className="flex items-center justify-between mb-4 border-b border-emerald-500/20 pb-3">
              <div>
                <h3 className="text-base font-bold text-white flex items-center gap-2">
                  <Plus className="w-4 h-4 text-emerald-400" /> Initialize New Aerial Mission
                </h3>
                <p className="text-muted-foreground text-[11px] mt-0.5">
                  Register survey coordinates and mission metadata.
                </p>
              </div>
              <button
                type="button"
                onClick={() => setShowCreateModal(false)}
                className="p-1 rounded text-muted-foreground hover:text-white"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            <form onSubmit={handleCreateProject} className="space-y-4">
              <div>
                <label className="text-white block mb-1 font-semibold">Mission Name *</label>
                <input
                  type="text"
                  required
                  placeholder="e.g. Coastal Survey Delta"
                  value={newProject.name}
                  onChange={(e) => setNewProject({ ...newProject, name: e.target.value })}
                  className="w-full bg-forest-950 border border-emerald-500/30 rounded p-2.5 text-white focus:outline-none focus:border-emerald-400"
                />
              </div>

              <div>
                <label className="text-white block mb-1 font-semibold">Location / Sector *</label>
                <input
                  type="text"
                  required
                  placeholder="e.g. Paradip Port Coastline"
                  value={newProject.location_name}
                  onChange={(e) => setNewProject({ ...newProject, location_name: e.target.value })}
                  className="w-full bg-forest-950 border border-emerald-500/30 rounded p-2.5 text-white focus:outline-none focus:border-emerald-400"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="text-white block mb-1 font-semibold">Center Latitude</label>
                  <input
                    type="number"
                    step="any"
                    value={newProject.center_lat}
                    onChange={(e) =>
                      setNewProject({ ...newProject, center_lat: parseFloat(e.target.value) || 0 })
                    }
                    className="w-full bg-forest-950 border border-emerald-500/30 rounded p-2.5 text-white focus:outline-none focus:border-emerald-400"
                  />
                </div>
                <div>
                  <label className="text-white block mb-1 font-semibold">Center Longitude</label>
                  <input
                    type="number"
                    step="any"
                    value={newProject.center_lon}
                    onChange={(e) =>
                      setNewProject({ ...newProject, center_lon: parseFloat(e.target.value) || 0 })
                    }
                    className="w-full bg-forest-950 border border-emerald-500/30 rounded p-2.5 text-white focus:outline-none focus:border-emerald-400"
                  />
                </div>
              </div>

              <div>
                <label className="text-white block mb-1 font-semibold">Mission Description</label>
                <textarea
                  rows={2}
                  placeholder="Survey objectives, flight law, camera sensor details..."
                  value={newProject.description}
                  onChange={(e) => setNewProject({ ...newProject, description: e.target.value })}
                  className="w-full bg-forest-950 border border-emerald-500/30 rounded p-2.5 text-white focus:outline-none focus:border-emerald-400"
                />
              </div>

              <div className="pt-3 flex items-center justify-end gap-2 border-t border-emerald-500/20">
                <Button
                  type="button"
                  variant="outline"
                  size="sm"
                  onClick={() => setShowCreateModal(false)}
                >
                  Cancel
                </Button>
                <Button type="submit" variant="primary" size="sm">
                  Create Mission
                </Button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}

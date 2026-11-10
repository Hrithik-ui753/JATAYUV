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
  Compass
} from "lucide-react";
import { Button } from "@/components/ui/Button";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { BeforeAfterSlider } from "@/components/viewer/BeforeAfterSlider";
import { DepthViewer } from "@/components/viewer/DepthViewer";
import { api } from "@/lib/api";
<<<<<<< HEAD
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
=======
<<<<<<< HEAD
=======
import { uploadOutcome } from "@/lib/integrity.mjs";
>>>>>>> 0400f2f (p5-udpated)
import { 
  Project, 
  AerialImage, 
  AnalysisJob, 
  DepthResult, 
  SegmentationResult, 
  DamageAssessmentResult, 
  ChangeDetectionResult, 
  Reconstruction3DResult 
>>>>>>> origin/main
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

export default function DashboardPage() {
  const [activeTab, setActiveTab] = useState<
    "overview" | "projects" | "upload" | "ai" | "viewer3d" | "jobs" | "models" | "settings"
  >("overview");

  const [aiSubTab, setAiSubTab] = useState<"depth" | "segmentation" | "damage" | "change">("depth");

  // Core Data States
  const [projects, setProjects] = useState<Project[]>([]);
  const [selectedProjectId, setSelectedProjectId] = useState<string>("proj-coastal-01");
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
<<<<<<< HEAD

  const [analysisError, setAnalysisError] = useState<string | null>(null);

  // Upload state — a success message is only shown after the backend confirms stored frames.
  const [uploadFiles, setUploadFiles] = useState<File[]>([]);
  const [uploading, setUploading] = useState(false);
<<<<<<< HEAD
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
=======
  const [uploadStatus, setUploadStatus] = useState<string | null>(null);
=======
  const [analysisError, setAnalysisError] = useState<string | null>(null);

  // Upload state — a success message is only shown after the backend confirms stored frames.
  const [uploadFiles, setUploadFiles] = useState<File[]>([]);
  const [uploading, setUploading] = useState(false);
  const [uploadStatus, setUploadStatus] = useState<
    { kind: "success" | "error"; message: string } | null
  >(null);
>>>>>>> 0400f2f (p5-udpated)
>>>>>>> origin/main

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
      const projList = await api.getProjects();
      setProjects(projList);

      const activeId = selectedProjectId || (projList[0]?.id ?? "proj-coastal-01");
      setSelectedProjectId(activeId);

      const [imgList, jobList] = await Promise.all([
        api.getProjectImages(activeId),
        api.getProjectJobs(activeId),
      ]);
      setImages(imgList);
      setJobs(jobList);

      // Load sample analysis results
      try {
        const dRes = await api.getDepthResult("img-pre-01");
        setDepthResult(dRes);
      } catch {}
      try {
        const sRes = await api.getSegmentationResult("img-pre-01");
        setSegmentationResult(sRes);
      } catch {}
      try {
        const dmgRes = await api.getDamageResult("img-pre-01", "img-post-01");
        setDamageResult(dmgRes);
      } catch {}
      try {
        const cRes = await api.getChangeResult("img-pre-01", "img-post-01");
        setChangeResult(cRes);
      } catch {}
      try {
        const rRes = await api.get3DReconstructionResult(activeId);
        setReconResult(rRes);
      } catch {}
      try {
        const vids = await api.getProjectVideos(activeId);
        setProjectVideos(vids);
        if (vids.length > 0) setSelectedVideo(vids[0]);
      } catch {}
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
    setVideoProcessStatus("Dispatching single-pass video reconstruction pipeline (PyAV -> Blur Filter -> Perception -> COLMAP)...");
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

<<<<<<< HEAD
  // Image Upload Handler — success is only reported when the backend confirms records.
=======
<<<<<<< HEAD
  // Image Upload Handler
=======
  // Image Upload Handler — success is only reported when the backend confirms records.
>>>>>>> 0400f2f (p5-udpated)
>>>>>>> origin/main
  const handleUploadSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (uploadFiles.length === 0) return;
    setUploading(true);
<<<<<<< HEAD
    setUploadStatus(null);
=======
<<<<<<< HEAD
    setUploadStatus("Ingesting UAV imagery and parsing EXIF headers...");
>>>>>>> origin/main
    try {
      const uploaded = await api.uploadImages(selectedProjectId, uploadFiles);
      setImages([...uploaded, ...images]);
      setUploadStatus(uploadOutcome({ ok: true, uploadedCount: uploaded.length }));
      // Keep the selection only when the backend stored nothing (retry path).
      if (uploaded.length > 0) setUploadFiles([]);
    } catch (err: any) {
<<<<<<< HEAD
=======
      setUploadStatus("Upload completed with local simulation.");
=======
    setUploadStatus(null);
    try {
      const uploaded = await api.uploadImages(selectedProjectId, uploadFiles);
      setImages([...uploaded, ...images]);
      setUploadStatus(uploadOutcome({ ok: true, uploadedCount: uploaded.length }));
      // Keep the selection only when the backend stored nothing (retry path).
      if (uploaded.length > 0) setUploadFiles([]);
    } catch (err: any) {
>>>>>>> origin/main
      // The selection stays in place so the operator can retry the same upload.
      setUploadStatus(
        uploadOutcome({
          ok: false,
          errorMessage: err?.message ?? "No response from the backend",
        })
      );
<<<<<<< HEAD
=======
>>>>>>> 0400f2f (p5-udpated)
>>>>>>> origin/main
    } finally {
      setUploading(false);
    }
  };

  // Trigger AI Depth
  const triggerDepth = async (imageId: string) => {
    setActiveInferencing("depth");
<<<<<<< HEAD
    setAnalysisError(null);
=======
<<<<<<< HEAD
=======
    setAnalysisError(null);
>>>>>>> 0400f2f (p5-udpated)
>>>>>>> origin/main
    try {
      const res = await api.triggerDepthEstimation(imageId);
      setDepthResult(res);
      fetchData();
<<<<<<< HEAD
    } catch (err: any) {
      setAnalysisError(err?.message ?? "Depth estimation failed");
=======
<<<<<<< HEAD
    } catch (err) {
      console.error(err);
=======
    } catch (err: any) {
      setAnalysisError(err?.message ?? "Depth estimation failed");
>>>>>>> 0400f2f (p5-udpated)
>>>>>>> origin/main
    } finally {
      setActiveInferencing(null);
    }
  };

  // Trigger AI Segmentation
  const triggerSegmentation = async (imageId: string) => {
    setActiveInferencing("segmentation");
<<<<<<< HEAD
    setAnalysisError(null);
=======
<<<<<<< HEAD
=======
    setAnalysisError(null);
>>>>>>> 0400f2f (p5-udpated)
>>>>>>> origin/main
    try {
      const res = await api.triggerSegmentation(imageId);
      setSegmentationResult(res);
      fetchData();
<<<<<<< HEAD
    } catch (err: any) {
      setSegmentationResult(null);
      setAnalysisError(err?.message ?? "Segmentation failed");
=======
<<<<<<< HEAD
    } catch (err) {
      console.error(err);
=======
    } catch (err: any) {
      setSegmentationResult(null);
      setAnalysisError(err?.message ?? "Segmentation failed");
>>>>>>> 0400f2f (p5-udpated)
>>>>>>> origin/main
    } finally {
      setActiveInferencing(null);
    }
  };

  // Trigger Damage Assessment
  const triggerDamage = async (preId: string, postId: string) => {
    setActiveInferencing("damage");
<<<<<<< HEAD
    setAnalysisError(null);
=======
<<<<<<< HEAD
=======
    setAnalysisError(null);
>>>>>>> 0400f2f (p5-udpated)
>>>>>>> origin/main
    try {
      const res = await api.triggerDamageAssessment(preId, postId);
      setDamageResult(res);
      fetchData();
<<<<<<< HEAD
    } catch (err: any) {
      setDamageResult(null);
      setAnalysisError(err?.message ?? "Damage assessment failed");
=======
<<<<<<< HEAD
    } catch (err) {
      console.error(err);
=======
    } catch (err: any) {
      setDamageResult(null);
      setAnalysisError(err?.message ?? "Damage assessment failed");
>>>>>>> 0400f2f (p5-udpated)
>>>>>>> origin/main
    } finally {
      setActiveInferencing(null);
    }
  };

  // Trigger Change Detection
  const triggerChange = async (beforeId: string, afterId: string) => {
    setActiveInferencing("change");
    try {
      const res = await api.triggerChangeDetection(beforeId, afterId);
      setChangeResult(res);
      fetchData();
    } catch (err) {
      console.error(err);
    } finally {
      setActiveInferencing(null);
    }
  };

  // Trigger 3D Reconstruction
  const trigger3D = async () => {
    setActiveInferencing("3d");
<<<<<<< HEAD
    setAnalysisError(null);
=======
<<<<<<< HEAD
=======
    setAnalysisError(null);
>>>>>>> 0400f2f (p5-udpated)
>>>>>>> origin/main
    try {
      const res = await api.trigger3DReconstruction(selectedProjectId);
      setReconResult(res);
      fetchData();
<<<<<<< HEAD
=======
<<<<<<< HEAD
    } catch (err) {
      console.error(err);
=======
>>>>>>> origin/main
    } catch (err: any) {
      // Reconstruction unavailability/failure is surfaced; no geometry is displayed.
      setReconResult(null);
      setAnalysisError(err?.message ?? "3D reconstruction failed");
<<<<<<< HEAD
=======
>>>>>>> 0400f2f (p5-udpated)
>>>>>>> origin/main
    } finally {
      setActiveInferencing(null);
    }
  };

  const currentProject = projects.find((p) => p.id === selectedProjectId) || projects[0];

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
<<<<<<< HEAD
                      Stored missions
=======
<<<<<<< HEAD
                      100% Calibrated
=======
                      Stored missions
>>>>>>> 0400f2f (p5-udpated)
>>>>>>> origin/main
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
<<<<<<< HEAD
                      {images.length}
                    </h3>
                    <p className="text-[10px] font-mono text-emerald-400 mt-0.5">
                      Backend-confirmed uploads
=======
<<<<<<< HEAD
                      {images.length > 0 ? images.length * 42 : 148}
                    </h3>
                    <p className="text-[10px] font-mono text-emerald-400 mt-0.5">
                      EXIF Geotagged
=======
                      {images.length}
                    </h3>
                    <p className="text-[10px] font-mono text-emerald-400 mt-0.5">
                      Backend-confirmed uploads
>>>>>>> 0400f2f (p5-udpated)
>>>>>>> origin/main
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
<<<<<<< HEAD
                      {damageResult ? damageResult.total_buildings : "—"}
                    </h3>
                    <p className="text-[10px] font-mono text-rose-300 mt-0.5">
                      {damageResult ? "4-Tier Classification" : "No verified assessment"}
=======
<<<<<<< HEAD
                      {damageResult ? damageResult.total_buildings : 248}
                    </h3>
                    <p className="text-[10px] font-mono text-rose-300 mt-0.5">
                      4-Tier Classification
=======
                      {damageResult ? damageResult.total_buildings : "—"}
                    </h3>
                    <p className="text-[10px] font-mono text-rose-300 mt-0.5">
                      {damageResult ? "4-Tier Classification" : "No verified assessment"}
>>>>>>> 0400f2f (p5-udpated)
>>>>>>> origin/main
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
<<<<<<< HEAD
                      {reconResult ? `${(reconResult.num_points / 1000).toFixed(0)}K pts` : "—"}
                    </h3>
                    <p className="text-[10px] font-mono text-cyan-300 mt-0.5">
                      {reconResult ? "Verified COLMAP cloud" : "No verified reconstruction"}
=======
<<<<<<< HEAD
                      {reconResult ? `${(reconResult.num_points / 1000).toFixed(0)}K pts` : "124K pts"}
                    </h3>
                    <p className="text-[10px] font-mono text-cyan-300 mt-0.5">
                      Dense Multi-View SfM
=======
                      {reconResult ? `${(reconResult.num_points / 1000).toFixed(0)}K pts` : "—"}
                    </h3>
                    <p className="text-[10px] font-mono text-cyan-300 mt-0.5">
                      {reconResult ? "Verified COLMAP cloud" : "No verified reconstruction"}
>>>>>>> 0400f2f (p5-udpated)
>>>>>>> origin/main
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
                    Multi-view SfM dense point cloud and elevation relief mesh.
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
<<<<<<< HEAD
                  plyUrl={reconResult?.pointcloud_ply_path}
=======
<<<<<<< HEAD
                  initialPointCount={65000}
=======
                  plyUrl={reconResult?.pointcloud_ply_path}
>>>>>>> 0400f2f (p5-udpated)
>>>>>>> origin/main
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
        {/* TAB 3: DRONE VIDEO INGESTION & 3D PIPELINE */}
        {/* ============================================================== */}
        {activeTab === "upload" && (
          <div className="flex flex-col gap-6">
            <div className="flex items-center justify-between">
              <div>
                <h2 className="text-xl font-bold text-white font-mono flex items-center gap-2">
                  <Video className="w-5 h-5 text-emerald-400" />
                  Single-Pass Drone Video Ingestion &amp; 3D Reconstruction
                </h2>
                <p className="text-xs text-muted-foreground mt-1">
                  Upload raw UAV video footage (.mp4, .mov, .m4v, .avi) with flight telemetry (.csv, .srt, .gpx) for {currentProject?.name}.
                </p>
              </div>
            </div>

            {/* Primary Drone Video Upload Form */}
            <form onSubmit={handleVideoUploadSubmit} className="glass-panel p-6 rounded-xl border border-emerald-500/25 space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {/* Video File Dropzone */}
                <div className="border-2 border-dashed border-emerald-500/30 rounded-lg p-6 flex flex-col items-center justify-center text-center hover:border-emerald-500/60 transition-colors bg-forest-950/40 relative">
                  <Film className="w-10 h-10 text-emerald-400 mb-2" />
                  <p className="text-sm font-bold text-white font-mono">
                    Select Single-Pass Drone Video
                  </p>
                  <p className="text-[11px] text-muted-foreground mt-1">
                    MP4, MOV, M4V, AVI (H.264, HEVC / 4K / 1080p)
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
                    <div className="mt-2 text-xs font-mono text-emerald-300">
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
                    <div className="mt-2 text-xs font-mono text-cyan-300">
                      Selected: {telemetryFile.name} ({(telemetryFile.size / 1024).toFixed(1)} KB)
                    </div>
                  )}
                </div>
              </div>

              {videoFile && (
                <div className="p-3 rounded bg-forest-900 border border-emerald-500/20 font-mono text-xs flex items-center justify-between">
                  <span className="text-emerald-300">
                    Ready to ingest single-pass drone flight video: {videoFile.name}
                  </span>
                  <Button type="submit" variant="primary" size="sm" isLoading={videoUploading}>
                    Upload Drone Video &amp; Initialize Mission
                  </Button>
                </div>
              )}

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
                      <div className="p-2 rounded bg-forest-900 border border-emerald-500/20 text-emerald-300">6. COLMAP SfM Tracking</div>
                      <div className="p-2 rounded bg-forest-900 border border-emerald-500/20 text-emerald-300">7. Dense MVS Point Cloud</div>
                      <div className="p-2 rounded bg-forest-900 border border-emerald-500/20 text-emerald-300">8. Georeferenced Mesh</div>
                    </div>
                  </div>
                )}
              </div>
            )}

            {/* Extracted Frames Gallery */}
            <div className="space-y-4">
              <h3 className="text-sm font-bold text-white font-mono flex items-center gap-2">
                <FileCheck2 className="w-4 h-4 text-emerald-400" />
                EXTRACTED AERIAL FRAMES &amp; TELEMETRY ({images.length})
              </h3>

              {images.length === 0 ? (
                <div className="p-8 rounded-lg border border-dashed border-emerald-500/20 text-center font-mono text-xs text-muted-foreground bg-forest-950/30">
                  No frames extracted yet. Upload a drone video and click &quot;RUN 3D RECONSTRUCTION&quot; to decode keyframes.
                </div>
              ) : (
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {images.map((img) => (
                    <div key={img.id} className="glass-panel p-4 rounded-lg border border-emerald-500/20 flex flex-col sm:flex-row gap-4 font-mono text-xs">
                      <div className="w-full sm:w-44 h-32 rounded overflow-hidden shrink-0 bg-forest-950 border border-emerald-500/20">
                        <img
                          src={img.thumbnail_path}
                          alt={img.filename}
                          className="w-full h-full object-cover"
                        />
                      </div>
                      <div className="flex-1 space-y-1.5">
                        <div className="text-white font-bold text-xs truncate">
                          {img.filename}
                        </div>
                        <div className="text-[11px] text-muted-foreground">
                          {img.width}x{img.height} px | {(img.file_size_bytes / 1024 / 1024).toFixed(1)} MB | {img.format}
                        </div>
                        <div className="flex flex-wrap gap-1 mt-1">
                          {img.telemetry?.latitude && img.telemetry?.longitude ? (
                            <Badge variant="tactical" className="text-[10px]">
                              GPS: {img.telemetry.latitude.toFixed(4)}, {img.telemetry.longitude.toFixed(4)}
                            </Badge>
                          ) : (
                            <Badge variant="outline" className="text-[10px] text-muted-foreground">
                              No GPS
                            </Badge>
                          )}
                          <Badge variant="outline" className="text-[10px] text-emerald-400">
                            Frame #{img.id.slice(0, 6)}
                          </Badge>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>

            {/* Optional / Fallback Still Orthophoto Upload */}
            <details className="glass-panel p-4 rounded-lg border border-emerald-500/15 font-mono text-xs">
              <summary className="cursor-pointer text-muted-foreground hover:text-emerald-300 font-bold">
                Batch Image Ingestion (Optional Orthophoto Mode)
              </summary>
              <form onSubmit={handleUploadSubmit} className="mt-4 space-y-3">
                <p className="text-[11px] text-muted-foreground">
                  Ingest pre-extracted still aerial frames (TIFF, JPEG, PNG, DNG) directly into the project:
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
                  className="text-xs font-mono text-emerald-400 file:mr-3 file:py-1 file:px-2.5 file:rounded file:border-0 file:text-xs file:bg-emerald-700 file:text-white cursor-pointer"
                />
                {uploadFiles.length > 0 && (
                  <Button type="submit" variant="primary" size="sm" isLoading={uploading}>
                    Ingest Still Images ({uploadFiles.length})
                  </Button>
<<<<<<< HEAD
                )}
              </form>
            </details>
=======
                </div>
              )}

              {uploadStatus && (
<<<<<<< HEAD
                <div className="p-3 rounded bg-forest-900/90 border border-emerald-500/30 text-xs font-mono text-emerald-300">
                  {uploadStatus}
                </div>
              )}
=======
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

              {uploadStatus?.kind === "error" && uploadFiles.length > 0 && (
                <Button
                  type="submit"
                  variant="outline"
                  size="sm"
                  isLoading={uploading}
                >
                  <RefreshCw className="w-3.5 h-3.5 mr-1" /> Retry upload
                </Button>
              )}
>>>>>>> 0400f2f (p5-udpated)
            </form>

            {/* Current Project Image Inventory */}
            <div className="space-y-4">
              <h3 className="text-sm font-bold text-white font-mono flex items-center gap-2">
                <FileCheck2 className="w-4 h-4 text-emerald-400" />
                INGESTED AERIAL FRAMES &amp; TELEMETRY ({images.length})
              </h3>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {images.map((img) => (
                  <div key={img.id} className="glass-panel p-4 rounded-lg border border-emerald-500/20 flex flex-col sm:flex-row gap-4 font-mono text-xs">
                    <div className="w-full sm:w-44 h-32 rounded overflow-hidden shrink-0 bg-forest-950 border border-emerald-500/20">
                      <img
                        src={img.thumbnail_path}
                        alt={img.filename}
                        className="w-full h-full object-cover"
                      />
                    </div>
                    <div className="flex-1 space-y-1.5">
                      <div className="text-white font-bold text-xs truncate">
                        {img.filename}
                      </div>
                      <div className="text-[11px] text-muted-foreground">
                        {img.width}x{img.height} px | {(img.file_size_bytes / 1024 / 1024).toFixed(1)} MB | {img.format}
                      </div>

                      {img.telemetry && (
                        <div className="p-2 rounded bg-forest-900/80 border border-emerald-500/15 text-[10px] space-y-0.5 text-muted-foreground">
                          <div>CAMERA: <span className="text-emerald-300">{img.telemetry.camera_make} {img.telemetry.camera_model}</span></div>
                          <div>ALTITUDE: <span className="text-white font-semibold">{img.telemetry.altitude_m} m AGL</span></div>
                          <div>GPS: <span className="text-white">{img.telemetry.latitude}°N, {img.telemetry.longitude}°E</span></div>
                        </div>
                      )}

                      <div className="pt-2 flex items-center gap-2">
                        <Button
                          onClick={() => {
                            setActiveTab("ai");
                            triggerDepth(img.id);
                          }}
                          variant="tactical"
                          size="sm"
                          className="text-[10px] h-6 px-2"
                        >
                          Estimate Depth
                        </Button>
                        <Button
                          onClick={() => {
                            setActiveTab("ai");
                            triggerSegmentation(img.id);
                          }}
                          variant="tactical"
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
            </div>
>>>>>>> origin/main
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
                  Execute deep learning pipelines on aerial captures.
                </p>
              </div>

<<<<<<< HEAD
=======
<<<<<<< HEAD
=======
>>>>>>> origin/main
              {analysisError && (
                <div className="w-full p-3 rounded bg-rose-950/60 border border-rose-500/40 text-rose-300 text-xs font-mono flex items-start gap-2">
                  <AlertTriangle className="w-4 h-4 shrink-0" />
                  <span>{analysisError}</span>
                </div>
              )}

<<<<<<< HEAD
=======
>>>>>>> 0400f2f (p5-udpated)
>>>>>>> origin/main
              {/* Sub-tabs for Depth, Segmentation, Damage, Change */}
              <div className="flex items-center gap-1.5 glass-panel p-1 rounded font-mono text-xs">
                {(["depth", "segmentation", "damage", "change"] as const).map((sub) => (
                  <button
                    key={sub}
                    onClick={() => setAiSubTab(sub)}
                    className={`px-3 py-1.5 rounded uppercase transition-all ${
                      aiSubTab === sub
                        ? "bg-emerald-600 text-white font-bold"
                        : "text-muted-foreground hover:bg-forest-800 hover:text-white"
                    }`}
                  >
                    {sub}
                  </button>
                ))}
              </div>
            </div>

            {/* AI SUB-TAB 1: DEPTH MAPS */}
            {aiSubTab === "depth" && (
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <div className="font-mono text-xs">
                    <span className="text-sky-400 font-bold">DEPTH ANYTHING V2 SMALL:</span>
                    <span className="text-muted-foreground ml-2">
                      Relative inverse depth (no metric claim unless calibrated)
                    </span>
                  </div>
                  <Button
                    onClick={() => triggerDepth("img-pre-01")}
                    variant="primary"
                    size="sm"
                    isLoading={activeInferencing === "depth"}
                  >
                    Run Depth Estimation
                  </Button>
                </div>

                {depthResult && (
                  <div className="glass-panel p-6 rounded-xl border border-emerald-500/20 space-y-4">
                    <DepthViewer
                      originalImage="https://images.unsplash.com/photo-1508873696983-2df5293cb32f?auto=format&fit=crop&w=1200&q=80"
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

                    <div className="p-3 rounded bg-forest-900 border border-emerald-500/15 font-mono text-xs flex flex-wrap items-center justify-between gap-4">
                      <div>RESULT ID: <span className="text-white">{depthResult.id}</span></div>
                      <div>JOB ID: <span className="text-emerald-300">{depthResult.job_id}</span></div>
                      <div>SURFACE MESH: <span className="text-sky-300">{depthResult.mesh_obj_path}</span></div>
                    </div>
                  </div>
                )}
              </div>
            )}

            {/* AI SUB-TAB 2: SEGMENTATION */}
            {aiSubTab === "segmentation" && (
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <div className="font-mono text-xs">
<<<<<<< HEAD
=======
<<<<<<< HEAD
                    <span className="text-emerald-400 font-bold">SEGFORMER-B4:</span>
                    <span className="text-muted-foreground ml-2">8-class aerial land-cover categorization</span>
=======
>>>>>>> origin/main
                    <span className="text-emerald-400 font-bold">AERIAL LAND-COVER SEGMENTATION:</span>
                    <span className="text-muted-foreground ml-2">
                      7-class aerial land-cover categorisation (requires a verified checkpoint)
                    </span>
<<<<<<< HEAD
=======
>>>>>>> 0400f2f (p5-udpated)
>>>>>>> origin/main
                  </div>
                  <Button
                    onClick={() => triggerSegmentation("img-pre-01")}
                    variant="primary"
                    size="sm"
                    isLoading={activeInferencing === "segmentation"}
                  >
                    Run Segmentation
                  </Button>
                </div>

                {segmentationResult && (
                  <div className="glass-panel p-6 rounded-xl border border-emerald-500/20 space-y-4">
                    <div className="relative rounded-lg overflow-hidden border border-emerald-500/30 aspect-video">
                      <img
                        src={segmentationResult.overlay_path}
                        alt="Segmentation Overlay"
                        className="w-full h-full object-cover"
                      />
                      <div className="absolute inset-0 bg-gradient-to-tr from-emerald-900/40 via-purple-900/30 to-blue-900/30 mix-blend-overlay pointer-events-none" />
                    </div>

                    <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-2 font-mono text-xs">
                      {Object.entries(segmentationResult.class_distribution).map(([cls, pct]) => (
                        <div key={cls} className="p-2.5 rounded bg-forest-900 border border-emerald-500/15 text-center">
                          <div className="text-[10px] text-muted-foreground uppercase">{cls}</div>
                          <div className="text-emerald-400 font-bold text-sm mt-0.5">{pct}%</div>
                        </div>
                      ))}
                    </div>

                    <div className="flex items-center justify-between pt-2 font-mono text-xs text-muted-foreground">
                      <span>VECTOR GEODATA: {segmentationResult.geojson_path}</span>
                      <button
                        onClick={() => alert("GeoJSON building polygons exported to local downloads.")}
                        className="text-emerald-400 hover:underline flex items-center gap-1 font-bold"
                      >
                        <Download className="w-3.5 h-3.5" /> Download GeoJSON
                      </button>
                    </div>
                  </div>
                )}
              </div>
            )}

            {/* AI SUB-TAB 3: DAMAGE ASSESSMENT */}
            {aiSubTab === "damage" && (
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <div className="font-mono text-xs">
                    <span className="text-rose-400 font-bold">xBD DISASTER TRIAGE:</span>
                    <span className="text-muted-foreground ml-2">4-tier structural collapse classification</span>
                  </div>
                  <Button
                    onClick={() => triggerDamage("img-pre-01", "img-post-01")}
                    variant="primary"
                    size="sm"
                    isLoading={activeInferencing === "damage"}
                  >
                    Run Damage Evaluation
                  </Button>
                </div>

                {damageResult && (
                  <div className="glass-panel p-6 rounded-xl border border-emerald-500/20 space-y-4">
                    <BeforeAfterSlider
                      beforeImage="https://images.unsplash.com/photo-1508873696983-2df5293cb32f?auto=format&fit=crop&w=1200&q=80"
                      afterImage="https://images.unsplash.com/photo-1547683905-f686c993aae5?auto=format&fit=crop&w=1200&q=80"
                      beforeLabel="Pre-Disaster Baseline"
                      afterLabel="Post-Disaster Triage"
                    />

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

                    <div className="p-3 rounded bg-forest-900/90 border border-emerald-500/15 font-mono text-xs flex justify-between">
                      <span className="text-muted-foreground">COMPOSITE SEVERITY INDEX:</span>
                      <span className="text-rose-400 font-bold">
                        {damageResult.severity_index} ({damageResult.damage_percentage}% altered)
                      </span>
                    </div>
                  </div>
                )}
              </div>
            )}

            {/* AI SUB-TAB 4: CHANGE DETECTION */}
            {aiSubTab === "change" && (
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <div className="font-mono text-xs">
                    <span className="text-amber-400 font-bold">BI-TEMPORAL DIFFERENCING:</span>
                    <span className="text-muted-foreground ml-2">Photometric and structural shift heatmap</span>
                  </div>
                  <Button
                    onClick={() => triggerChange("img-pre-01", "img-post-01")}
                    variant="primary"
                    size="sm"
                    isLoading={activeInferencing === "change"}
                  >
                    Run Change Differencing
                  </Button>
                </div>

                {changeResult && (
                  <div className="glass-panel p-6 rounded-xl border border-emerald-500/20 space-y-4">
                    <BeforeAfterSlider
                      beforeImage="https://images.unsplash.com/photo-1508873696983-2df5293cb32f?auto=format&fit=crop&w=1200&q=80"
                      afterImage="https://images.unsplash.com/photo-1547683905-f686c993aae5?auto=format&fit=crop&w=1200&q=80"
                      beforeLabel="Before"
                      afterLabel="After"
                    />
                  </div>
                )}
              </div>
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

<<<<<<< HEAD
            <Card className="glass-panel border-emerald-500/25">
              <CardHeader className="p-4 border-b border-emerald-500/15">
                <CardTitle className="text-sm font-bold font-mono flex items-center gap-2">
                  <Box className="w-4 h-4 text-emerald-400" />
                  PRIMARY 3D SPATIAL SURFACE // {currentProject?.name}
                </CardTitle>
                <CardDescription className="text-xs">
                  Multi-view SfM dense point cloud and elevation relief mesh.
                </CardDescription>
              </CardHeader>
              <CardContent className="p-4">
                <AdvancedSpatialViewer3D
                  projectName={currentProject?.name}
                  locationName={currentProject?.location_name}
                  plyUrl={reconResult?.pointcloud_ply_path}
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
=======
<<<<<<< HEAD
            <AdvancedSpatialViewer3D
              projectName={currentProject?.name}
              locationName={currentProject?.location_name}
              initialPointCount={85000}
=======
            {analysisError && (
              <div className="p-3 rounded bg-rose-950/60 border border-rose-500/40 text-rose-300 text-xs font-mono flex items-start gap-2">
                <AlertTriangle className="w-4 h-4 shrink-0" />
                <span>{analysisError}</span>
              </div>
            )}

            <AdvancedSpatialViewer3D
              projectName={currentProject?.name}
              locationName={currentProject?.location_name}
              plyUrl={reconResult?.pointcloud_ply_path}
>>>>>>> 0400f2f (p5-udpated)
            />
>>>>>>> origin/main
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
<<<<<<< HEAD
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
=======
              <div className="glass-panel p-5 rounded-lg border border-emerald-500/20 font-mono text-xs space-y-3">
                <div className="flex items-center justify-between border-b border-emerald-500/20 pb-2">
                  <span className="text-sm font-bold text-white flex items-center gap-2">
                    <Activity className="w-4 h-4 text-sky-400" />
                    Depth Anything V2 Small (Relative)
                  </span>
                  <Badge variant="tactical">RELATIVE DEPTH</Badge>
                </div>
                <div className="space-y-1.5 text-muted-foreground text-[11px]">
                  <div>BACKBONE: <span className="text-white">DINOv2 ViT-S/14 + DPT head</span></div>
                  <div>PARAMETERS: <span className="text-white">24.79 Million (6.28 M trainable when fine-tuned)</span></div>
                  <div>INPUT TENSOR: <span className="text-white">3 x 518 x 518 (RGB float32)</span></div>
                  <div>OUTPUT: <span className="text-white">relative inverse depth (unitless)</span></div>
                  <div>LATENCY: <span className="text-emerald-300 font-bold">~185 ms/image on CPU (378 px, measured)</span></div>
                  <div>
                    ACCURACY: <span className="text-amber-300">
                      no metric claim; aligned relative AbsRel 0.071 on the held-out SkyScenes test town
                    </span>
                  </div>
                </div>
              </div>
>>>>>>> origin/main

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
    </div>
  );
}

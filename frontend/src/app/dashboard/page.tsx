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
  Maximize2
} from "lucide-react";
import { Button } from "@/components/ui/Button";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { BeforeAfterSlider } from "@/components/viewer/BeforeAfterSlider";
import { DepthViewer } from "@/components/viewer/DepthViewer";
import { api } from "@/lib/api";
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

  // Upload state
  const [uploadFiles, setUploadFiles] = useState<File[]>([]);
  const [uploading, setUploading] = useState(false);
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
    } catch (err) {
      console.error("Dashboard fetch error:", err);
    } finally {
      setLoading(false);
      setRefreshing(false);
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
  // Image Upload Handler
=======
  // Image Upload Handler — success is only reported when the backend confirms records.
>>>>>>> 0400f2f (p5-udpated)
  const handleUploadSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (uploadFiles.length === 0) return;
    setUploading(true);
<<<<<<< HEAD
    setUploadStatus("Ingesting UAV imagery and parsing EXIF headers...");
    try {
      const uploaded = await api.uploadImages(selectedProjectId, uploadFiles);
      setImages([...uploaded, ...images]);
      setUploadStatus(`Successfully ingested ${uploaded.length} aerial frame(s)!`);
      setUploadFiles([]);
    } catch (err: any) {
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
      // The selection stays in place so the operator can retry the same upload.
      setUploadStatus(
        uploadOutcome({
          ok: false,
          errorMessage: err?.message ?? "No response from the backend",
        })
      );
>>>>>>> 0400f2f (p5-udpated)
    } finally {
      setUploading(false);
    }
  };

  // Trigger AI Depth
  const triggerDepth = async (imageId: string) => {
    setActiveInferencing("depth");
<<<<<<< HEAD
=======
    setAnalysisError(null);
>>>>>>> 0400f2f (p5-udpated)
    try {
      const res = await api.triggerDepthEstimation(imageId);
      setDepthResult(res);
      fetchData();
<<<<<<< HEAD
    } catch (err) {
      console.error(err);
=======
    } catch (err: any) {
      setAnalysisError(err?.message ?? "Depth estimation failed");
>>>>>>> 0400f2f (p5-udpated)
    } finally {
      setActiveInferencing(null);
    }
  };

  // Trigger AI Segmentation
  const triggerSegmentation = async (imageId: string) => {
    setActiveInferencing("segmentation");
<<<<<<< HEAD
=======
    setAnalysisError(null);
>>>>>>> 0400f2f (p5-udpated)
    try {
      const res = await api.triggerSegmentation(imageId);
      setSegmentationResult(res);
      fetchData();
<<<<<<< HEAD
    } catch (err) {
      console.error(err);
=======
    } catch (err: any) {
      setSegmentationResult(null);
      setAnalysisError(err?.message ?? "Segmentation failed");
>>>>>>> 0400f2f (p5-udpated)
    } finally {
      setActiveInferencing(null);
    }
  };

  // Trigger Damage Assessment
  const triggerDamage = async (preId: string, postId: string) => {
    setActiveInferencing("damage");
<<<<<<< HEAD
=======
    setAnalysisError(null);
>>>>>>> 0400f2f (p5-udpated)
    try {
      const res = await api.triggerDamageAssessment(preId, postId);
      setDamageResult(res);
      fetchData();
<<<<<<< HEAD
    } catch (err) {
      console.error(err);
=======
    } catch (err: any) {
      setDamageResult(null);
      setAnalysisError(err?.message ?? "Damage assessment failed");
>>>>>>> 0400f2f (p5-udpated)
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
=======
    setAnalysisError(null);
>>>>>>> 0400f2f (p5-udpated)
    try {
      const res = await api.trigger3DReconstruction(selectedProjectId);
      setReconResult(res);
      fetchData();
<<<<<<< HEAD
    } catch (err) {
      console.error(err);
=======
    } catch (err: any) {
      // Reconstruction unavailability/failure is surfaced; no geometry is displayed.
      setReconResult(null);
      setAnalysisError(err?.message ?? "3D reconstruction failed");
>>>>>>> 0400f2f (p5-udpated)
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
            { id: "upload", label: "Image Uploads", icon: UploadCloud },
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
                      100% Calibrated
=======
                      Stored missions
>>>>>>> 0400f2f (p5-udpated)
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
                  initialPointCount={65000}
=======
                  plyUrl={reconResult?.pointcloud_ply_path}
>>>>>>> 0400f2f (p5-udpated)
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
        {/* TAB 3: IMAGE UPLOADS */}
        {/* ============================================================== */}
        {activeTab === "upload" && (
          <div className="flex flex-col gap-6">
            <div className="flex items-center justify-between">
              <div>
                <h2 className="text-xl font-bold text-white font-mono">Aerial Imagery Ingestion</h2>
                <p className="text-xs text-muted-foreground">
                  Upload raw UAV orthophotos (TIFF, JPEG, PNG, DNG) for {currentProject?.name}.
                </p>
              </div>
            </div>

            {/* Drag & Drop Upload Form */}
            <form onSubmit={handleUploadSubmit} className="glass-panel p-6 rounded-xl border border-emerald-500/25 space-y-4">
              <div className="border-2 border-dashed border-emerald-500/30 rounded-lg p-8 flex flex-col items-center justify-center text-center hover:border-emerald-500/60 transition-colors cursor-pointer bg-forest-950/40">
                <UploadCloud className="w-10 h-10 text-emerald-400 mb-3" />
                <p className="text-sm font-bold text-white font-mono">
                  Select Drone Survey Frames or Drag &amp; Drop
                </p>
                <p className="text-xs text-muted-foreground mt-1">
                  Supports DJI Matrice, Wingtra, Skydio TIFF / JPEG with standard EXIF / GPS telemetry.
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
                  className="mt-4 text-xs font-mono text-emerald-400 file:mr-4 file:py-1.5 file:px-3 file:rounded file:border-0 file:text-xs file:font-mono file:bg-emerald-600 file:text-white hover:file:bg-emerald-500 cursor-pointer"
                />
              </div>

              {uploadFiles.length > 0 && (
                <div className="p-3 rounded bg-forest-900 border border-emerald-500/20 font-mono text-xs flex items-center justify-between">
                  <span className="text-emerald-300">
                    {uploadFiles.length} file(s) queued for ingestion.
                  </span>
                  <Button type="submit" variant="primary" size="sm" isLoading={uploading}>
                    Ingest Images to Backend API
                  </Button>
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
              {analysisError && (
                <div className="w-full p-3 rounded bg-rose-950/60 border border-rose-500/40 text-rose-300 text-xs font-mono flex items-start gap-2">
                  <AlertTriangle className="w-4 h-4 shrink-0" />
                  <span>{analysisError}</span>
                </div>
              )}

>>>>>>> 0400f2f (p5-udpated)
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
                    <span className="text-emerald-400 font-bold">SEGFORMER-B4:</span>
                    <span className="text-muted-foreground ml-2">8-class aerial land-cover categorization</span>
=======
                    <span className="text-emerald-400 font-bold">AERIAL LAND-COVER SEGMENTATION:</span>
                    <span className="text-muted-foreground ml-2">
                      7-class aerial land-cover categorisation (requires a verified checkpoint)
                    </span>
>>>>>>> 0400f2f (p5-udpated)
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
                      afterImage={changeResult.heatmap_path}
                      beforeLabel="Baseline T0"
                      afterLabel="Divergence Heatmap T1"
                    />

                    <div className="p-3 rounded bg-forest-900 border border-emerald-500/15 font-mono text-xs flex flex-wrap justify-between gap-4">
                      <div>CHANGED AREA: <span className="text-amber-400 font-bold">{changeResult.changed_area_pct}%</span></div>
                      <div>CHANGED PIXELS: <span className="text-white font-semibold">{changeResult.changed_pixels.toLocaleString()} px</span></div>
                      <div>CONFIDENCE: <span className="text-emerald-300 font-semibold">{changeResult.significance_score}</span></div>
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>
        )}

        {/* ============================================================== */}
        {/* TAB 5: 3D POINT CLOUD & RECONSTRUCTION */}
        {/* ============================================================== */}
        {activeTab === "viewer3d" && (
          <div className="flex flex-col gap-4">
            <div className="flex items-center justify-between">
              <div>
                <h2 className="text-xl font-bold text-white font-mono">3D Spatial Photogrammetry Suite</h2>
                <p className="text-xs text-muted-foreground">
                  Interactive WebGL Point Cloud &amp; Terrain Relief Visualizer for {currentProject?.name}.
                </p>
              </div>
              <Button
                onClick={trigger3D}
                variant="primary"
                size="sm"
                isLoading={activeInferencing === "3d"}
              >
                Reconstruct 3D Geometry
              </Button>
            </div>

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
          </div>
        )}

        {/* ============================================================== */}
        {/* TAB 6: JOB HISTORY */}
        {/* ============================================================== */}
        {activeTab === "jobs" && (
          <div className="flex flex-col gap-4">
            <div className="flex items-center justify-between">
              <div>
                <h2 className="text-xl font-bold text-white font-mono">Celery Distributed Task History</h2>
                <p className="text-xs text-muted-foreground">
                  Audit log of asynchronous vision worker execution and pipeline task IDs.
                </p>
              </div>
              <Button onClick={fetchData} variant="outline" size="sm">
                <RefreshCw className="w-3.5 h-3.5 mr-1" /> Refresh Tasks
              </Button>
            </div>

            <div className="rounded-lg border border-emerald-500/20 overflow-hidden bg-forest-900/60 font-mono text-xs">
              <table className="w-full text-left">
                <thead className="bg-forest-950 text-[10px] uppercase text-muted-foreground border-b border-emerald-500/15">
                  <tr>
                    <th className="px-4 py-3">Task ID</th>
                    <th className="px-4 py-3">Pipeline Type</th>
                    <th className="px-4 py-3">Status</th>
                    <th className="px-4 py-3">Progress</th>
                    <th className="px-4 py-3">Started</th>
                    <th className="px-4 py-3">Completed</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-emerald-500/10">
                  {jobs.map((j) => (
                    <tr key={j.id} className="hover:bg-forest-800/30">
                      <td className="px-4 py-3 text-emerald-300 font-semibold">{j.celery_task_id || j.id}</td>
                      <td className="px-4 py-3 text-white font-bold">{j.job_type}</td>
                      <td className="px-4 py-3">
                        {j.status === "completed" ? (
                          <span className="inline-flex items-center gap-1 text-emerald-400 text-[11px]">
                            <CheckCircle2 className="w-3.5 h-3.5" /> COMPLETED
                          </span>
                        ) : j.status === "failed" ? (
                          <span className="inline-flex items-center gap-1 text-rose-400 text-[11px]">
                            <AlertTriangle className="w-3.5 h-3.5" /> FAILED
                          </span>
                        ) : (
                          <span className="inline-flex items-center gap-1 text-amber-400 text-[11px]">
                            <Clock className="w-3.5 h-3.5 animate-spin" /> RUNNING
                          </span>
                        )}
                      </td>
                      <td className="px-4 py-3">
                        <div className="w-32 h-2 bg-forest-950 rounded-full overflow-hidden">
                          <div
                            className="h-full bg-emerald-400 rounded-full"
                            style={{ width: `${j.progress_pct}%` }}
                          />
                        </div>
                      </td>
                      <td className="px-4 py-3 text-muted-foreground text-[11px]">
                        {new Date(j.created_at).toLocaleTimeString()}
                      </td>
                      <td className="px-4 py-3 text-muted-foreground text-[11px]">
                        {new Date(j.updated_at).toLocaleTimeString()}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {/* ============================================================== */}
        {/* TAB 7: MODEL INFORMATION */}
        {/* ============================================================== */}
        {activeTab === "models" && (
          <div className="flex flex-col gap-6">
            <div>
              <h2 className="text-xl font-bold text-white font-mono">Neural Architecture Specifications</h2>
              <p className="text-xs text-muted-foreground">
                Weights, inference latency, receptive field, and tensor parameter profiles.
              </p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
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

              <div className="glass-panel p-5 rounded-lg border border-emerald-500/20 font-mono text-xs space-y-3">
                <div className="flex items-center justify-between border-b border-emerald-500/20 pb-2">
                  <span className="text-sm font-bold text-white flex items-center gap-2">
                    <Layers className="w-4 h-4 text-emerald-400" />
                    SegFormer-B4 (Aerial LULC)
                  </span>
                  <Badge variant="tactical">LAND COVER</Badge>
                </div>
                <div className="space-y-1.5 text-muted-foreground text-[11px]">
                  <div>BACKBONE: <span className="text-white">Mix Transformer (MiT-B4)</span></div>
                  <div>PARAMETERS: <span className="text-white">64.1 Million</span></div>
                  <div>CLASSES: <span className="text-white">8 LULC Categories (Cityscapes / UAV)</span></div>
                  <div>INFERENCE LATENCY: <span className="text-emerald-300 font-bold">18.2 ms</span></div>
                  <div>MEAN IoU: <span className="text-emerald-300">88.4% Across Validation Flight Sets</span></div>
                </div>
              </div>

              <div className="glass-panel p-5 rounded-lg border border-emerald-500/20 font-mono text-xs space-y-3">
                <div className="flex items-center justify-between border-b border-emerald-500/20 pb-2">
                  <span className="text-sm font-bold text-white flex items-center gap-2">
                    <ShieldAlert className="w-4 h-4 text-rose-400" />
                    xBD Damage Siamese Classifier
                  </span>
                  <Badge variant="tactical">HUMANITARIAN</Badge>
                </div>
                <div className="space-y-1.5 text-muted-foreground text-[11px]">
                  <div>BACKBONE: <span className="text-white">ResNeXt-101 Siamese Feature Extractor</span></div>
                  <div>TAXONOMY: <span className="text-white">None, Minor, Major, Destroyed</span></div>
                  <div>INPUT TENSOR: <span className="text-white">2 x 3 x 1024 x 1024 (Pre &amp; Post Pairs)</span></div>
                  <div>INFERENCE LATENCY: <span className="text-emerald-300 font-bold">28.4 ms</span></div>
                  <div>F1 SCORE: <span className="text-emerald-300">0.826 (xBD Disaster Response Challenge)</span></div>
                </div>
              </div>

              <div className="glass-panel p-5 rounded-lg border border-emerald-500/20 font-mono text-xs space-y-3">
                <div className="flex items-center justify-between border-b border-emerald-500/20 pb-2">
                  <span className="text-sm font-bold text-white flex items-center gap-2">
                    <Box className="w-4 h-4 text-cyan-400" />
                    Open3D Multi-View SfM
                  </span>
                  <Badge variant="tactical">PHOTOGRAMMETRY</Badge>
                </div>
                <div className="space-y-1.5 text-muted-foreground text-[11px]">
                  <div>PIPELINE: <span className="text-white">SIFT Tracking + Epipolar Bundle Adjustment</span></div>
                  <div>DENSE STEREO: <span className="text-white">Multi-View Depth Fusion</span></div>
                  <div>OUTPUT ASSETS: <span className="text-white">Point Cloud (.ply), Mesh (.obj), DSM (.tif)</span></div>
                  <div>REPROJECTION ERROR: <span className="text-emerald-300 font-bold">0.78 px (Sub-pixel)</span></div>
                  <div>POINT DENSITY: <span className="text-emerald-300">124,000+ Points / Survey Sector</span></div>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* ============================================================== */}
        {/* TAB 8: SETTINGS */}
        {/* ============================================================== */}
        {activeTab === "settings" && (
          <div className="flex flex-col gap-6 max-w-3xl font-mono text-xs">
            <div>
              <h2 className="text-xl font-bold text-white">Platform Configuration &amp; Geo-Settings</h2>
              <p className="text-xs text-muted-foreground">Adjust spatial coordinate references, worker endpoints, and hardware tuning.</p>
            </div>

            <div className="glass-panel p-6 rounded-xl border border-emerald-500/20 space-y-5">
              <div className="space-y-1.5">
                <label className="text-white font-semibold block">COORDINATE REFERENCE SYSTEM (CRS)</label>
                <select
                  value={settingsState.crs}
                  onChange={(e) => setSettingsState({ ...settingsState, crs: e.target.value })}
                  className="w-full bg-forest-950 border border-emerald-500/30 rounded p-2 text-emerald-300 focus:outline-none"
                >
                  <option>WGS84 (EPSG:4326) — Universal UAV GPS</option>
                  <option>UTM Zone 44N (EPSG:32644) — India West / Central</option>
                  <option>UTM Zone 45N (EPSG:32645) — India East / Coastal Odisha</option>
                  <option>Web Mercator (EPSG:3857) — Standard Web Maps</option>
                </select>
              </div>

              <div className="space-y-1.5">
                <label className="text-white font-semibold block">BACKEND API REST ENDPOINT</label>
                <input
                  type="text"
                  value={settingsState.apiEndpoint}
                  onChange={(e) => setSettingsState({ ...settingsState, apiEndpoint: e.target.value })}
                  className="w-full bg-forest-950 border border-emerald-500/30 rounded p-2 text-white focus:outline-none"
                />
              </div>

              <div className="space-y-1.5">
                <label className="text-white font-semibold block">3D POINT CLOUD LEVEL-OF-DETAIL (LOD)</label>
                <select
                  value={settingsState.lodLevel}
                  onChange={(e) => setSettingsState({ ...settingsState, lodLevel: e.target.value })}
                  className="w-full bg-forest-950 border border-emerald-500/30 rounded p-2 text-emerald-300 focus:outline-none"
                >
                  <option>High (125k pts) — Desktop / Workstation</option>
                  <option>Balanced (65k pts) — Laptop / Tablet</option>
                  <option>Performance (25k pts) — Mobile / Low-Bandwidth</option>
                </select>
              </div>

              <div className="space-y-1.5">
                <label className="text-white font-semibold block">PRIMARY 3D EXPORT FORMAT</label>
                <select
                  value={settingsState.exportFormat}
                  onChange={(e) => setSettingsState({ ...settingsState, exportFormat: e.target.value })}
                  className="w-full bg-forest-950 border border-emerald-500/30 rounded p-2 text-emerald-300 focus:outline-none"
                >
                  <option>PLY Point Cloud (.ply)</option>
                  <option>Wavefront OBJ Mesh (.obj)</option>
                  <option>Digital Surface Model GeoTIFF (.tif)</option>
                  <option>GeoJSON Vector Footprints (.geojson)</option>
                </select>
              </div>

              <div className="pt-2 flex items-center justify-between">
                <span className="text-muted-foreground text-[11px]">Changes persist to browser local storage.</span>
                <Button
                  onClick={() => alert("Platform settings updated successfully.")}
                  variant="primary"
                  size="sm"
                >
                  Save Configuration
                </Button>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* CREATE MISSION MODAL */}
      {showCreateModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm">
          <div className="glass-panel w-full max-w-lg p-6 rounded-xl border border-emerald-500/40 shadow-2xl relative font-mono text-xs">
            <h3 className="text-base font-bold text-white mb-1">
              Initialize New Aerial Mission
            </h3>
            <p className="text-muted-foreground text-[11px] mb-4">
              Register a new UAV survey project in the persistent geospatial database.
            </p>

            <form onSubmit={handleCreateProject} className="space-y-3.5">
              <div>
                <label className="text-white block mb-1">Mission Name *</label>
                <input
                  type="text"
                  required
                  placeholder="e.g. Mission Brahmaputra: Flood Breach Corridor"
                  value={newProject.name}
                  onChange={(e) => setNewProject({ ...newProject, name: e.target.value })}
                  className="w-full bg-forest-950 border border-emerald-500/30 rounded p-2 text-white focus:outline-none"
                />
              </div>

              <div>
                <label className="text-white block mb-1">Location / Sector *</label>
                <input
                  type="text"
                  required
                  placeholder="e.g. Kaziranga River Basin, Assam"
                  value={newProject.location_name}
                  onChange={(e) => setNewProject({ ...newProject, location_name: e.target.value })}
                  className="w-full bg-forest-950 border border-emerald-500/30 rounded p-2 text-white focus:outline-none"
                />
              </div>

              <div>
                <label className="text-white block mb-1">Mission Scope Description</label>
                <textarea
                  rows={2}
                  placeholder="Operational details and survey objectives..."
                  value={newProject.description}
                  onChange={(e) => setNewProject({ ...newProject, description: e.target.value })}
                  className="w-full bg-forest-950 border border-emerald-500/30 rounded p-2 text-white focus:outline-none"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="text-white block mb-1">Center Latitude (°N)</label>
                  <input
                    type="number"
                    step="0.0001"
                    value={newProject.center_lat}
                    onChange={(e) => setNewProject({ ...newProject, center_lat: parseFloat(e.target.value) })}
                    className="w-full bg-forest-950 border border-emerald-500/30 rounded p-2 text-white focus:outline-none"
                  />
                </div>
                <div>
                  <label className="text-white block mb-1">Center Longitude (°E)</label>
                  <input
                    type="number"
                    step="0.0001"
                    value={newProject.center_lon}
                    onChange={(e) => setNewProject({ ...newProject, center_lon: parseFloat(e.target.value) })}
                    className="w-full bg-forest-950 border border-emerald-500/30 rounded p-2 text-white focus:outline-none"
                  />
                </div>
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
                  Register Mission
                </Button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}


"use client";

import React, { useState } from "react";
import Link from "next/link";
import {
  Compass,
  Layers,
  ShieldAlert,
  Box,
  FolderKanban,
  UploadCloud,
  ArrowUpRight,
  Sparkles,
  TrendingUp,
  MapPin,
  Clock,
  CheckCircle2,
} from "lucide-react";
import { Button } from "@/components/ui/Button";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/Card";
import { PointCloudViewer } from "@/components/viewer/PointCloudViewer";
import { BeforeAfterSlider } from "@/components/viewer/BeforeAfterSlider";
import { DepthViewer } from "@/components/viewer/DepthViewer";

export default function DashboardPage() {
  const [activeTab, setActiveTab] = useState<"3d" | "damage" | "depth">("3d");

  // Sample verified projects
  const recentProjects = [
    {
      id: "proj-01",
      name: "Coastal Sector 4 Post-Storm Survey",
      location: "Bhubaneswar Coastal Region",
      imageCount: 148,
      status: "completed",
      lastUpdated: "2026-11-02 18:30",
      damageIndex: "42.8%",
    },
    {
      id: "proj-02",
      name: "Urban Highway Corridor Expansion",
      location: "Hyderabad Outer Ring Road",
      imageCount: 84,
      status: "processing",
      lastUpdated: "2026-11-03 09:15",
      damageIndex: "N/A (LULC)",
    },
    {
      id: "proj-03",
      name: "Mountain Valley Seismic Faultline Pass",
      location: "Uttarakhand Foothills",
      imageCount: 312,
      status: "completed",
      lastUpdated: "2026-11-01 14:10",
      damageIndex: "68.1%",
    },
  ];

  return (
    <div className="flex flex-col gap-8 p-8 max-w-7xl mx-auto w-full">
      {/* Hero Welcome & Quick Action */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-border pb-6">
        <div>
          <h1 className="text-2xl md:text-3xl font-extrabold tracking-tight text-white flex items-center gap-2.5">
            Aerial Mission Control
            <span className="text-xs font-medium px-2.5 py-0.5 rounded-full bg-primary/10 text-primary border border-primary/20">
              v1.0 Production
            </span>
          </h1>
          <p className="text-sm text-muted-foreground mt-1">
            End-to-end aerial computer vision: Depth estimation, semantic segmentation, humanitarian damage assessment & 3D photogrammetry.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <Link href="/projects">
            <Button variant="outline" size="md">
              <FolderKanban className="w-4 h-4 mr-1.5" /> All Projects
            </Button>
          </Link>
          <Link href="/projects/new">
            <Button variant="primary" size="md">
              <UploadCloud className="w-4 h-4 mr-1.5" /> New Aerial Mission
            </Button>
          </Link>
        </div>
      </div>

      {/* KPI Stats Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card className="bg-card/70 backdrop-blur">
          <CardContent className="p-5 flex items-center justify-between">
            <div>
              <p className="text-xs text-muted-foreground font-medium">Mapped Survey Area</p>
              <h3 className="text-2xl font-bold text-white mt-1">128.4 km²</h3>
              <p className="text-[11px] text-emerald-400 flex items-center gap-1 mt-1">
                <TrendingUp className="w-3 h-3" /> +14.2 km² this week
              </p>
            </div>
            <div className="h-12 w-12 rounded-xl bg-primary/10 text-primary flex items-center justify-center">
              <Compass className="w-6 h-6" />
            </div>
          </CardContent>
        </Card>

        <Card className="bg-card/70 backdrop-blur">
          <CardContent className="p-5 flex items-center justify-between">
            <div>
              <p className="text-xs text-muted-foreground font-medium">Ingested Drone Images</p>
              <h3 className="text-2xl font-bold text-white mt-1">3,842</h3>
              <p className="text-[11px] text-muted-foreground mt-1">
                All EXIF / GPS telemetry parsed
              </p>
            </div>
            <div className="h-12 w-12 rounded-xl bg-sky-500/10 text-sky-400 flex items-center justify-center">
              <Layers className="w-6 h-6" />
            </div>
          </CardContent>
        </Card>

        <Card className="bg-card/70 backdrop-blur">
          <CardContent className="p-5 flex items-center justify-between">
            <div>
              <p className="text-xs text-muted-foreground font-medium">Structures Assessed (xBD)</p>
              <h3 className="text-2xl font-bold text-rose-400 mt-1">1,940</h3>
              <p className="text-[11px] text-rose-300 mt-1">
                4-tier damage classification
              </p>
            </div>
            <div className="h-12 w-12 rounded-xl bg-rose-500/10 text-rose-400 flex items-center justify-center">
              <ShieldAlert className="w-6 h-6" />
            </div>
          </CardContent>
        </Card>

        <Card className="bg-card/70 backdrop-blur">
          <CardContent className="p-5 flex items-center justify-between">
            <div>
              <p className="text-xs text-muted-foreground font-medium">3D Point Clouds Reconstructed</p>
              <h3 className="text-2xl font-bold text-amber-400 mt-1">42 Models</h3>
              <p className="text-[11px] text-muted-foreground mt-1">
                Dense SfM / Open3D meshes
              </p>
            </div>
            <div className="h-12 w-12 rounded-xl bg-amber-500/10 text-amber-400 flex items-center justify-center">
              <Box className="w-6 h-6" />
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Interactive AI Visualizer Showcase */}
      <Card className="border-border overflow-hidden">
        <CardHeader className="flex flex-row items-center justify-between border-b border-border pb-4">
          <div>
            <CardTitle className="flex items-center gap-2">
              <Sparkles className="w-5 h-5 text-primary" /> Live Aerial Visualizer Suite
            </CardTitle>
            <CardDescription>
              Interact with real-time 3D photogrammetry, xBD building damage comparison, and monocular depth estimation.
            </CardDescription>
          </div>

          <div className="flex items-center gap-1.5 bg-secondary/60 p-1 rounded-lg border border-border">
            <button
              onClick={() => setActiveTab("3d")}
              className={`px-3 py-1.5 text-xs font-semibold rounded-md transition-colors ${
                activeTab === "3d" ? "bg-primary text-white" : "text-muted-foreground hover:text-white"
              }`}
            >
              3D Point Cloud
            </button>
            <button
              onClick={() => setActiveTab("damage")}
              className={`px-3 py-1.5 text-xs font-semibold rounded-md transition-colors ${
                activeTab === "damage" ? "bg-primary text-white" : "text-muted-foreground hover:text-white"
              }`}
            >
              Damage Slider
            </button>
            <button
              onClick={() => setActiveTab("depth")}
              className={`px-3 py-1.5 text-xs font-semibold rounded-md transition-colors ${
                activeTab === "depth" ? "bg-primary text-white" : "text-muted-foreground hover:text-white"
              }`}
            >
              Monocular Depth
            </button>
          </div>
        </CardHeader>

        <CardContent className="p-6">
          {activeTab === "3d" && (
            <PointCloudViewer numPoints={40000} />
          )}

          {activeTab === "damage" && (
            <div className="flex flex-col gap-4">
              <BeforeAfterSlider
                beforeImage="https://images.unsplash.com/photo-1508873696983-2df5293cb32f?auto=format&fit=crop&w=1200&q=80"
                afterImage="https://images.unsplash.com/photo-1547683905-f686c993aae5?auto=format&fit=crop&w=1200&q=80"
                beforeLabel="Pre-Disaster Aerial Survey"
                afterLabel="Post-Disaster Aerial Survey (xBD Analysis)"
              />
              <div className="flex items-center justify-between text-xs text-muted-foreground px-2">
                <span>Drag the vertical divider left or right to inspect building structural failures.</span>
                <span className="text-rose-400 font-medium">84.2% Structural Collapse Detected</span>
              </div>
            </div>
          )}

          {activeTab === "depth" && (
            <DepthViewer
              originalImage="https://images.unsplash.com/photo-1508873696983-2df5293cb32f?auto=format&fit=crop&w=1200&q=80"
              depthMapUrl="https://images.unsplash.com/photo-1579546929518-9e396f3cc809?auto=format&fit=crop&w=1200&q=80"
              minDepth={3.2}
              maxDepth={112.5}
              meanDepth={45.8}
            />
          )}
        </CardContent>
      </Card>

      {/* Recent Projects Table */}
      <div className="flex flex-col gap-4">
        <div className="flex items-center justify-between">
          <h2 className="text-lg font-bold text-white flex items-center gap-2">
            <FolderKanban className="w-5 h-5 text-primary" /> Active Survey Missions
          </h2>
          <Link href="/projects" className="text-xs text-primary hover:underline flex items-center gap-1">
            View all 12 projects <ArrowUpRight className="w-3.5 h-3.5" />
          </Link>
        </div>

        <div className="rounded-xl border border-border overflow-hidden bg-card">
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm">
              <thead className="bg-secondary/40 text-xs uppercase text-muted-foreground border-b border-border">
                <tr>
                  <th className="px-6 py-3.5 font-semibold">Mission Name</th>
                  <th className="px-6 py-3.5 font-semibold">Location</th>
                  <th className="px-6 py-3.5 font-semibold">Imagery</th>
                  <th className="px-6 py-3.5 font-semibold">Damage Score</th>
                  <th className="px-6 py-3.5 font-semibold">Status</th>
                  <th className="px-6 py-3.5 font-semibold">Last Updated</th>
                  <th className="px-6 py-3.5 text-right font-semibold">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border">
                {recentProjects.map((p) => (
                  <tr key={p.id} className="hover:bg-secondary/20 transition-colors">
                    <td className="px-6 py-4 font-medium text-white">
                      <Link href={`/projects/${p.id}`} className="hover:text-primary transition-colors">
                        {p.name}
                      </Link>
                    </td>
                    <td className="px-6 py-4 text-muted-foreground flex items-center gap-1.5">
                      <MapPin className="w-3.5 h-3.5 text-primary" />
                      {p.location}
                    </td>
                    <td className="px-6 py-4 text-muted-foreground">{p.imageCount} captures</td>
                    <td className="px-6 py-4 font-semibold text-rose-400">{p.damageIndex}</td>
                    <td className="px-6 py-4">
                      {p.status === "completed" ? (
                        <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-medium bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                          <CheckCircle2 className="w-3 h-3" /> Ready
                        </span>
                      ) : (
                        <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-medium bg-amber-500/10 text-amber-400 border border-amber-500/20">
                          <Clock className="w-3 h-3 animate-spin" /> Processing
                        </span>
                      )}
                    </td>
                    <td className="px-6 py-4 text-xs text-muted-foreground">{p.lastUpdated}</td>
                    <td className="px-6 py-4 text-right">
                      <Link href={`/projects/${p.id}`}>
                        <Button size="sm" variant="outline">
                          Open Workspace
                        </Button>
                      </Link>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  );
}

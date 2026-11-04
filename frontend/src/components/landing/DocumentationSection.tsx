"use client";

import React, { useState } from "react";
import { 
  FileCode, 
  Terminal, 
  BookOpen, 
  Server, 
  Copy, 
  Check, 
  Layers, 
  ShieldAlert, 
  Box, 
  Key,
  ExternalLink
} from "lucide-react";
import { Badge } from "@/components/ui/Badge";

export function DocumentationSection() {
  const [activeTab, setActiveTab] = useState<"quickstart" | "api" | "architecture">("quickstart");
  const [copiedIndex, setCopiedIndex] = useState<string | null>(null);

  const copyCode = (key: string, text: string) => {
    navigator.clipboard.writeText(text);
    setCopiedIndex(key);
    setTimeout(() => setCopiedIndex(null), 2000);
  };

  const curlExample = `curl -X POST "http://localhost:8000/api/v1/auth/login/json" \\
  -H "Content-Type: application/json" \\
  -d '{"email": "analyst@jatayuv.ai", "password": "password123"}'`;

  const pythonExample = `import requests

# 1. Authenticate
token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
headers = {"Authorization": f"Bearer {token}"}

# 2. Trigger Monocular Depth Estimation
res = requests.post(
    "http://localhost:8000/api/v1/analysis/depth",
    json={"image_id": "img-pre-01"},
    headers=headers
)
depth_data = res.json()
print("Depth type:", depth_data["depth_type"], "model:", depth_data["model_label"])
print("Relative range:", depth_data["relative_min"], "-", depth_data["relative_max"])
# min_depth_m is null for relative output: Depth Anything V2 Small has no metric scale.`;

  return (
    <section id="documentation" className="py-20 bg-forest-950/90 border-b border-emerald-500/20 relative">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Section Heading */}
        <div className="flex flex-col items-center text-center max-w-3xl mx-auto mb-14">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded bg-emerald-500/10 border border-emerald-500/25 text-emerald-400 text-xs font-mono mb-3">
            <FileCode className="w-3.5 h-3.5" />
            <span>PLATFORM SPECIFICATION &amp; REPO DOCS</span>
          </div>

          <h2 className="text-3xl sm:text-4xl font-extrabold text-white tracking-tight">
            Developer &amp; Flight Analyst Documentation
          </h2>

          <p className="mt-3 text-sm sm:text-base text-muted-foreground leading-relaxed">
            Standard operating procedures, REST API integration contracts, and architectural data-flow blueprints.
          </p>

          {/* Docs Tab Selector */}
          <div className="mt-8 flex items-center justify-center gap-2 p-1 rounded-lg glass-panel font-mono text-xs">
            <button
              onClick={() => setActiveTab("quickstart")}
              className={`px-4 py-2 rounded transition-all flex items-center gap-2 ${
                activeTab === "quickstart"
                  ? "bg-emerald-600 text-white font-semibold"
                  : "text-muted-foreground hover:text-white"
              }`}
            >
              <Terminal className="w-3.5 h-3.5" />
              <span>Quickstart &amp; Ingestion</span>
            </button>

            <button
              onClick={() => setActiveTab("api")}
              className={`px-4 py-2 rounded transition-all flex items-center gap-2 ${
                activeTab === "api"
                  ? "bg-emerald-600 text-white font-semibold"
                  : "text-muted-foreground hover:text-white"
              }`}
            >
              <Server className="w-3.5 h-3.5" />
              <span>REST API Endpoints</span>
            </button>

            <button
              onClick={() => setActiveTab("architecture")}
              className={`px-4 py-2 rounded transition-all flex items-center gap-2 ${
                activeTab === "architecture"
                  ? "bg-emerald-600 text-white font-semibold"
                  : "text-muted-foreground hover:text-white"
              }`}
            >
              <BookOpen className="w-3.5 h-3.5" />
              <span>System Blueprint</span>
            </button>
          </div>
        </div>

        {/* Dynamic Docs Container */}
        <div className="glass-panel p-6 sm:p-8 rounded-xl border border-emerald-500/20 relative">
          <div className="hud-corner-tl" />
          <div className="hud-corner-tr" />
          <div className="hud-corner-bl" />
          <div className="hud-corner-br" />

          {/* TAB 1: QUICKSTART */}
          {activeTab === "quickstart" && (
            <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
              <div className="lg:col-span-6 space-y-4">
                <h3 className="text-xl font-bold text-white flex items-center gap-2">
                  <Key className="w-5 h-5 text-emerald-400" />
                  Default Analyst Credentials &amp; Access
                </h3>

                <p className="text-xs text-muted-foreground leading-relaxed">
                  The local environment includes a pre-seeded Lead Flight Analyst account with administrative privileges for inspecting live drone missions.
                </p>

                <div className="p-4 rounded bg-forest-900 border border-emerald-500/20 font-mono text-xs space-y-2">
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">Portal Email:</span>
                    <span className="text-emerald-300 font-semibold">analyst@jatayuv.ai</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">Master Password:</span>
                    <span className="text-white font-semibold">jatayuv2026</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">Default Role:</span>
                    <span className="text-emerald-400 font-semibold">LEAD ANALYST (ADMIN)</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">Direct Link:</span>
                    <a href="/login" className="text-emerald-400 underline">
                      Go to Sign In Portal →
                    </a>
                  </div>
                </div>

                <div className="space-y-2.5 pt-2">
                  <h4 className="text-sm font-semibold text-white font-mono">Supported Drone Imagery Formats:</h4>
                  <div className="grid grid-cols-2 gap-2 font-mono text-xs">
                    <div className="p-2 rounded bg-forest-900/60 border border-emerald-500/10 text-gray-300">
                      • JPEG / JPG (DJI EXIF)
                    </div>
                    <div className="p-2 rounded bg-forest-900/60 border border-emerald-500/10 text-gray-300">
                      • GeoTIFF / TIFF
                    </div>
                    <div className="p-2 rounded bg-forest-900/60 border border-emerald-500/10 text-gray-300">
                      • PNG (8-bit / 16-bit)
                    </div>
                    <div className="p-2 rounded bg-forest-900/60 border border-emerald-500/10 text-gray-300">
                      • DNG RAW Aerial
                    </div>
                  </div>
                </div>
              </div>

              {/* Code Snippet Box */}
              <div className="lg:col-span-6 flex flex-col gap-4">
                <div className="flex items-center justify-between text-xs font-mono text-muted-foreground">
                  <span>PYTHON SDK SAMPLE CODE</span>
                  <button
                    onClick={() => copyCode("python", pythonExample)}
                    className="flex items-center gap-1 text-emerald-400 hover:text-white transition-colors"
                  >
                    {copiedIndex === "python" ? <Check className="w-3.5 h-3.5" /> : <Copy className="w-3.5 h-3.5" />}
                    <span>{copiedIndex === "python" ? "Copied" : "Copy"}</span>
                  </button>
                </div>

                <pre className="p-4 rounded-lg bg-forest-900/90 border border-emerald-500/20 font-mono text-xs text-emerald-200 overflow-x-auto leading-relaxed">
                  <code>{pythonExample}</code>
                </pre>
              </div>
            </div>
          )}

          {/* TAB 2: API SPEC */}
          {activeTab === "api" && (
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <h3 className="text-lg font-bold text-white font-mono">
                  FastAPI REST Endpoints (v1 Core)
                </h3>
                <span className="text-xs font-mono text-emerald-400">Base: /api/v1</span>
              </div>

              <div className="divide-y divide-emerald-500/15 font-mono text-xs">
                <div className="py-2.5 flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                  <div className="flex items-center gap-2">
                    <span className="px-2 py-0.5 rounded bg-emerald-500/20 text-emerald-300 text-[10px] font-bold">
                      POST
                    </span>
                    <span className="text-white font-semibold">/auth/login/json</span>
                  </div>
                  <span className="text-muted-foreground text-right">Generate JWT Bearer token</span>
                </div>

                <div className="py-2.5 flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                  <div className="flex items-center gap-2">
                    <span className="px-2 py-0.5 rounded bg-sky-500/20 text-sky-300 text-[10px] font-bold">
                      GET
                    </span>
                    <span className="text-white font-semibold">/projects</span>
                  </div>
                  <span className="text-muted-foreground text-right">List authenticated user survey missions</span>
                </div>

                <div className="py-2.5 flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                  <div className="flex items-center gap-2">
                    <span className="px-2 py-0.5 rounded bg-emerald-500/20 text-emerald-300 text-[10px] font-bold">
                      POST
                    </span>
                    <span className="text-white font-semibold">/projects/{`{id}`}/images/upload</span>
                  </div>
                  <span className="text-muted-foreground text-right">Multi-image UAV upload &amp; EXIF telemetry parser</span>
                </div>

                <div className="py-2.5 flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                  <div className="flex items-center gap-2">
                    <span className="px-2 py-0.5 rounded bg-emerald-500/20 text-emerald-300 text-[10px] font-bold">
                      POST
                    </span>
                    <span className="text-white font-semibold">/analysis/depth</span>
                  </div>
                  <span className="text-muted-foreground text-right">Trigger Depth Anything V2 monocular elevation</span>
                </div>

                <div className="py-2.5 flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                  <div className="flex items-center gap-2">
                    <span className="px-2 py-0.5 rounded bg-emerald-500/20 text-emerald-300 text-[10px] font-bold">
                      POST
                    </span>
                    <span className="text-white font-semibold">/analysis/segmentation</span>
                  </div>
                  <span className="text-muted-foreground text-right">Trigger SegFormer 8-class land use segmentation</span>
                </div>

                <div className="py-2.5 flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                  <div className="flex items-center gap-2">
                    <span className="px-2 py-0.5 rounded bg-emerald-500/20 text-emerald-300 text-[10px] font-bold">
                      POST
                    </span>
                    <span className="text-white font-semibold">/analysis/damage</span>
                  </div>
                  <span className="text-muted-foreground text-right">Trigger xBD 4-tier humanitarian structural triage</span>
                </div>

                <div className="py-2.5 flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                  <div className="flex items-center gap-2">
                    <span className="px-2 py-0.5 rounded bg-emerald-500/20 text-emerald-300 text-[10px] font-bold">
                      POST
                    </span>
                    <span className="text-white font-semibold">/reconstruction/3d</span>
                  </div>
                  <span className="text-muted-foreground text-right">Trigger Open3D Structure from Motion (.ply / DSM)</span>
                </div>

                <div className="py-2.5 flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                  <div className="flex items-center gap-2">
                    <span className="px-2 py-0.5 rounded bg-sky-500/20 text-sky-300 text-[10px] font-bold">
                      GET
                    </span>
                    <span className="text-white font-semibold">/jobs/{`{id}`}</span>
                  </div>
                  <span className="text-muted-foreground text-right">Poll Celery task status and progress percentage</span>
                </div>
              </div>
            </div>
          )}

          {/* TAB 3: ARCHITECTURE */}
          {activeTab === "architecture" && (
            <div className="space-y-4">
              <h3 className="text-lg font-bold text-white font-mono">
                System Blueprint &amp; Data Pipeline Architecture
              </h3>

              <div className="p-4 rounded-lg bg-forest-900 border border-emerald-500/20 font-mono text-xs text-emerald-300 leading-relaxed overflow-x-auto whitespace-pre">
{`+-------------------------------------------------------------------------+
|                         JATAYUV-AI ARCHITECTURE                         |
+-------------------------------------------------------------------------+

  [UAV / Drone Ingestion]
       │
       ▼ (EXIF & Radiometry)
  [FastAPI REST API / Preprocessor] ───► [Persistent SQLite / PostgreSQL]
       │                                  - Projects, Images, Job History
       │ (Async Task Dispatch)
       ▼
  [Redis Broker] ───► [Celery Worker Pool]
                            │
         ┌──────────────────┼──────────────────┬─────────────────┐
         ▼                  ▼                  ▼                 ▼
   [Depth Anything]    [SegFormer]       [xBD Damage]       [Open3D SfM]
   - Metric Relief     - 8-Class LULC    - 4-Tier Collapse  - Dense Point Cloud
   - OBJ Meshes        - GeoJSON Vector  - Severity Index   - DSM Elevation
         │                  │                  │                 │
         └──────────────────┼──────────────────┴─────────────────┘
                            │ (Binary artifacts cached in /storage)
                            ▼
              [Next.js 14 Cinematic Frontend]
              - WebGL 3D Point Cloud Visualizer (Three.js)
              - Split-screen Damage Assessment Slider
              - Real-time Aerospace Telemetry HUD`}
              </div>
            </div>
          )}
        </div>
      </div>
    </section>
  );
}


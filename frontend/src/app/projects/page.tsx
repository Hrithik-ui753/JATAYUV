"use client";

import React, { useState } from "react";
import Link from "next/link";
import {
  FolderKanban,
  UploadCloud,
  Plus,
  MapPin,
  Camera,
  Calendar,
  ArrowRight,
  Search,
  Filter,
} from "lucide-react";
import { Button } from "@/components/ui/Button";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/Card";

export default function ProjectsPage() {
  const [searchQuery, setSearchQuery] = useState("");

  const projects = [
    {
      id: "proj-01",
      name: "Coastal Sector 4 Post-Storm Survey",
      description: "Drone photogrammetry and damage assessment after Cyclone Hudhud landfall.",
      location: "Bhubaneswar Coastal Region",
      imageCount: 148,
      status: "completed",
      lastUpdated: "2026-11-02 18:30",
    },
    {
      id: "proj-02",
      name: "Urban Highway Corridor Expansion",
      description: "Corridor mapping and land-cover segmentation for high-speed expressway planning.",
      location: "Hyderabad Outer Ring Road",
      imageCount: 84,
      status: "processing",
      lastUpdated: "2026-11-03 09:15",
    },
    {
      id: "proj-03",
      name: "Mountain Valley Seismic Faultline Pass",
      description: "LiDAR and aerial stereo surveying of active fault line rupture zone.",
      location: "Uttarakhand Foothills",
      imageCount: 312,
      status: "completed",
      lastUpdated: "2026-11-01 14:10",
    },
  ];

  const filtered = projects.filter(
    (p) =>
      p.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      p.location.toLowerCase().includes(searchQuery.toLowerCase())
  );

  return (
    <div className="flex flex-col gap-6 p-8 max-w-7xl mx-auto w-full">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-border pb-5">
        <div>
          <h1 className="text-2xl font-bold text-white flex items-center gap-2">
            <FolderKanban className="w-6 h-6 text-primary" /> Survey Projects
          </h1>
          <p className="text-xs text-muted-foreground mt-1">
            Manage your aerial mapping campaigns, image sets, and AI analysis pipelines.
          </p>
        </div>

        <Button variant="primary" size="md">
          <Plus className="w-4 h-4 mr-1.5" /> Create New Mission
        </Button>
      </div>

      {/* Filter and Search Bar */}
      <div className="flex items-center gap-3">
        <div className="relative flex-1">
          <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground" />
          <input
            type="text"
            placeholder="Search missions by name or geographic region..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full pl-9 pr-4 py-2 bg-secondary/50 border border-border rounded-lg text-sm text-white placeholder:text-muted-foreground focus:outline-none focus:ring-1 focus:ring-primary"
          />
        </div>
      </div>

      {/* Projects Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
        {filtered.map((proj) => (
          <Card key={proj.id} className="hover:border-primary/40 transition-colors flex flex-col justify-between">
            <CardHeader className="pb-3">
              <div className="flex items-center justify-between">
                <span className="text-[11px] font-semibold uppercase px-2 py-0.5 rounded bg-primary/10 text-primary border border-primary/20">
                  {proj.status}
                </span>
                <span className="text-xs text-muted-foreground">{proj.lastUpdated}</span>
              </div>
              <CardTitle className="text-base mt-2 text-white">
                <Link href={`/projects/${proj.id}`} className="hover:text-primary transition-colors">
                  {proj.name}
                </Link>
              </CardTitle>
              <CardDescription className="line-clamp-2 text-xs">
                {proj.description}
              </CardDescription>
            </CardHeader>

            <CardContent className="pt-0 flex flex-col gap-3">
              <div className="flex flex-col gap-1.5 text-xs text-muted-foreground border-t border-border pt-3">
                <div className="flex items-center gap-1.5">
                  <MapPin className="w-3.5 h-3.5 text-primary" />
                  <span className="truncate">{proj.location}</span>
                </div>
                <div className="flex items-center gap-1.5">
                  <Camera className="w-3.5 h-3.5 text-primary" />
                  <span>{proj.imageCount} Geotagged Aerial Frames</span>
                </div>
              </div>

              <Link href={`/projects/${proj.id}`}>
                <Button size="sm" variant="outline" className="w-full justify-between">
                  Open Mission Workspace <ArrowRight className="w-3.5 h-3.5" />
                </Button>
              </Link>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
}

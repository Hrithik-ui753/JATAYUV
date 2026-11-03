"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import {
  FolderKanban,
  UploadCloud,
  Plus,
  MapPin,
  Calendar,
  ArrowRight,
  Search,
  Trash2,
  RefreshCw,
  Box,
  Compass
} from "lucide-react";
import { Button } from "@/components/ui/Button";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { api } from "@/lib/api";
import { Project } from "@/types";

export default function ProjectsPage() {
  const [searchQuery, setSearchQuery] = useState("");
  const [projects, setProjects] = useState<Project[]>([]);
  const [loading, setLoading] = useState(true);
  const [showModal, setShowModal] = useState(false);
  const [newProject, setNewProject] = useState({
    name: "",
    location_name: "",
    description: "",
    center_lat: 20.316,
    center_lon: 86.611,
  });

  const loadProjects = async () => {
    try {
      setLoading(true);
      const list = await api.getProjects();
      setProjects(list);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadProjects();
  }, []);

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newProject.name) return;
    try {
      const created = await api.createProject(newProject);
      setProjects([created, ...projects]);
      setShowModal(false);
      setNewProject({ name: "", location_name: "", description: "", center_lat: 20.316, center_lon: 86.611 });
    } catch (err: any) {
      alert("Error creating project: " + err.message);
    }
  };

  const handleDelete = async (id: string) => {
    if (!confirm("Permanently delete this aerial survey mission?")) return;
    try {
      await api.deleteProject(id);
      setProjects(projects.filter((p) => p.id !== id));
    } catch (err: any) {
      alert("Error deleting: " + err.message);
    }
  };

  const filtered = projects.filter(
    (p) =>
      p.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      p.location_name.toLowerCase().includes(searchQuery.toLowerCase())
  );

  return (
    <div className="flex-1 flex flex-col p-6 sm:p-8 max-w-7xl mx-auto w-full gap-6 font-mono">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-emerald-500/20 pb-5">
        <div>
          <h1 className="text-2xl font-bold text-white flex items-center gap-2">
            <FolderKanban className="w-6 h-6 text-emerald-400" />
            Aerial Survey Missions
          </h1>
          <p className="text-xs text-muted-foreground mt-1">
            Connected to real SQLite/PostgreSQL geospatial database.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <Link href="/dashboard">
            <Button variant="outline" size="sm">
              <Compass className="w-4 h-4 mr-1.5" /> Mission Control Dashboard
            </Button>
          </Link>
          <Button onClick={() => setShowModal(true)} variant="primary" size="sm">
            <Plus className="w-4 h-4 mr-1.5" /> New Mission
          </Button>
        </div>
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
            className="w-full pl-9 pr-4 py-2 bg-forest-900 border border-emerald-500/30 rounded-lg text-xs text-white placeholder:text-muted-foreground focus:outline-none focus:border-emerald-400"
          />
        </div>
        <Button onClick={loadProjects} variant="outline" size="sm" className="h-9 px-3">
          <RefreshCw className="w-4 h-4" />
        </Button>
      </div>

      {/* Projects Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
        {filtered.map((proj) => (
          <div
            key={proj.id}
            className="glass-panel p-5 rounded-lg border border-emerald-500/20 hover:border-emerald-500/40 transition-all flex flex-col justify-between"
          >
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <Badge variant="tactical">
                  {proj.image_count} CAPTURES
                </Badge>
                <span className="text-[10px] text-muted-foreground">
                  {new Date(proj.created_at).toLocaleDateString()}
                </span>
              </div>

              <h2 className="text-base font-bold text-white leading-tight">
                {proj.name}
              </h2>

              <p className="text-xs text-muted-foreground line-clamp-2">
                {proj.description}
              </p>

              <div className="flex items-center gap-1.5 text-xs text-emerald-300">
                <MapPin className="w-3.5 h-3.5 text-emerald-400 shrink-0" />
                <span className="truncate">{proj.location_name}</span>
              </div>
            </div>

            <div className="pt-4 mt-3 border-t border-emerald-500/15 flex items-center justify-between gap-2">
              <Link href={`/projects/${proj.id}`} className="flex-1">
                <Button variant="primary" size="sm" className="w-full text-xs">
                  Open 3D Workspace <ArrowRight className="w-3.5 h-3.5 ml-1" />
                </Button>
              </Link>

              <button
                onClick={() => handleDelete(proj.id)}
                title="Delete Mission"
                className="p-1.5 rounded hover:bg-rose-950 text-rose-400 hover:text-rose-200 transition-colors"
              >
                <Trash2 className="w-4 h-4" />
              </button>
            </div>
          </div>
        ))}
      </div>

      {/* CREATE MODAL */}
      {showModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm">
          <div className="glass-panel w-full max-w-lg p-6 rounded-xl border border-emerald-500/40 shadow-2xl relative font-mono text-xs">
            <h3 className="text-base font-bold text-white mb-1">
              Initialize New Aerial Mission
            </h3>
            <p className="text-muted-foreground text-[11px] mb-4">
              Register survey boundaries and camera profile.
            </p>

            <form onSubmit={handleCreate} className="space-y-3.5">
              <div>
                <label className="text-white block mb-1">Mission Name *</label>
                <input
                  type="text"
                  required
                  placeholder="e.g. Mission Brahmaputra: Flood Breach"
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
                  placeholder="e.g. Kaziranga Corridor"
                  value={newProject.location_name}
                  onChange={(e) => setNewProject({ ...newProject, location_name: e.target.value })}
                  className="w-full bg-forest-950 border border-emerald-500/30 rounded p-2 text-white focus:outline-none"
                />
              </div>

              <div>
                <label className="text-white block mb-1">Description</label>
                <textarea
                  rows={2}
                  placeholder="Survey objectives and flight law notes..."
                  value={newProject.description}
                  onChange={(e) => setNewProject({ ...newProject, description: e.target.value })}
                  className="w-full bg-forest-950 border border-emerald-500/30 rounded p-2 text-white focus:outline-none"
                />
              </div>

              <div className="pt-3 flex items-center justify-end gap-2 border-t border-emerald-500/20">
                <Button
                  type="button"
                  variant="outline"
                  size="sm"
                  onClick={() => setShowModal(false)}
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

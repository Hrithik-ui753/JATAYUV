"use client";

import React, { useRef, useEffect, useState } from "react";
import * as THREE from "three";
import { cn } from "@/lib/utils";
import { Box, Eye, RotateCw, ZoomIn, Layers } from "lucide-react";
import { Button } from "@/components/ui/Button";

interface PointCloudViewerProps {
  plyUrl?: string;
  numPoints?: number;
  className?: string;
}

export function PointCloudViewer({
  plyUrl,
  numPoints = 25000,
  className,
}: PointCloudViewerProps) {
  const mountRef = useRef<HTMLDivElement>(null);
  const [pointSize, setPointSize] = useState<number>(0.05);
  const [colorMode, setColorMode] = useState<"elevation" | "rgb" | "intensity">("elevation");
  const [isRotating, setIsRotating] = useState<boolean>(true);

  const sceneRef = useRef<THREE.Scene | null>(null);
  const rendererRef = useRef<THREE.WebGLRenderer | null>(null);
  const pointsMeshRef = useRef<THREE.Points | null>(null);

  useEffect(() => {
    if (!mountRef.current) return;

    // Dimensions
    const width = mountRef.current.clientWidth;
    const height = mountRef.current.clientHeight || 450;

    // Scene & Camera
    const scene = new THREE.Scene();
    sceneRef.current = scene;
    scene.background = new THREE.Color(0x0a0f1d);

    const camera = new THREE.PerspectiveCamera(60, width / height, 0.1, 1000);
    camera.position.set(0, 15, 25);
    camera.lookAt(0, 0, 0);

    // Renderer
    const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
    rendererRef.current = renderer;
    renderer.setSize(width, height);
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    mountRef.current.appendChild(renderer.domElement);

    // Grid & Axes
    const grid = new THREE.GridHelper(30, 30, 0x0284c7, 0x1e293b);
    scene.add(grid);

    // Generate Aerial Terrain Point Cloud
    const count = numPoints;
    const geometry = new THREE.BufferGeometry();
    const positions = new Float32Array(count * 3);
    const colors = new Float32Array(count * 3);

    const colorHelper = new THREE.Color();
    const terrainExtent = 20;

    for (let i = 0; i < count; i++) {
      // Spatial distribution simulating aerial drone photogrammetry over buildings and terrain
      const x = (Math.random() - 0.5) * terrainExtent;
      const z = (Math.random() - 0.5) * terrainExtent;

      // Realistic terrain elevations with structures/hills
      const hill = Math.sin(x * 0.3) * Math.cos(z * 0.3) * 2.5;
      const building1 = (Math.abs(x - 3) < 3 && Math.abs(z - 2) < 3) ? 4.5 : 0;
      const building2 = (Math.abs(x + 4) < 2.5 && Math.abs(z + 3) < 2.5) ? 6.0 : 0;
      const y = Math.max(0, hill + building1 + building2 + (Math.random() - 0.5) * 0.2);

      positions[i * 3] = x;
      positions[i * 3 + 1] = y;
      positions[i * 3 + 2] = z;

      // Elevation based coloring (Hypsometric tint: blue -> green -> yellow -> red)
      const normY = Math.min(1, Math.max(0, y / 7.0));
      colorHelper.setHSL((1.0 - normY) * 0.65, 0.9, 0.5);

      colors[i * 3] = colorHelper.r;
      colors[i * 3 + 1] = colorHelper.g;
      colors[i * 3 + 2] = colorHelper.b;
    }

    geometry.setAttribute("position", new THREE.BufferAttribute(positions, 3));
    geometry.setAttribute("color", new THREE.BufferAttribute(colors, 3));

    const material = new THREE.PointsMaterial({
      size: pointSize,
      vertexColors: true,
      sizeAttenuation: true,
    });

    const pointsMesh = new THREE.Points(geometry, material);
    pointsMeshRef.current = pointsMesh;
    scene.add(pointsMesh);

    // Interactive Orbit Drag Controls
    let isDragging = false;
    let prevMouseX = 0;
    let prevMouseY = 0;

    const onMouseDown = (e: MouseEvent) => {
      isDragging = true;
      prevMouseX = e.clientX;
      prevMouseY = e.clientY;
    };

    const onMouseMove = (e: MouseEvent) => {
      if (!isDragging || !pointsMeshRef.current) return;
      const deltaX = e.clientX - prevMouseX;
      const deltaY = e.clientY - prevMouseY;

      pointsMeshRef.current.rotation.y += deltaX * 0.008;
      camera.position.y = Math.max(2, Math.min(40, camera.position.y - deltaY * 0.05));
      camera.lookAt(0, 0, 0);

      prevMouseX = e.clientX;
      prevMouseY = e.clientY;
    };

    const onMouseUp = () => {
      isDragging = false;
    };

    const onWheel = (e: WheelEvent) => {
      camera.position.z = Math.max(5, Math.min(60, camera.position.z + e.deltaY * 0.02));
      camera.lookAt(0, 0, 0);
    };

    const domElement = renderer.domElement;
    domElement.addEventListener("mousedown", onMouseDown);
    window.addEventListener("mousemove", onMouseMove);
    window.addEventListener("mouseup", onMouseUp);
    domElement.addEventListener("wheel", onWheel);

    // Animation Loop
    let animationFrameId: number;
    const animate = () => {
      animationFrameId = requestAnimationFrame(animate);

      if (isRotating && pointsMeshRef.current && !isDragging) {
        pointsMeshRef.current.rotation.y += 0.002;
      }

      renderer.render(scene, camera);
    };
    animate();

    // Resize Handler
    const handleResize = () => {
      if (!mountRef.current || !renderer) return;
      const newWidth = mountRef.current.clientWidth;
      const newHeight = mountRef.current.clientHeight || 450;
      camera.aspect = newWidth / newHeight;
      camera.updateProjectionMatrix();
      renderer.setSize(newWidth, newHeight);
    };
    window.addEventListener("resize", handleResize);

    return () => {
      cancelAnimationFrame(animationFrameId);
      domElement.removeEventListener("mousedown", onMouseDown);
      window.removeEventListener("mousemove", onMouseMove);
      window.removeEventListener("mouseup", onMouseUp);
      domElement.removeEventListener("wheel", onWheel);
      window.removeEventListener("resize", handleResize);
      if (mountRef.current && renderer.domElement) {
        mountRef.current.removeChild(renderer.domElement);
      }
      geometry.dispose();
      material.dispose();
      renderer.dispose();
    };
  }, []);

  // Update Point Size dynamically
  useEffect(() => {
    if (pointsMeshRef.current) {
      const mat = pointsMeshRef.current.material as THREE.PointsMaterial;
      mat.size = pointSize;
    }
  }, [pointSize]);

  return (
    <div className={cn("flex flex-col gap-3 rounded-xl border border-border bg-card p-4", className)}>
      <div className="flex flex-wrap items-center justify-between gap-3 border-b border-border pb-3">
        <div className="flex items-center gap-2">
          <Box className="w-4 h-4 text-primary" />
          <span className="font-semibold text-white text-sm">3D Photogrammetry Point Cloud</span>
          <span className="px-2 py-0.5 rounded-full bg-primary/10 text-primary border border-primary/20 text-xs">
            {numPoints.toLocaleString()} points
          </span>
        </div>

        <div className="flex items-center gap-3 text-xs text-muted-foreground">
          <button
            onClick={() => setIsRotating(!isRotating)}
            className="flex items-center gap-1 px-2.5 py-1 rounded bg-secondary hover:bg-secondary/80 text-white border border-border"
          >
            <RotateCw className={cn("w-3.5 h-3.5", isRotating && "animate-spin")} />
            {isRotating ? "Auto Orbit" : "Paused"}
          </button>

          <div className="flex items-center gap-1.5">
            <span>Point Size:</span>
            <input
              type="range"
              min="0.02"
              max="0.20"
              step="0.01"
              value={pointSize}
              onChange={(e) => setPointSize(parseFloat(e.target.value))}
              className="w-20 accent-primary h-1.5 bg-secondary rounded appearance-none cursor-pointer"
            />
          </div>
        </div>
      </div>

      {/* 3D WebGL Canvas */}
      <div
        ref={mountRef}
        className="w-full h-[450px] rounded-lg overflow-hidden relative cursor-grab active:cursor-grabbing border border-border"
      >
        <div className="absolute top-3 left-3 flex flex-col gap-1 p-2 rounded bg-black/70 backdrop-blur border border-white/10 text-[11px] text-white pointer-events-none">
          <div className="flex items-center gap-1.5 font-medium text-primary">
            <ZoomIn className="w-3.5 h-3.5" /> Navigation Controls
          </div>
          <span className="text-muted-foreground">Left Drag: Orbit Rotation</span>
          <span className="text-muted-foreground">Scroll Wheel: Zoom In / Out</span>
        </div>

        {/* Hypsometric Elevation Legend */}
        <div className="absolute bottom-3 right-3 p-2 rounded bg-black/80 backdrop-blur border border-white/10 text-[10px] text-white">
          <div className="font-medium text-muted-foreground mb-1">Elevation (Z-axis)</div>
          <div className="h-2 w-28 rounded bg-gradient-to-r from-blue-500 via-emerald-400 to-rose-500" />
          <div className="flex justify-between text-muted-foreground mt-0.5">
            <span>Low (0m)</span>
            <span>High (7m+)</span>
          </div>
        </div>
      </div>
    </div>
  );
}


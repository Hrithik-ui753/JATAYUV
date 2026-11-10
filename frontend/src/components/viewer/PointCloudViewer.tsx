"use client";

<<<<<<< HEAD
import React, { useCallback, useEffect, useRef, useState } from "react";
=======
<<<<<<< HEAD
import React, { useRef, useEffect, useState } from "react";
>>>>>>> origin/main
import * as THREE from "three";
import { cn } from "@/lib/utils";
import { Box, RotateCw, ZoomIn, AlertTriangle, Loader2, RefreshCw } from "lucide-react";
import {
  EMPTY_RECONSTRUCTION_MESSAGE,
  isUsablePointCloud,
  resolveViewerState,
} from "@/lib/integrity.mjs";

interface PointCloudViewerProps {
  /** Verified PLY point cloud produced by a real reconstruction. */
  plyUrl?: string;
  className?: string;
}

type ViewerStatus = "empty" | "loading" | "ready" | "error";

/** Fetch real PLY bytes and parse them with Three.js PLYLoader. */
async function fetchPlyGeometry(url: string): Promise<THREE.BufferGeometry> {
  const response = await fetch(url, { cache: "no-store" });
  if (!response.ok) {
    throw new Error(`Could not load point cloud (HTTP ${response.status} ${response.statusText}).`);
  }
  const buffer = await response.arrayBuffer();
  if (buffer.byteLength === 0) {
    throw new Error("Point cloud artifact is empty (0 bytes).");
  }
  const { PLYLoader } = await import("three/examples/jsm/loaders/PLYLoader.js");
  const geometry = new PLYLoader().parse(buffer);
  if (!isUsablePointCloud(geometry)) {
    geometry.dispose();
    throw new Error(
      "PLY file contains no finite vertices; the artifact is empty or corrupt."
    );
  }
  geometry.computeBoundingBox();
  geometry.computeVertexNormals();
  return geometry;
}

export function PointCloudViewer({ plyUrl, className }: PointCloudViewerProps) {
  const mountRef = useRef<HTMLDivElement>(null);
  const [pointSize, setPointSize] = useState<number>(0.05);
  const [colorMode, setColorMode] = useState<"elevation" | "rgb">("elevation");
  const [isRotating, setIsRotating] = useState<boolean>(true);
  const [status, setStatus] = useState<ViewerStatus>("empty");
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [pointCount, setPointCount] = useState<number>(0);
  const [hasVertexColors, setHasVertexColors] = useState<boolean>(false);
  const [reloadKey, setReloadKey] = useState(0);

  const rendererRef = useRef<THREE.WebGLRenderer | null>(null);
  const pointsMeshRef = useRef<THREE.Points | null>(null);
  const materialRef = useRef<THREE.PointsMaterial | null>(null);
  const elevationColorsRef = useRef<Float32Array | null>(null);
  const sourceColorsRef = useRef<Float32Array | null>(null);
  const rotatingRef = useRef(isRotating);

  const resolved = resolveViewerState({ plyUrl });

  useEffect(() => {
    rotatingRef.current = isRotating;
  }, [isRotating]);

  useEffect(() => {
    if (resolved.status === "empty" || resolved.status === "error") {
      setStatus(resolved.status === "empty" ? "empty" : "error");
      setErrorMessage(resolved.status === "error" ? resolved.message ?? "Invalid artifact URL." : null);
      return;
    }
    if (!plyUrl) return;
    const mount = mountRef.current;
    if (!mount) return;

    let cancelled = false;
    setStatus("loading");
    setErrorMessage(null);
    setPointCount(0);

    const width = mount.clientWidth || 640;
    const height = mount.clientHeight || 450;

    const scene = new THREE.Scene();
    scene.background = new THREE.Color(0x0a0f1d);

    const camera = new THREE.PerspectiveCamera(60, width / height, 0.01, 10000);
    camera.position.set(0, 15, 25);

    const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
    renderer.setSize(width, height);
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    mount.appendChild(renderer.domElement);
    rendererRef.current = renderer;

    scene.add(new THREE.AmbientLight(0xffffff, 1.5));
    const light = new THREE.DirectionalLight(0xffffff, 1.5);
    light.position.set(10, 20, 15);
    scene.add(light);

    let grid: THREE.GridHelper | null = null;
    let geometry: THREE.BufferGeometry | null = null;

    let lastX = 0;
    let lastY = 0;
    const onPointerDown = (event: MouseEvent) => {
      lastX = event.clientX;
      lastY = event.clientY;
    };
    const onPointerMove = (event: MouseEvent) => {
      if (event.buttons !== 1 || !pointsMeshRef.current) return;
      pointsMeshRef.current.rotation.y += (event.clientX - lastX) * 0.008;
      camera.position.y = Math.max(0.1, camera.position.y - (event.clientY - lastY) * 0.05);
      camera.lookAt(0, 0, 0);
      lastX = event.clientX;
      lastY = event.clientY;
    };
<<<<<<< HEAD
    const onWheel = (event: WheelEvent) => {
      event.preventDefault();
      camera.position.z = Math.max(0.5, camera.position.z + event.deltaY * 0.02);
=======

    const onMouseUp = () => {
      isDragging = false;
    };

    const onWheel = (e: WheelEvent) => {
      camera.position.z = Math.max(5, Math.min(60, camera.position.z + e.deltaY * 0.02));
=======
import React, { useCallback, useEffect, useRef, useState } from "react";
import * as THREE from "three";
import { cn } from "@/lib/utils";
import { Box, RotateCw, ZoomIn, AlertTriangle, Loader2, RefreshCw } from "lucide-react";
import {
  EMPTY_RECONSTRUCTION_MESSAGE,
  isUsablePointCloud,
  resolveViewerState,
} from "@/lib/integrity.mjs";

interface PointCloudViewerProps {
  /** Verified PLY point cloud produced by a real reconstruction. */
  plyUrl?: string;
  className?: string;
}

type ViewerStatus = "empty" | "loading" | "ready" | "error";

/** Fetch real PLY bytes and parse them with Three.js PLYLoader. */
async function fetchPlyGeometry(url: string): Promise<THREE.BufferGeometry> {
  const response = await fetch(url, { cache: "no-store" });
  if (!response.ok) {
    throw new Error(`Could not load point cloud (HTTP ${response.status} ${response.statusText}).`);
  }
  const buffer = await response.arrayBuffer();
  if (buffer.byteLength === 0) {
    throw new Error("Point cloud artifact is empty (0 bytes).");
  }
  const { PLYLoader } = await import("three/examples/jsm/loaders/PLYLoader.js");
  const geometry = new PLYLoader().parse(buffer);
  if (!isUsablePointCloud(geometry)) {
    geometry.dispose();
    throw new Error(
      "PLY file contains no finite vertices; the artifact is empty or corrupt."
    );
  }
  geometry.computeBoundingBox();
  geometry.computeVertexNormals();
  return geometry;
}

export function PointCloudViewer({ plyUrl, className }: PointCloudViewerProps) {
  const mountRef = useRef<HTMLDivElement>(null);
  const [pointSize, setPointSize] = useState<number>(0.05);
  const [colorMode, setColorMode] = useState<"elevation" | "rgb">("elevation");
  const [isRotating, setIsRotating] = useState<boolean>(true);
  const [status, setStatus] = useState<ViewerStatus>("empty");
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [pointCount, setPointCount] = useState<number>(0);
  const [hasVertexColors, setHasVertexColors] = useState<boolean>(false);
  const [reloadKey, setReloadKey] = useState(0);

  const rendererRef = useRef<THREE.WebGLRenderer | null>(null);
  const pointsMeshRef = useRef<THREE.Points | null>(null);
  const materialRef = useRef<THREE.PointsMaterial | null>(null);
  const elevationColorsRef = useRef<Float32Array | null>(null);
  const sourceColorsRef = useRef<Float32Array | null>(null);
  const rotatingRef = useRef(isRotating);

  const resolved = resolveViewerState({ plyUrl });

  useEffect(() => {
    rotatingRef.current = isRotating;
  }, [isRotating]);

  useEffect(() => {
    if (resolved.status === "empty" || resolved.status === "error") {
      setStatus(resolved.status === "empty" ? "empty" : "error");
      setErrorMessage(resolved.status === "error" ? resolved.message ?? "Invalid artifact URL." : null);
      return;
    }
    if (!plyUrl) return;
    const mount = mountRef.current;
    if (!mount) return;

    let cancelled = false;
    setStatus("loading");
    setErrorMessage(null);
    setPointCount(0);

    const width = mount.clientWidth || 640;
    const height = mount.clientHeight || 450;

    const scene = new THREE.Scene();
    scene.background = new THREE.Color(0x0a0f1d);

    const camera = new THREE.PerspectiveCamera(60, width / height, 0.01, 10000);
    camera.position.set(0, 15, 25);

    const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
    renderer.setSize(width, height);
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    mount.appendChild(renderer.domElement);
    rendererRef.current = renderer;

    scene.add(new THREE.AmbientLight(0xffffff, 1.5));
    const light = new THREE.DirectionalLight(0xffffff, 1.5);
    light.position.set(10, 20, 15);
    scene.add(light);

    let grid: THREE.GridHelper | null = null;
    let geometry: THREE.BufferGeometry | null = null;

    let lastX = 0;
    let lastY = 0;
    const onPointerDown = (event: MouseEvent) => {
      lastX = event.clientX;
      lastY = event.clientY;
    };
    const onPointerMove = (event: MouseEvent) => {
      if (event.buttons !== 1 || !pointsMeshRef.current) return;
      pointsMeshRef.current.rotation.y += (event.clientX - lastX) * 0.008;
      camera.position.y = Math.max(0.1, camera.position.y - (event.clientY - lastY) * 0.05);
      camera.lookAt(0, 0, 0);
      lastX = event.clientX;
      lastY = event.clientY;
    };
    const onWheel = (event: WheelEvent) => {
      event.preventDefault();
      camera.position.z = Math.max(0.5, camera.position.z + event.deltaY * 0.02);
>>>>>>> 0400f2f (p5-udpated)
>>>>>>> origin/main
      camera.lookAt(0, 0, 0);
    };

    const domElement = renderer.domElement;
<<<<<<< HEAD
    domElement.addEventListener("mousedown", onPointerDown);
    domElement.addEventListener("mousemove", onPointerMove);
    domElement.addEventListener("wheel", onWheel, { passive: false });
=======
<<<<<<< HEAD
    domElement.addEventListener("mousedown", onMouseDown);
    window.addEventListener("mousemove", onMouseMove);
    window.addEventListener("mouseup", onMouseUp);
    domElement.addEventListener("wheel", onWheel);
>>>>>>> origin/main

    let animationFrameId = 0;
    const animate = () => {
      animationFrameId = requestAnimationFrame(animate);
      if (rotatingRef.current && pointsMeshRef.current) {
        pointsMeshRef.current.rotation.y += 0.002;
      }
<<<<<<< HEAD
=======

=======
    domElement.addEventListener("mousedown", onPointerDown);
    domElement.addEventListener("mousemove", onPointerMove);
    domElement.addEventListener("wheel", onWheel, { passive: false });

    let animationFrameId = 0;
    const animate = () => {
      animationFrameId = requestAnimationFrame(animate);
      if (rotatingRef.current && pointsMeshRef.current) {
        pointsMeshRef.current.rotation.y += 0.002;
      }
>>>>>>> 0400f2f (p5-udpated)
>>>>>>> origin/main
      renderer.render(scene, camera);
    };
    animate();

<<<<<<< HEAD
    const handleResize = () => {
      if (!mount) return;
      const newWidth = mount.clientWidth || 1;
      const newHeight = mount.clientHeight || 450;
=======
<<<<<<< HEAD
    // Resize Handler
    const handleResize = () => {
      if (!mountRef.current || !renderer) return;
      const newWidth = mountRef.current.clientWidth;
      const newHeight = mountRef.current.clientHeight || 450;
=======
    const handleResize = () => {
      if (!mount) return;
      const newWidth = mount.clientWidth || 1;
      const newHeight = mount.clientHeight || 450;
>>>>>>> 0400f2f (p5-udpated)
>>>>>>> origin/main
      camera.aspect = newWidth / newHeight;
      camera.updateProjectionMatrix();
      renderer.setSize(newWidth, newHeight);
    };
    window.addEventListener("resize", handleResize);

<<<<<<< HEAD
    const load = async () => {
      const geo = await fetchPlyGeometry(plyUrl);
      if (cancelled) {
        geo.dispose();
        return;
      }
      geometry = geo;

      const box = geo.boundingBox ?? new THREE.Box3().setFromBufferAttribute(
        geo.getAttribute("position") as THREE.BufferAttribute
      );
      const center = box.getCenter(new THREE.Vector3());
      const size = box.getSize(new THREE.Vector3());
      const maxDimension = Math.max(size.x, size.y, size.z) || 1;

      // Centre the real cloud at the origin and frame it with the real extents.
      geo.translate(-center.x, -center.y, -center.z);

      const position = geo.getAttribute("position");
      const spanY = Math.max(1e-6, size.y);
      const minY = box.min.y;
      const elevationColors = new Float32Array(position.count * 3);
      for (let i = 0; i < position.count; i++) {
        const t = THREE.MathUtils.clamp((position.getY(i) + center.y - minY) / spanY, 0, 1);
        const color = new THREE.Color().setHSL((1.0 - t) * 0.65, 0.9, 0.5);
        elevationColors[i * 3] = color.r;
        elevationColors[i * 3 + 1] = color.g;
        elevationColors[i * 3 + 2] = color.b;
      }
      elevationColorsRef.current = elevationColors;

      const sourceColorAttr = geo.getAttribute("color");
      const stored = sourceColorAttr ? new Float32Array(sourceColorAttr.array as ArrayLike<number>) : null;
      sourceColorsRef.current = stored;
      setHasVertexColors(Boolean(stored));

      geo.setAttribute("color", new THREE.BufferAttribute(elevationColors, 3));
      geo.computeBoundingSphere();

      const material = new THREE.PointsMaterial({
        size: Math.max(maxDimension * 0.004, 0.005),
        vertexColors: true,
        sizeAttenuation: true,
      });
      materialRef.current = material;
      setPointSize(Math.max(maxDimension * 0.004, 0.005));

      const points = new THREE.Points(geo, material);
      pointsMeshRef.current = points;
      scene.add(points);

      grid = new THREE.GridHelper(maxDimension * 1.4, 20, 0x0284c7, 0x1e293b);
      grid.position.y = -size.y / 2;
      scene.add(grid);

      const distance = maxDimension * 1.4;
      camera.position.set(distance * 0.4, distance * 0.6, distance);
      camera.near = Math.max(0.001, maxDimension / 1000);
      camera.far = Math.max(100, maxDimension * 100);
      camera.updateProjectionMatrix();
      camera.lookAt(0, 0, 0);

      setPointCount(position.count);
      setStatus("ready");
    };

    load().catch((error: unknown) => {
      if (cancelled) return;
      setErrorMessage(error instanceof Error ? error.message : String(error));
      setStatus("error");
    });

=======
<<<<<<< HEAD
>>>>>>> origin/main
    return () => {
      cancelled = true;
      cancelAnimationFrame(animationFrameId);
      domElement.removeEventListener("mousedown", onPointerDown);
      domElement.removeEventListener("mousemove", onPointerMove);
      domElement.removeEventListener("wheel", onWheel);
      window.removeEventListener("resize", handleResize);
      if (geometry) geometry.dispose();
      if (materialRef.current) materialRef.current.dispose();
      if (grid) {
        grid.geometry.dispose();
        (grid.material as THREE.Material).dispose();
      }
      if (mount.contains(renderer.domElement)) {
        mount.removeChild(renderer.domElement);
      }
      renderer.dispose();
      pointsMeshRef.current = null;
      materialRef.current = null;
      rendererRef.current = null;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [plyUrl, reloadKey]);

  useEffect(() => {
    if (materialRef.current) materialRef.current.size = pointSize;
  }, [pointSize]);

<<<<<<< HEAD
=======
=======
    const load = async () => {
      const geo = await fetchPlyGeometry(plyUrl);
      if (cancelled) {
        geo.dispose();
        return;
      }
      geometry = geo;

      const box = geo.boundingBox ?? new THREE.Box3().setFromBufferAttribute(
        geo.getAttribute("position") as THREE.BufferAttribute
      );
      const center = box.getCenter(new THREE.Vector3());
      const size = box.getSize(new THREE.Vector3());
      const maxDimension = Math.max(size.x, size.y, size.z) || 1;

      // Centre the real cloud at the origin and frame it with the real extents.
      geo.translate(-center.x, -center.y, -center.z);

      const position = geo.getAttribute("position");
      const spanY = Math.max(1e-6, size.y);
      const minY = box.min.y;
      const elevationColors = new Float32Array(position.count * 3);
      for (let i = 0; i < position.count; i++) {
        const t = THREE.MathUtils.clamp((position.getY(i) + center.y - minY) / spanY, 0, 1);
        const color = new THREE.Color().setHSL((1.0 - t) * 0.65, 0.9, 0.5);
        elevationColors[i * 3] = color.r;
        elevationColors[i * 3 + 1] = color.g;
        elevationColors[i * 3 + 2] = color.b;
      }
      elevationColorsRef.current = elevationColors;

      const sourceColorAttr = geo.getAttribute("color");
      const stored = sourceColorAttr ? new Float32Array(sourceColorAttr.array as ArrayLike<number>) : null;
      sourceColorsRef.current = stored;
      setHasVertexColors(Boolean(stored));

      geo.setAttribute("color", new THREE.BufferAttribute(elevationColors, 3));
      geo.computeBoundingSphere();

      const material = new THREE.PointsMaterial({
        size: Math.max(maxDimension * 0.004, 0.005),
        vertexColors: true,
        sizeAttenuation: true,
      });
      materialRef.current = material;
      setPointSize(Math.max(maxDimension * 0.004, 0.005));

      const points = new THREE.Points(geo, material);
      pointsMeshRef.current = points;
      scene.add(points);

      grid = new THREE.GridHelper(maxDimension * 1.4, 20, 0x0284c7, 0x1e293b);
      grid.position.y = -size.y / 2;
      scene.add(grid);

      const distance = maxDimension * 1.4;
      camera.position.set(distance * 0.4, distance * 0.6, distance);
      camera.near = Math.max(0.001, maxDimension / 1000);
      camera.far = Math.max(100, maxDimension * 100);
      camera.updateProjectionMatrix();
      camera.lookAt(0, 0, 0);

      setPointCount(position.count);
      setStatus("ready");
    };

    load().catch((error: unknown) => {
      if (cancelled) return;
      setErrorMessage(error instanceof Error ? error.message : String(error));
      setStatus("error");
    });

    return () => {
      cancelled = true;
      cancelAnimationFrame(animationFrameId);
      domElement.removeEventListener("mousedown", onPointerDown);
      domElement.removeEventListener("mousemove", onPointerMove);
      domElement.removeEventListener("wheel", onWheel);
      window.removeEventListener("resize", handleResize);
      if (geometry) geometry.dispose();
      if (materialRef.current) materialRef.current.dispose();
      if (grid) {
        grid.geometry.dispose();
        (grid.material as THREE.Material).dispose();
      }
      if (mount.contains(renderer.domElement)) {
        mount.removeChild(renderer.domElement);
      }
      renderer.dispose();
      pointsMeshRef.current = null;
      materialRef.current = null;
      rendererRef.current = null;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [plyUrl, reloadKey]);

  useEffect(() => {
    if (materialRef.current) materialRef.current.size = pointSize;
  }, [pointSize]);

>>>>>>> origin/main
  const applyColorMode = useCallback((mode: "elevation" | "rgb") => {
    const points = pointsMeshRef.current;
    if (!points) return;
    const target = mode === "rgb" ? sourceColorsRef.current : elevationColorsRef.current;
    if (!target) return;
    const geometry = points.geometry;
    const colors = new Float32Array(target.length);
    colors.set(target);
    geometry.setAttribute("color", new THREE.BufferAttribute(colors, 3));
    const attribute = geometry.getAttribute("color");
    if (attribute) attribute.needsUpdate = true;
    setColorMode(mode);
  }, []);

<<<<<<< HEAD
=======
>>>>>>> 0400f2f (p5-udpated)
>>>>>>> origin/main
  return (
    <div className={cn("flex flex-col gap-3 rounded-xl border border-border bg-card p-4", className)}>
      <div className="flex flex-wrap items-center justify-between gap-3 border-b border-border pb-3">
        <div className="flex items-center gap-2">
          <Box className="w-4 h-4 text-primary" />
          <span className="font-semibold text-white text-sm">3D Photogrammetry Point Cloud</span>
<<<<<<< HEAD
          {status === "ready" && pointCount > 0 && (
            <span className="px-2 py-0.5 rounded-full bg-primary/10 text-primary border border-primary/20 text-xs">
              {pointCount.toLocaleString()} points
            </span>
          )}
=======
<<<<<<< HEAD
          <span className="px-2 py-0.5 rounded-full bg-primary/10 text-primary border border-primary/20 text-xs">
            {numPoints.toLocaleString()} points
          </span>
>>>>>>> origin/main
        </div>

        {status === "ready" && (
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
                min="0.001"
                max="0.5"
                step="0.001"
                value={pointSize}
                onChange={(event) => setPointSize(parseFloat(event.target.value))}
                className="w-20 accent-primary h-1.5 bg-secondary rounded appearance-none cursor-pointer"
              />
            </div>

            <div className="flex items-center gap-1">
              <button
                onClick={() => applyColorMode("elevation")}
                className={cn(
                  "px-2 py-1 rounded border border-border",
                  colorMode === "elevation" ? "text-primary font-bold" : "text-muted-foreground"
                )}
              >
                ELEV
              </button>
              <button
                onClick={() => applyColorMode("rgb")}
                disabled={!hasVertexColors}
                title={hasVertexColors ? "Colours stored in the PLY" : "This PLY carries no vertex colours"}
                className={cn(
                  "px-2 py-1 rounded border border-border disabled:opacity-30",
                  colorMode === "rgb" ? "text-primary font-bold" : "text-muted-foreground"
                )}
              >
                RGB
              </button>
            </div>
          </div>
        )}
      </div>

<<<<<<< HEAD
=======
      {/* 3D WebGL Canvas */}
=======
          {status === "ready" && pointCount > 0 && (
            <span className="px-2 py-0.5 rounded-full bg-primary/10 text-primary border border-primary/20 text-xs">
              {pointCount.toLocaleString()} points
            </span>
          )}
        </div>

        {status === "ready" && (
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
                min="0.001"
                max="0.5"
                step="0.001"
                value={pointSize}
                onChange={(event) => setPointSize(parseFloat(event.target.value))}
                className="w-20 accent-primary h-1.5 bg-secondary rounded appearance-none cursor-pointer"
              />
            </div>

            <div className="flex items-center gap-1">
              <button
                onClick={() => applyColorMode("elevation")}
                className={cn(
                  "px-2 py-1 rounded border border-border",
                  colorMode === "elevation" ? "text-primary font-bold" : "text-muted-foreground"
                )}
              >
                ELEV
              </button>
              <button
                onClick={() => applyColorMode("rgb")}
                disabled={!hasVertexColors}
                title={hasVertexColors ? "Colours stored in the PLY" : "This PLY carries no vertex colours"}
                className={cn(
                  "px-2 py-1 rounded border border-border disabled:opacity-30",
                  colorMode === "rgb" ? "text-primary font-bold" : "text-muted-foreground"
                )}
              >
                RGB
              </button>
            </div>
          </div>
        )}
      </div>

>>>>>>> 0400f2f (p5-udpated)
>>>>>>> origin/main
      <div
        ref={mountRef}
        className="w-full h-[450px] rounded-lg overflow-hidden relative cursor-grab active:cursor-grabbing border border-border"
      >
<<<<<<< HEAD
        {status === "empty" && (
          <div className="absolute inset-0 flex flex-col items-center justify-center gap-2 p-6 text-center text-xs text-muted-foreground">
            <Box className="w-8 h-8 text-primary/50" />
            <p className="max-w-sm">{EMPTY_RECONSTRUCTION_MESSAGE}</p>
=======
<<<<<<< HEAD
        <div className="absolute top-3 left-3 flex flex-col gap-1 p-2 rounded bg-black/70 backdrop-blur border border-white/10 text-[11px] text-white pointer-events-none">
          <div className="flex items-center gap-1.5 font-medium text-primary">
            <ZoomIn className="w-3.5 h-3.5" /> Navigation Controls
>>>>>>> origin/main
          </div>
        )}

        {status === "loading" && (
          <div className="absolute inset-0 flex flex-col items-center justify-center gap-2 text-xs text-muted-foreground">
            <Loader2 className="w-5 h-5 animate-spin text-primary" />
            <span>Loading verified point cloud…</span>
          </div>
<<<<<<< HEAD
=======
        </div>
=======
        {status === "empty" && (
          <div className="absolute inset-0 flex flex-col items-center justify-center gap-2 p-6 text-center text-xs text-muted-foreground">
            <Box className="w-8 h-8 text-primary/50" />
            <p className="max-w-sm">{EMPTY_RECONSTRUCTION_MESSAGE}</p>
          </div>
        )}

        {status === "loading" && (
          <div className="absolute inset-0 flex flex-col items-center justify-center gap-2 text-xs text-muted-foreground">
            <Loader2 className="w-5 h-5 animate-spin text-primary" />
            <span>Loading verified point cloud…</span>
          </div>
>>>>>>> origin/main
        )}

        {status === "error" && (
          <div className="absolute inset-0 flex flex-col items-center justify-center gap-2 p-6 text-center text-xs">
            <AlertTriangle className="w-7 h-7 text-rose-400" />
            <div className="font-semibold text-rose-300">Point cloud unavailable</div>
            <p className="text-muted-foreground max-w-md break-words">{errorMessage}</p>
            <button
              onClick={() => setReloadKey((key) => key + 1)}
              className="mt-1 flex items-center gap-1.5 px-2.5 py-1 rounded border border-border text-muted-foreground hover:text-white"
            >
              <RefreshCw className="w-3.5 h-3.5" /> Retry load
            </button>
          </div>
        )}

        {status === "ready" && (
          <>
            <div className="absolute top-3 left-3 flex flex-col gap-1 p-2 rounded bg-black/70 backdrop-blur border border-white/10 text-[11px] text-white pointer-events-none">
              <div className="flex items-center gap-1.5 font-medium text-primary">
                <ZoomIn className="w-3.5 h-3.5" /> Navigation
              </div>
              <span className="text-muted-foreground">Drag: orbit</span>
              <span className="text-muted-foreground">Wheel: zoom</span>
            </div>

            <div className="absolute bottom-3 right-3 p-2 rounded bg-black/80 backdrop-blur border border-white/10 text-[10px] text-white">
              <div className="font-medium text-muted-foreground mb-1">Elevation (relative)</div>
              <div className="h-2 w-28 rounded bg-gradient-to-r from-blue-500 via-emerald-400 to-rose-500" />
              <div className="text-muted-foreground mt-0.5">unscaled reconstruction units</div>
            </div>
          </>
        )}
<<<<<<< HEAD
=======
>>>>>>> 0400f2f (p5-udpated)
>>>>>>> origin/main
      </div>
    </div>
  );
}
<<<<<<< HEAD
=======
<<<<<<< HEAD

=======
>>>>>>> 0400f2f (p5-udpated)
>>>>>>> origin/main

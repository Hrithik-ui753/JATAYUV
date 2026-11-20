"use client";

import React, { useCallback, useEffect, useRef, useState } from "react";
import * as THREE from "three";
import { OrbitControls } from "three/examples/jsm/controls/OrbitControls.js";
import {
  RotateCcw,
  Maximize2,
  Minimize2,
  Ruler,
  Download,
  Crosshair,
  Box,
  AlertTriangle,
  Loader2,
  RefreshCw,
  Sparkles,
  Zap,
  Activity,
  X,
  ChevronRight,
  ChevronLeft,
  Layers,
  Compass,
  Clock,
  Sliders,
  Video,
  Play,
  Pause,
  Scissors,
  Grid as GridIcon,
  Eye,
  EyeOff,
  Sun,
  Check,
  Flame,
  Maximize,
  ShieldAlert,
} from "lucide-react";
import {
  EMPTY_RECONSTRUCTION_MESSAGE,
  isUsablePointCloud,
  resolveViewerState,
  validateArtifactUrl,
} from "@/lib/integrity.mjs";
import type { LocalizedInfrastructureItem } from "@/types/infrastructure";

export type ViewportMode = "render" | "edit" | "object" | "wireframe";
export type ColorMode = "rgb" | "elevation";

export interface AdvancedSpatialViewerProps {
  /** Verified PLY point cloud produced by a real reconstruction. */
  plyUrl?: string;
  /** Optional verified GLB/GLTF/OBJ mesh produced by a real reconstruction. */
  modelUrl?: string;
  projectName?: string;
  locationName?: string;
  className?: string;
  /** AI-detected 3D localized infrastructure assets. */
  infrastructureData?: LocalizedInfrastructureItem[];
  /** Optional URL to fetch spatial intelligence JSON. */
  spatialIntelligenceUrl?: string;
  /** Initial selected track ID to highlight. */
  selectedTrackId?: string | null;
  /** Callback when an infrastructure asset is selected. */
  onSelectObject?: (item: LocalizedInfrastructureItem | null) => void;
  /** Optional aerial drone video URL for side-by-side synchronized view. */
  videoUrl?: string;
  /** Optional poster image for drone video. */
  videoPoster?: string;
  /** Initial viewport mode. Defaults to "render". */
  initialMode?: ViewportMode;
  /** Optional callback to run 3D reconstruction from the uploaded video. */
  onRunReconstruction?: () => void;
  /** Whether 3D reconstruction is currently processing. */
  isReconstructing?: boolean;
}

type ViewerStatus = "empty" | "loading" | "ready" | "error";

interface CloudStats {
  pointCount: number;
  hasVertexColors: boolean;
  units: string;
}

const ELEVATION_GRADIENT = (t: number) => new THREE.Color().setHSL(0.55 - t * 0.55, 0.9, 0.5);

/** Load bytes with a real HTTP status check so a 404 is an error, not an empty scene. */
async function fetchArtifact(url: string): Promise<ArrayBuffer> {
  const response = await fetch(url, { cache: "no-store" });
  if (!response.ok) {
    throw new Error(`Could not load artifact (HTTP ${response.status} ${response.statusText}).`);
  }
  const buffer = await response.arrayBuffer();
  if (buffer.byteLength === 0) {
    throw new Error("Artifact is empty (0 bytes).");
  }
  return buffer;
}

/** Parse PLY bytes with Three.js PLYLoader and reject clouds with no vertices. */
export async function loadPlyGeometry(url: string): Promise<THREE.BufferGeometry> {
  const { PLYLoader } = await import("three/examples/jsm/loaders/PLYLoader.js");
  const buffer = await fetchArtifact(url);
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

async function loadGltfModel(url: string): Promise<THREE.Object3D> {
  const cleanUrl = url.split("?")[0].toLowerCase();
  const buffer = await fetchArtifact(url);

  let model: THREE.Object3D;
  if (cleanUrl.endsWith(".obj")) {
    const { OBJLoader } = await import("three/examples/jsm/loaders/OBJLoader.js");
    const text = new TextDecoder().decode(buffer);
    model = new OBJLoader().parse(text);
  } else if (cleanUrl.endsWith(".ply")) {
    const { PLYLoader } = await import("three/examples/jsm/loaders/PLYLoader.js");
    const geometry = new PLYLoader().parse(buffer);
    geometry.computeBoundingBox();
    geometry.computeVertexNormals();
    const hasColor = Boolean(geometry.getAttribute("color"));
    const material = new THREE.MeshStandardMaterial({
      vertexColors: hasColor,
      roughness: 0.8,
      metalness: 0.1,
      side: THREE.DoubleSide,
    });
    model = new THREE.Mesh(geometry, material);
  } else {
    const { GLTFLoader } = await import("three/examples/jsm/loaders/GLTFLoader.js");
    model = await new Promise<THREE.Object3D>((resolve, reject) => {
      new GLTFLoader().parse(
        buffer,
        "",
        (gltf) => resolve(gltf.scene),
        (error) => reject(new Error(`GLB/GLTF could not be parsed: ${String(error)}`))
      );
    });
  }

  // Traverse model meshes: apply vertex colors if present, or subtle terrain shading.
  // NEVER leave it as flat unshaded blinding white!
  model.traverse((child) => {
    if (child instanceof THREE.Mesh) {
      const hasColor = Boolean(child.geometry?.getAttribute("color"));
      if (hasColor) {
        child.material = new THREE.MeshStandardMaterial({
          vertexColors: true,
          roughness: 0.85,
          metalness: 0.1,
          side: THREE.DoubleSide,
        });
      } else {
        // Uncolored Poisson surface mesh: give it a subtle semi-transparent terrain tint
        // so it never appears as a flat opaque blinding white blob over the point cloud!
        child.material = new THREE.MeshStandardMaterial({
          color: 0x1b3b2b,
          roughness: 0.9,
          metalness: 0.05,
          wireframe: false,
          transparent: true,
          opacity: 0.45,
          side: THREE.DoubleSide,
        });
      }
    }
  });

  return model;
}

/**
 * Generate an ultra-sharp, antialiased circular disc texture at 512x512 resolution.
 * Replaces blurry particles with razor-sharp sub-pixel discs with vector crispness.
 */
function createSharpPointTexture(): THREE.Texture {
  const canvas = document.createElement("canvas");
  canvas.width = 512;
  canvas.height = 512;
  const ctx = canvas.getContext("2d");
  if (ctx) {
    ctx.clearRect(0, 0, 512, 512);
    const gradient = ctx.createRadialGradient(256, 256, 235, 256, 256, 254);
    gradient.addColorStop(0, "rgba(255, 255, 255, 1.0)");
    gradient.addColorStop(0.85, "rgba(255, 255, 255, 1.0)");
    gradient.addColorStop(0.97, "rgba(255, 255, 255, 0.95)");
    gradient.addColorStop(1.0, "rgba(255, 255, 255, 0.0)");
    ctx.fillStyle = gradient;
    ctx.beginPath();
    ctx.arc(256, 256, 254, 0, 2 * Math.PI);
    ctx.fill();
  }
  const texture = new THREE.CanvasTexture(canvas);
  texture.generateMipmaps = true;
  texture.minFilter = THREE.LinearMipmapLinearFilter;
  texture.magFilter = THREE.LinearFilter;
  texture.anisotropy = 16;
  return texture;
}

function createBillboardLabel(text: string, subtext: string, colorHex: string): THREE.Sprite {
  const canvas = document.createElement("canvas");
  canvas.width = 320;
  canvas.height = 96;
  const ctx = canvas.getContext("2d");
  if (ctx) {
    ctx.clearRect(0, 0, 320, 96);
    ctx.fillStyle = "rgba(6, 15, 12, 0.94)";
    ctx.strokeStyle = colorHex;
    ctx.lineWidth = 3;
    ctx.beginPath();
    ctx.roundRect(8, 8, 304, 80, 8);
    ctx.fill();
    ctx.stroke();

    ctx.fillStyle = "#ffffff";
    ctx.font = "bold 22px monospace";
    ctx.textAlign = "center";
    ctx.fillText(text, 160, 42);

    ctx.fillStyle = colorHex;
    ctx.font = "bold 15px monospace";
    ctx.fillText(subtext, 160, 70);
  }
  const texture = new THREE.CanvasTexture(canvas);
  texture.generateMipmaps = true;
  texture.minFilter = THREE.LinearMipmapLinearFilter;
  const material = new THREE.SpriteMaterial({ map: texture, depthTest: false, transparent: true });
  const sprite = new THREE.Sprite(material);
  sprite.scale.set(6.5, 2.0, 1);
  return sprite;
}

export function AdvancedSpatialViewer3D({
  plyUrl,
  modelUrl,
  projectName = "Mission 3D Map",
  locationName,
  infrastructureData,
  spatialIntelligenceUrl,
  selectedTrackId,
  onSelectObject,
  videoUrl,
  videoPoster,
  initialMode = "render",
  className,
  onRunReconstruction,
  isReconstructing = false,
}: AdvancedSpatialViewerProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const canvasHostRef = useRef<HTMLDivElement>(null);
  const videoElementRef = useRef<HTMLVideoElement>(null);

  // --- Core State ---
  const [status, setStatus] = useState<ViewerStatus>("empty");
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [stats, setStats] = useState<CloudStats | null>(null);

  // --- 4 Main Modes: 1. Render, 2. Edit, 3. Object, 4. Wireframe ---
  const [mode, setMode] = useState<ViewportMode>(initialMode);
  const modeRef = useRef<ViewportMode>(initialMode);

  // --- Declutter & Clean 3D Map Toggle ---
  // When true: synthetic yellow cables, cylinder towers, dashed clearance lines, rings, and billboard text tags are completely removed from 3D map.
  const [cleanMapMode, setCleanMapMode] = useState<boolean>(true);
  const cleanMapModeRef = useRef<boolean>(true);

  // --- Ultra-HD 4K Clarity & Adaptive Zoom Point Sizing ---
  const [superClarity, setSuperClarity] = useState<boolean>(true);
  const superClarityRef = useRef<boolean>(true);
  const [adaptiveZoomPoints, setAdaptiveZoomPoints] = useState<boolean>(true);
  const adaptiveZoomPointsRef = useRef<boolean>(true);
  const [pointSize, setPointSize] = useState<number>(2.5);
  const pointSizeRef = useRef<number>(2.5);

  // --- Side-by-side Drone Video Synchronization ---
  const [showVideoSync, setShowVideoSync] = useState<boolean>(false);
  const [videoPlaying, setVideoPlaying] = useState<boolean>(false);

  // --- Zen Mode (Hides all web HUDs for 100% full-canvas clear inspection) ---
  const [zenMode, setZenMode] = useState<boolean>(false);
  const [isFullscreen, setIsFullscreen] = useState<boolean>(false);

  // --- Collapsible Dockable Side Drawer ---
  const [drawerOpen, setDrawerOpen] = useState<boolean>(false);
  const [activeDrawerTab, setActiveDrawerTab] = useState<"tools" | "objects" | "layers" | "timeline">("tools");

  // --- Inspection / Edit Mode Calipers & Slicing ---
  const [colorMode, setColorMode] = useState<ColorMode>("rgb");
  const [measureMode, setMeasureMode] = useState(false);
  const [measurePoints, setMeasurePoints] = useState<THREE.Vector3[]>([]);
  const [measurementResult, setMeasurementResult] = useState<{
    distance: number;
    horizontal: number;
    elevation: number;
    slopeDeg: number;
  } | null>(null);
  const [yClippingRatio, setYClippingRatio] = useState<number>(100); // 0% to 100% elevation cut

  // --- Multi-Mission Timeline ---
  const [timelineStep, setTimelineStep] = useState<number>(2); // 0: Baseline, 1: Survey 2, 2: Current

  // --- Layer Visibility ---
  const [layers, setLayers] = useState({
    pointCloud: true,
    mesh: false, // Default to FALSE so untextured white surface mesh never covers the point cloud
    gridHelper: false,
    boundingBox: false,
  });

  const [infraLayers, setInfraLayers] = useState({
    towers: true,
    lines: true,
    insulators: true,
    anomalies: true,
    labels: false,
  });

  // --- Infrastructure Asset Data & Selection ---
  const [infraItems, setInfraItems] = useState<LocalizedInfrastructureItem[]>(
    infrastructureData || []
  );
  const [selectedItem, setSelectedItem] = useState<LocalizedInfrastructureItem | null>(null);
  const [reloadKey, setReloadKey] = useState(0);

  // --- Scene References ---
  const sceneRef = useRef<THREE.Scene | null>(null);
  const cameraRef = useRef<THREE.PerspectiveCamera | null>(null);
  const controlsRef = useRef<OrbitControls | null>(null);
  const rendererRef = useRef<THREE.WebGLRenderer | null>(null);
  const pointsRef = useRef<THREE.Points | null>(null);
  const meshRef = useRef<THREE.Object3D | null>(null);
  const gridRef = useRef<THREE.GridHelper | null>(null);
  const boxRef = useRef<THREE.Box3Helper | null>(null);
  const contentRef = useRef<THREE.Group | null>(null);
  const infraGroupRef = useRef<THREE.Group | null>(null);
  const towersSubGroupRef = useRef<THREE.Group | null>(null);
  const linesSubGroupRef = useRef<THREE.Group | null>(null);
  const insulatorsSubGroupRef = useRef<THREE.Group | null>(null);
  const anomaliesSubGroupRef = useRef<THREE.Group | null>(null);
  const labelsSubGroupRef = useRef<THREE.Group | null>(null);
  const measureMarkersRef = useRef<THREE.Group | null>(null);
  const measureLineRef = useRef<THREE.Line | null>(null);
  const clippingPlaneRef = useRef<THREE.Plane | null>(null);

  const elevationColorsRef = useRef<Float32Array | null>(null);
  const sourceColorsRef = useRef<Float32Array | null>(null);
  const maxDimensionRef = useRef<number>(1);
  const boundsCenterRef = useRef<THREE.Vector3>(new THREE.Vector3());
  const boundsMinYRef = useRef<number>(0);
  const boundsMaxYRef = useRef<number>(1);
  const sharpTextureRef = useRef<THREE.Texture | null>(null);

  // Sync ref values for animation loop
  useEffect(() => {
    modeRef.current = mode;
  }, [mode]);
  useEffect(() => {
    cleanMapModeRef.current = cleanMapMode;
  }, [cleanMapMode]);
  useEffect(() => {
    superClarityRef.current = superClarity;
  }, [superClarity]);
  useEffect(() => {
    adaptiveZoomPointsRef.current = adaptiveZoomPoints;
  }, [adaptiveZoomPoints]);
  useEffect(() => {
    pointSizeRef.current = pointSize;
  }, [pointSize]);

  const resolved = resolveViewerState({ plyUrl, modelUrl });

  // -------------------------------------------------------------
  // Keyboard Shortcuts: 1 (Render), 2 (Edit), 3 (Object), 4 (Wireframe), C (Clean), Z (Zen)
  // -------------------------------------------------------------
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.target instanceof HTMLInputElement || e.target instanceof HTMLTextAreaElement) return;
      if (e.key === "1") setMode("render");
      else if (e.key === "2") setMode("edit");
      else if (e.key === "3") setMode("object");
      else if (e.key === "4") setMode("wireframe");
      else if (e.key.toLowerCase() === "c") setCleanMapMode((prev) => !prev);
      else if (e.key.toLowerCase() === "z") setZenMode((prev) => !prev);
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, []);

  // -------------------------------------------------------------
  // Core Three.js Scene Setup & Render Loop
  // -------------------------------------------------------------
  useEffect(() => {
    if (resolved.status === "empty" || resolved.status === "error") {
      setStatus(resolved.status === "empty" ? "empty" : "error");
      setErrorMessage(resolved.status === "error" ? resolved.message ?? "Invalid artifact URL." : null);
      return;
    }

    const host = canvasHostRef.current;
    if (!host) return;

    let cancelled = false;
    const disposables: Array<{ dispose: () => void }> = [];
    setStatus("loading");
    setErrorMessage(null);
    setStats(null);
    setMeasurePoints([]);
    setMeasurementResult(null);

    const scene = new THREE.Scene();
    scene.background = new THREE.Color(0x060b09);
    sceneRef.current = scene;

    const camera = new THREE.PerspectiveCamera(
      45,
      Math.max(1, host.clientWidth) / Math.max(1, host.clientHeight),
      0.001,
      10000
    );
    camera.position.set(12, 10, 14);
    cameraRef.current = camera;

    const renderer = new THREE.WebGLRenderer({
      antialias: true,
      preserveDrawingBuffer: true,
      powerPreference: "high-performance",
      logarithmicDepthBuffer: true, // Prevents z-fighting and close-zoom clipping blur
    });
    renderer.setSize(host.clientWidth || 640, host.clientHeight || 480);
    const pixelRatio = Math.min(window.devicePixelRatio || 1, superClarityRef.current ? 3.5 : 2.0);
    renderer.setPixelRatio(pixelRatio);
    renderer.toneMapping = THREE.ACESFilmicToneMapping;
    renderer.toneMappingExposure = 1.35;
    renderer.outputColorSpace = THREE.SRGBColorSpace;
    renderer.localClippingEnabled = true;

    host.appendChild(renderer.domElement);
    rendererRef.current = renderer;

    const controls = new OrbitControls(camera, renderer.domElement);
    controls.enableDamping = true;
    controls.dampingFactor = 0.08;
    controls.zoomSpeed = 1.2;
    controls.rotateSpeed = 0.85;
    controls.panSpeed = 0.85;
    controls.target.set(0, 0, 0);
    controlsRef.current = controls;

    // Lighting (Realistic sun + ambient + subtle rim)
    const ambientLight = new THREE.AmbientLight(0xe4f5ed, 1.8);
    scene.add(ambientLight);
    const sunLight = new THREE.DirectionalLight(0xffffff, 2.2);
    sunLight.position.set(40, 60, 30);
    scene.add(sunLight);
    const rimLight = new THREE.DirectionalLight(0x00f5a0, 0.4);
    rimLight.position.set(-30, -20, -30);
    scene.add(rimLight);

    const content = new THREE.Group();
    scene.add(content);
    contentRef.current = content;

    const markers = new THREE.Group();
    scene.add(markers);
    measureMarkersRef.current = markers;

    const measureLine = new THREE.Line(
      new THREE.BufferGeometry(),
      new THREE.LineBasicMaterial({ color: 0x00f5a0, linewidth: 2 })
    );
    measureLine.visible = false;
    scene.add(measureLine);
    measureLineRef.current = measureLine;

    // Animation & Adaptive Zoom Scaling Loop
    let animationFrame = 0;
    const animate = () => {
      animationFrame = requestAnimationFrame(animate);
      controls.update();

      // Crystal-clear sub-pixel point scaling on zoom
      if (pointsRef.current && adaptiveZoomPointsRef.current) {
        const dist = camera.position.distanceTo(controls.target);
        const maxDim = maxDimensionRef.current || 1;
        // Dynamically shrink points when zooming in close so pixels stay razor-sharp
        const distRatio = Math.max(0.12, Math.min(2.5, dist / (maxDim * 1.4)));
        const base = Math.max(maxDim * 0.005, 0.06);
        const mat = pointsRef.current.material as THREE.PointsMaterial;
        mat.size = base * (pointSizeRef.current / 2.5) * Math.sqrt(distRatio);
      }

      renderer.render(scene, camera);
    };
    animate();

    const stageScene = () => {
      const bounds = new THREE.Box3().setFromObject(content);
      if (bounds.isEmpty()) {
        throw new Error("Artifact contained no renderable geometry.");
      }
      const center = bounds.getCenter(new THREE.Vector3());
      boundsCenterRef.current.copy(center);
      content.position.sub(center);

      const size = bounds.getSize(new THREE.Vector3());
      const maxDimension = Math.max(size.x, size.y, size.z) || 1;
      maxDimensionRef.current = maxDimension;
      boundsMinYRef.current = bounds.min.y - center.y;
      boundsMaxYRef.current = bounds.max.y - center.y;

      const distance = maxDimension * 1.6;
      camera.position.set(distance * 0.8, distance * 0.6, distance * 0.9);
      camera.near = Math.max(0.0005, maxDimension / 20000); // Super close zoom capability
      camera.far = Math.max(200, maxDimension * 200);
      camera.updateProjectionMatrix();
      controls.target.set(0, 0, 0);
      controls.minDistance = Math.max(0.005, maxDimension * 0.002);
      controls.maxDistance = maxDimension * 30;
      controls.update();

      // Coordinate reference grid
      const gridSize = maxDimension * 1.6;
      const grid = new THREE.GridHelper(gridSize, 24, 0x10b981, 0x10281e);
      grid.position.y = -size.y / 2;
      grid.visible = layers.gridHelper;
      scene.add(grid);
      gridRef.current = grid;
      disposables.push(grid.geometry, grid.material as THREE.Material);

      // Bounding Box Helper
      const box = new THREE.Box3Helper(new THREE.Box3().setFromObject(content), 0x10b981);
      box.visible = layers.boundingBox;
      scene.add(box);
      boxRef.current = box;
      disposables.push(box.geometry, box.material as THREE.Material);

      // --- Infrastructure Assets 3D Group ---
      const infraGroup = new THREE.Group();
      infraGroupRef.current = infraGroup;
      content.add(infraGroup);

      const towersGroup = new THREE.Group();
      towersSubGroupRef.current = towersGroup;
      infraGroup.add(towersGroup);

      const linesGroup = new THREE.Group();
      linesSubGroupRef.current = linesGroup;
      infraGroup.add(linesGroup);

      const insulatorsGroup = new THREE.Group();
      insulatorsSubGroupRef.current = insulatorsGroup;
      infraGroup.add(insulatorsGroup);

      const anomaliesGroup = new THREE.Group();
      anomaliesSubGroupRef.current = anomaliesGroup;
      infraGroup.add(anomaliesGroup);

      const labelsGroup = new THREE.Group();
      labelsSubGroupRef.current = labelsGroup;
      labelsGroup.visible = infraLayers.labels;
      infraGroup.add(labelsGroup);

      // Populate 3D markers from infraItems
      infraItems.forEach((item) => {
        const pos = new THREE.Vector3(...item.position);
        let colorHex = "#06b6d4";

        if (item.class_name === "transmission_tower") {
          colorHex = "#06b6d4";
          const towerH = Math.max(item.extents[1] || 16, 6);
          const mastGeo = new THREE.CylinderGeometry(0.8, 1.8, towerH, 6);
          const mastMat = new THREE.MeshStandardMaterial({
            color: 0x06b6d4,
            emissive: 0x0891b2,
            emissiveIntensity: 0.35,
            wireframe: true,
          });
          const mast = new THREE.Mesh(mastGeo, mastMat);
          mast.position.set(pos.x, pos.y + towerH / 2, pos.z);
          mast.userData = { infraItem: item };
          towersGroup.add(mast);
          disposables.push(mastGeo, mastMat);

          const crossGeo = new THREE.BoxGeometry(item.extents[0] || 10, 0.5, 0.8);
          const crossMat = new THREE.MeshStandardMaterial({ color: 0x38bdf8, metalness: 0.8 });
          const cross = new THREE.Mesh(crossGeo, crossMat);
          cross.position.set(pos.x, pos.y + towerH * 0.85, pos.z);
          cross.userData = { infraItem: item };
          towersGroup.add(cross);
          disposables.push(crossGeo, crossMat);
        } else if (item.class_name === "transmission_line") {
          colorHex = "#f59e0b";
          const catPts =
            item.catenary_model?.interpolated_catenary_curve?.map((p) => new THREE.Vector3(...p.position)) ||
            (item.line_waypoints && item.line_waypoints.length >= 2
              ? item.line_waypoints.map((p) => new THREE.Vector3(...p))
              : null);

          if (catPts && catPts.length >= 2) {
            const curve = new THREE.CatmullRomCurve3(catPts);
            const tubeGeo = new THREE.TubeGeometry(curve, 32, 0.22, 6, false);
            const tubeMat = new THREE.MeshStandardMaterial({
              color: 0xf59e0b,
              emissive: 0xd97706,
              emissiveIntensity: 0.5,
              roughness: 0.3,
            });
            const tube = new THREE.Mesh(tubeGeo, tubeMat);
            tube.userData = { infraItem: item };
            linesGroup.add(tube);
            disposables.push(tubeGeo, tubeMat);

            if (item.clearance_result?.bottleneck) {
              const bn = item.clearance_result.bottleneck;
              const pCond = new THREE.Vector3(...bn.conductor_point_3d);
              const pTerr = new THREE.Vector3(...bn.terrain_point_3d);

              const lineGeo = new THREE.BufferGeometry().setFromPoints([pCond, pTerr]);
              const lineMat = new THREE.LineDashedMaterial({
                color: bn.clearance_status === "CLEARANCE_WARNING" ? 0xef4444 : 0xf59e0b,
                dashSize: 0.8,
                gapSize: 0.4,
              });
              const line = new THREE.Line(lineGeo, lineMat);
              line.computeLineDistances();
              linesGroup.add(line);
              disposables.push(lineGeo, lineMat);

              const ringG = new THREE.RingGeometry(0.8, 1.2, 16);
              const ringM = new THREE.MeshBasicMaterial({
                color: bn.clearance_status === "CLEARANCE_WARNING" ? 0xef4444 : 0xf59e0b,
                side: THREE.DoubleSide,
                transparent: true,
                opacity: 0.7,
              });
              const ring = new THREE.Mesh(ringG, ringM);
              ring.position.copy(pTerr);
              ring.rotation.x = Math.PI / 2;
              linesGroup.add(ring);
              disposables.push(ringG, ringM);
            }
          } else {
            const sphereGeo = new THREE.SphereGeometry(1.0, 12, 12);
            const sphereMat = new THREE.MeshStandardMaterial({ color: 0xf59e0b, emissive: 0xd97706, emissiveIntensity: 0.4 });
            const s = new THREE.Mesh(sphereGeo, sphereMat);
            s.position.copy(pos);
            s.userData = { infraItem: item };
            linesGroup.add(s);
            disposables.push(sphereGeo, sphereMat);
          }
        } else if (item.class_name === "insulator") {
          colorHex = "#10b981";
          const insGeo = new THREE.CylinderGeometry(0.4, 0.4, item.extents[1] || 2.5, 8);
          const insMat = new THREE.MeshStandardMaterial({ color: 0x10b981, emissive: 0x059669, emissiveIntensity: 0.4 });
          const ins = new THREE.Mesh(insGeo, insMat);
          ins.position.copy(pos);
          ins.userData = { infraItem: item };
          insulatorsGroup.add(ins);
          disposables.push(insGeo, insMat);
        } else if (item.class_name === "structural_damage" || item.severity !== "NORMAL") {
          colorHex = "#ef4444";
          const sphereGeo = new THREE.SphereGeometry(1.2, 16, 16);
          const sphereMat = new THREE.MeshStandardMaterial({ color: 0xef4444, emissive: 0xb91c1c, emissiveIntensity: 0.8 });
          const s = new THREE.Mesh(sphereGeo, sphereMat);
          s.position.copy(pos);
          s.userData = { infraItem: item };
          anomaliesGroup.add(s);
          disposables.push(sphereGeo, sphereMat);

          const ringGeo = new THREE.RingGeometry(1.5, 2.2, 24);
          const ringMat = new THREE.MeshBasicMaterial({ color: 0xf87171, side: THREE.DoubleSide, transparent: true, opacity: 0.7 });
          const ring = new THREE.Mesh(ringGeo, ringMat);
          ring.position.copy(pos);
          ring.rotation.x = Math.PI / 2;
          anomaliesGroup.add(ring);
          disposables.push(ringGeo, ringMat);
        } else {
          colorHex = "#8b5cf6";
          const boxG = new THREE.BoxGeometry(...item.extents);
          const boxM = new THREE.MeshStandardMaterial({ color: 0x8b5cf6, wireframe: true });
          const b = new THREE.Mesh(boxG, boxM);
          b.position.copy(pos);
          b.userData = { infraItem: item };
          towersGroup.add(b);
          disposables.push(boxG, boxM);
        }

        const labelSprite = createBillboardLabel(
          item.track_id,
          `${Math.round(item.confidence * 100)}% CONF · ${item.severity}`,
          colorHex
        );
        const labelHeight = (item.extents[1] || 8) + 2.5;
        labelSprite.position.set(pos.x, pos.y + labelHeight, pos.z);
        labelSprite.userData = { infraItem: item };
        labelsGroup.add(labelSprite);
        disposables.push(labelSprite.material, (labelSprite.material as THREE.SpriteMaterial).map as THREE.Texture);
      });

      // Initialize visibility based on current mode & cleanMapMode
      updateSceneModeVisibility(modeRef.current, cleanMapModeRef.current);
    };

    const applyElevationColors = (geometry: THREE.BufferGeometry) => {
      geometry.computeBoundingBox();
      const box = geometry.boundingBox ?? new THREE.Box3().setFromBufferAttribute(
        geometry.getAttribute("position") as THREE.BufferAttribute
      );
      const minY = box.min.y;
      const spanY = Math.max(1e-6, box.max.y - minY);
      const position = geometry.getAttribute("position");
      const colors = new Float32Array(position.count * 3);
      for (let i = 0; i < position.count; i++) {
        const t = THREE.MathUtils.clamp((position.getY(i) - minY) / spanY, 0, 1);
        const color = ELEVATION_GRADIENT(t);
        colors[i * 3] = color.r;
        colors[i * 3 + 1] = color.g;
        colors[i * 3 + 2] = color.b;
      }
      elevationColorsRef.current = colors;
      geometry.setAttribute("color", new THREE.BufferAttribute(colors, 3));
    };

    const load = async () => {
      const sources = resolved.sources ?? [];
      let pointCount = 0;
      let hasVertexColors = false;

      for (const source of sources) {
        if (source.kind === "ply") {
          const geometry = await loadPlyGeometry(source.url);
          if (cancelled) {
            geometry.dispose();
            return;
          }
          const colorAttr = geometry.getAttribute("color");
          hasVertexColors = Boolean(colorAttr);
          const sourceColors = colorAttr
            ? new Float32Array(colorAttr.array as ArrayLike<number>)
            : null;
          sourceColorsRef.current = sourceColors;
          applyElevationColors(geometry);

          // Restore true photographic RGB colors from drone photogrammetry
          if (hasVertexColors && sourceColors) {
            geometry.setAttribute("color", new THREE.BufferAttribute(new Float32Array(sourceColors), 3));
          }

          const sharpTex = createSharpPointTexture();
          sharpTextureRef.current = sharpTex;
          disposables.push(sharpTex);

          const baseSize = Math.max(maxDimensionRef.current * 0.005, 0.06);
          // Solid antialiased disc material: alphaTest 0.5 and transparent: false
          // prevents fuzzy halos and depth buffer flickering on close zoom!
          const material = new THREE.PointsMaterial({
            size: baseSize * (pointSizeRef.current / 2.5),
            vertexColors: true,
            map: sharpTex,
            alphaTest: 0.5,
            depthWrite: true,
            depthTest: true,
            transparent: false,
            sizeAttenuation: true,
          });
          const points = new THREE.Points(geometry, material);
          content.add(points);
          pointsRef.current = points;
          disposables.push(geometry, material);
          pointCount = geometry.getAttribute("position").count;
        } else if (source.kind === "model") {
          const model = await loadGltfModel(source.url);
          if (cancelled) return;
          content.add(model);
          meshRef.current = model;
          model.visible = layers.mesh;
        }
      }

      if (cancelled) return;

      stageScene();

      setStats({
        pointCount,
        hasVertexColors,
        units: "scale-calibrated reconstruction units",
      });
      setColorMode(hasVertexColors ? "rgb" : "elevation");
      setStatus("ready");
    };

    load().catch((error: unknown) => {
      if (cancelled) return;
      setErrorMessage(error instanceof Error ? error.message : String(error));
      setStatus("error");
    });

    // Canvas click raycaster (Asset selection & caliper measurements)
    const raycaster = new THREE.Raycaster();
    const pointer = new THREE.Vector2();

    const handleCanvasClick = (event: MouseEvent) => {
      const rect = renderer.domElement.getBoundingClientRect();
      pointer.x = ((event.clientX - rect.left) / rect.width) * 2 - 1;
      pointer.y = -((event.clientY - rect.top) / rect.height) * 2 + 1;

      // In Object Mode, check clicks on infrastructure 3D assets
      if (modeRef.current === "object" && infraGroupRef.current && infraGroupRef.current.visible) {
        raycaster.setFromCamera(pointer, camera);
        const infraHits = raycaster.intersectObjects(infraGroupRef.current.children, true);
        if (infraHits.length > 0) {
          let topObj: THREE.Object3D | null = infraHits[0].object;
          while (topObj && !topObj.userData?.infraItem && topObj.parent) {
            topObj = topObj.parent;
          }
          if (topObj?.userData?.infraItem) {
            const item = topObj.userData.infraItem as LocalizedInfrastructureItem;
            setSelectedItem(item);
            onSelectObject?.(item);
            setDrawerOpen(true);
            setActiveDrawerTab("objects");
            return;
          }
        }
      }

      // In Edit Mode, measurement caliper clicking
      if (modeRef.current === "edit" && pointsRef.current) {
        raycaster.params.Points.threshold = Math.max(maxDimensionRef.current * 0.015, 0.01);
        raycaster.setFromCamera(pointer, camera);
        const intersects = raycaster.intersectObject(pointsRef.current);
        if (intersects.length > 0) {
          const hit = intersects[0].point.clone();
          setMeasurePoints((previous) => (previous.length >= 2 ? [hit] : [...previous, hit]));
        }
      }
    };

    renderer.domElement.addEventListener("click", handleCanvasClick);

    const handleResize = () => {
      if (!host) return;
      const width = host.clientWidth || 1;
      const height = host.clientHeight || 1;
      camera.aspect = width / height;
      camera.updateProjectionMatrix();
      const pr = Math.min(window.devicePixelRatio || 1, superClarityRef.current ? 3.5 : 2.0);
      renderer.setPixelRatio(pr);
      renderer.setSize(width, height);
    };
    window.addEventListener("resize", handleResize);

    return () => {
      cancelled = true;
      window.removeEventListener("resize", handleResize);
      renderer.domElement.removeEventListener("click", handleCanvasClick);
      cancelAnimationFrame(animationFrame);
      controls.dispose();
      disposables.forEach((item) => item.dispose());
      renderer.dispose();
      if (host.contains(renderer.domElement)) {
        host.removeChild(renderer.domElement);
      }
      rendererRef.current = null;
      sharpTextureRef.current = null;
      pointsRef.current = null;
      meshRef.current = null;
      sceneRef.current = null;
      cameraRef.current = null;
      controlsRef.current = null;
      gridRef.current = null;
      boxRef.current = null;
      infraGroupRef.current = null;
      measureMarkersRef.current = null;
      measureLineRef.current = null;
      elevationColorsRef.current = null;
      sourceColorsRef.current = null;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [plyUrl, modelUrl, reloadKey]);

  // -------------------------------------------------------------
  // Mode Transition & Synthetic Overlays Controller
  // -------------------------------------------------------------
  const updateSceneModeVisibility = (targetMode: ViewportMode, isCleanMap: boolean) => {
    // 1. Synthetic Cables / Transformers / Extra elements ("tmeotvt that taransofrms light cbales unncnessaart thisng in 3d map")
    // When isCleanMap is true or mode is "render" / "wireframe": ALL synthetic clutter is purged!
    const showSynthetics = targetMode === "object" && !isCleanMap;

    if (infraGroupRef.current) {
      infraGroupRef.current.visible = showSynthetics;
    }
    if (towersSubGroupRef.current) {
      towersSubGroupRef.current.visible = showSynthetics && infraLayers.towers;
    }
    if (linesSubGroupRef.current) {
      linesSubGroupRef.current.visible = showSynthetics && infraLayers.lines;
    }
    if (insulatorsSubGroupRef.current) {
      insulatorsSubGroupRef.current.visible = showSynthetics && infraLayers.insulators;
    }
    if (anomaliesSubGroupRef.current) {
      anomaliesSubGroupRef.current.visible = showSynthetics && infraLayers.anomalies;
    }
    if (labelsSubGroupRef.current) {
      labelsSubGroupRef.current.visible = showSynthetics && infraLayers.labels;
    }

    // 2. Wireframe Mode vs Solid Mode
    if (meshRef.current) {
      const isWireframe = targetMode === "wireframe";
      meshRef.current.visible = isWireframe || layers.mesh;
      meshRef.current.traverse((child) => {
        if (child instanceof THREE.Mesh) {
          if (isWireframe) {
            child.material.wireframe = true;
            child.material.color = new THREE.Color(0x10b981);
            child.material.transparent = false;
            child.material.opacity = 1.0;
          } else {
            child.material.wireframe = false;
            const hasColor = Boolean(child.geometry?.getAttribute("color"));
            if (hasColor) {
              child.material.vertexColors = true;
              child.material.color = new THREE.Color(0xffffff);
            } else {
              child.material.color = new THREE.Color(0x1b3b2b);
              child.material.transparent = true;
              child.material.opacity = 0.45;
            }
          }
        }
      });
    }

    // 3. Grid & Box Helpers
    if (gridRef.current) {
      gridRef.current.visible = targetMode === "wireframe" || targetMode === "edit" || layers.gridHelper;
    }
    if (boxRef.current) {
      boxRef.current.visible = targetMode === "wireframe" || layers.boundingBox;
    }

    // 4. Background styling based on mode
    if (sceneRef.current) {
      if (targetMode === "wireframe") {
        sceneRef.current.background = new THREE.Color(0x040806);
      } else if (targetMode === "render") {
        sceneRef.current.background = new THREE.Color(0x060b09);
      } else {
        sceneRef.current.background = new THREE.Color(0x060c0a);
      }
    }
  };

  useEffect(() => {
    updateSceneModeVisibility(mode, cleanMapMode);
  }, [mode, cleanMapMode, infraLayers, layers]);

  // -------------------------------------------------------------
  // Caliper Measurement Calculation
  // -------------------------------------------------------------
  useEffect(() => {
    const markers = measureMarkersRef.current;
    const line = measureLineRef.current;
    if (!markers || !line) return;

    while (markers.children.length > 0) {
      markers.remove(markers.children[0]);
    }

    const markerRadius = maxDimensionRef.current * 0.006;
    measurePoints.forEach((point, index) => {
      const sphere = new THREE.Mesh(
        new THREE.SphereGeometry(Math.max(markerRadius, 0.001), 16, 16),
        new THREE.MeshBasicMaterial({ color: index === 0 ? 0x10b981 : 0x00f5a0 })
      );
      sphere.position.copy(point);
      markers.add(sphere);
    });

    if (measurePoints.length === 2) {
      const [first, second] = measurePoints;
      line.geometry.dispose();
      line.geometry = new THREE.BufferGeometry().setFromPoints([first, second]);
      line.visible = true;

      const distance = first.distanceTo(second);
      const horizontal = Math.sqrt((second.x - first.x) ** 2 + (second.z - first.z) ** 2);
      const elevation = Math.abs(second.y - first.y);
      const slope = horizontal > 0 ? Math.atan2(elevation, horizontal) * (180 / Math.PI) : 90;

      setMeasurementResult({
        distance: +distance.toFixed(3),
        horizontal: +horizontal.toFixed(3),
        elevation: +elevation.toFixed(3),
        slopeDeg: +slope.toFixed(1),
      });
    } else {
      line.visible = false;
      if (measurePoints.length === 0) setMeasurementResult(null);
    }
  }, [measurePoints]);

  // -------------------------------------------------------------
  // Y-Clipping Plane (Elevation Cross-Section in Edit Mode)
  // -------------------------------------------------------------
  useEffect(() => {
    if (!rendererRef.current) return;
    if (yClippingRatio >= 100) {
      if (clippingPlaneRef.current) {
        clippingPlaneRef.current = null;
        if (pointsRef.current) {
          (pointsRef.current.material as THREE.PointsMaterial).clippingPlanes = [];
        }
      }
      return;
    }

    const minY = boundsMinYRef.current;
    const maxY = boundsMaxYRef.current;
    const cutY = minY + ((maxY - minY) * yClippingRatio) / 100;

    const plane = new THREE.Plane(new THREE.Vector3(0, -1, 0), cutY);
    clippingPlaneRef.current = plane;

    if (pointsRef.current) {
      const mat = pointsRef.current.material as THREE.PointsMaterial;
      mat.clippingPlanes = [plane];
      mat.needsUpdate = true;
    }
  }, [yClippingRatio]);

  // -------------------------------------------------------------
  // Colormap Switching (True RGB vs Elevation Gradient)
  // -------------------------------------------------------------
  const applyColorMode = useCallback((newMode: ColorMode) => {
    const points = pointsRef.current;
    if (!points) return;
    const geometry = points.geometry;
    const position = geometry.getAttribute("position");
    const target = newMode === "rgb" ? sourceColorsRef.current : elevationColorsRef.current;
    if (!target) return;
    const colors = new Float32Array(position.count * 3);
    colors.set(target.subarray(0, colors.length));
    geometry.setAttribute("color", new THREE.BufferAttribute(colors, 3));
    const colorAttr = geometry.getAttribute("color");
    if (colorAttr) colorAttr.needsUpdate = true;
    setColorMode(newMode);
  }, []);

  // -------------------------------------------------------------
  // Camera View Presets
  // -------------------------------------------------------------
  const setCameraView = (view: "nadir" | "oblique" | "reset") => {
    const camera = cameraRef.current;
    const controls = controlsRef.current;
    if (!camera || !controls) return;
    const distance = Math.max(maxDimensionRef.current * 1.6, 0.01);
    if (view === "nadir") {
      camera.position.set(0, distance, 0.0001);
    } else if (view === "oblique") {
      camera.position.set(distance, distance * 0.45, distance);
    } else {
      camera.position.set(distance * 0.8, distance * 0.6, distance * 0.9);
    }
    controls.target.set(0, 0, 0);
    controls.update();
  };

  const focusOnObject = (pos: [number, number, number]) => {
    const controls = controlsRef.current;
    const camera = cameraRef.current;
    if (!controls || !camera) return;
    const target = new THREE.Vector3(...pos);
    controls.target.copy(target);
    camera.position.set(target.x + 10, target.y + 8, target.z + 12);
    controls.update();
  };

  // Fullscreen Toggle
  const toggleFullscreen = () => {
    const container = containerRef.current;
    if (!container) return;
    if (!document.fullscreenElement) {
      container
        .requestFullscreen()
        .then(() => setIsFullscreen(true))
        .catch((error) => console.error(error));
    } else {
      document
        .exitFullscreen()
        .then(() => setIsFullscreen(false))
        .catch((error) => console.error(error));
    }
  };

  // Screenshot Export
  const exportScreenshot = () => {
    const canvas = canvasHostRef.current?.querySelector("canvas");
    if (!canvas) return;
    const link = document.createElement("a");
    link.href = canvas.toDataURL("image/png");
    link.download = `JATAYUV_4K_SURFACE_${mode.toUpperCase()}_${Date.now()}.png`;
    link.click();
  };

  // Super Clarity 4K Toggle
  const toggleSuperClarity = () => {
    setSuperClarity((prev) => {
      const next = !prev;
      superClarityRef.current = next;
      if (rendererRef.current && canvasHostRef.current) {
        const pr = Math.min(window.devicePixelRatio || 1, next ? 3.5 : 2.0);
        rendererRef.current.setPixelRatio(pr);
        rendererRef.current.setSize(
          canvasHostRef.current.clientWidth || 640,
          canvasHostRef.current.clientHeight || 480
        );
      }
      return next;
    });
  };

  // Video playback control
  const toggleVideoPlay = () => {
    if (!videoElementRef.current) return;
    if (videoPlaying) {
      videoElementRef.current.pause();
      setVideoPlaying(false);
    } else {
      videoElementRef.current.play().then(() => setVideoPlaying(true)).catch(console.error);
    }
  };

  // Fetch Spatial Intelligence if provided
  useEffect(() => {
    if (infrastructureData) {
      setInfraItems(infrastructureData);
      return;
    }
    if (spatialIntelligenceUrl) {
      fetch(spatialIntelligenceUrl)
        .then((res) => (res.ok ? res.json() : null))
        .then((data) => {
          if (data && data.infrastructure_objects_3d) {
            setInfraItems(data.infrastructure_objects_3d);
          }
        })
        .catch((err) => console.warn("Could not load spatial intelligence:", err));
    }
  }, [infrastructureData, spatialIntelligenceUrl]);

  // Sync selected track ID from outside
  useEffect(() => {
    if (!selectedTrackId) return;
    const found = infraItems.find((it) => it.track_id === selectedTrackId);
    if (found) {
      setSelectedItem(found);
      focusOnObject(found.position);
      setDrawerOpen(true);
      setActiveDrawerTab("objects");
    }
  }, [selectedTrackId, infraItems]);

  const hasArtifact = Boolean(plyUrl || modelUrl);

  return (
    <div
      ref={containerRef}
      className={`relative w-full rounded-2xl overflow-hidden border border-emerald-500/30 bg-forest-950 select-none shadow-2xl transition-all duration-300 ${
        isFullscreen ? "h-screen w-screen" : "h-[680px]"
      } ${className || ""}`}
    >
      {/* 3D WebGL Canvas Viewport */}
      <div className="relative w-full h-full flex">
        {/* Main 3D Canvas */}
        <div
          ref={canvasHostRef}
          className={`h-full transition-all duration-300 ${
            showVideoSync && videoUrl ? "w-1/2 border-r border-emerald-500/30" : "w-full"
          }`}
        />

        {/* Side-by-side Drone Video Synchronization Panel ("Same as video, same as 3D") */}
        {showVideoSync && videoUrl && (
          <div className="w-1/2 h-full bg-forest-950 flex flex-col relative z-10 animate-in fade-in duration-300">
            <div className="p-3 border-b border-emerald-500/20 bg-forest-900/80 backdrop-blur flex items-center justify-between text-xs font-mono">
              <div className="flex items-center gap-2">
                <Video className="w-4 h-4 text-emerald-400" />
                <span className="font-bold text-white uppercase tracking-wider">
                  4K DRONE FLIGHT VIDEO (SYNCHRONIZED)
                </span>
                <span className="px-1.5 py-0.5 rounded bg-emerald-500/20 text-emerald-300 text-[10px] font-bold">
                  MATCHED 1:1 QUALITY
                </span>
              </div>
              <div className="flex items-center gap-2">
                <button
                  onClick={toggleVideoPlay}
                  className="px-2 py-1 rounded bg-emerald-600 hover:bg-emerald-500 text-white font-bold text-[11px] flex items-center gap-1"
                >
                  {videoPlaying ? <Pause className="w-3.5 h-3.5" /> : <Play className="w-3.5 h-3.5" />}
                  <span>{videoPlaying ? "PAUSE" : "PLAY"}</span>
                </button>
                <button
                  onClick={() => setShowVideoSync(false)}
                  className="p-1 rounded hover:bg-forest-800 text-muted-foreground hover:text-white"
                >
                  <X className="w-4 h-4" />
                </button>
              </div>
            </div>

            <div className="flex-1 relative flex items-center justify-center bg-black overflow-hidden">
              <video
                ref={videoElementRef}
                src={videoUrl}
                poster={videoPoster}
                controls
                loop
                playsInline
                className="w-full h-full object-contain"
                onPlay={() => setVideoPlaying(true)}
                onPause={() => setVideoPlaying(false)}
              />
              <div className="absolute top-3 left-3 bg-forest-950/80 backdrop-blur px-2 py-1 rounded border border-emerald-500/30 text-[10px] font-mono text-emerald-300">
                AERIAL RAW PIXELS: 100% CRYSTAL CLEAR
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Empty State / Standby Drone Video Viewport */}
      {status === "empty" && (
        <div className="absolute inset-0 z-20 bg-forest-950 flex flex-col">
          {videoUrl ? (
            <div className="relative w-full h-full flex flex-col bg-black">
              {/* Header Bar */}
              <div className="p-3 border-b border-emerald-500/25 bg-forest-950/95 backdrop-blur flex items-center justify-between text-xs font-mono z-10">
                <div className="flex items-center gap-2">
                  <Video className="w-4 h-4 text-emerald-400" />
                  <span className="font-bold text-white uppercase tracking-wider">
                    {projectName} // DRONE FLIGHT FOOTAGE READY
                  </span>
                  <span className="px-1.5 py-0.5 rounded bg-emerald-500/20 text-emerald-300 text-[10px] font-bold">
                    4K UAV FOOTAGE
                  </span>
                </div>
                {onRunReconstruction && (
                  <button
                    onClick={onRunReconstruction}
                    disabled={isReconstructing}
                    className="px-3.5 py-1.5 rounded-lg bg-gradient-to-r from-emerald-600 to-teal-500 hover:from-emerald-500 hover:to-teal-400 text-white font-bold text-xs flex items-center gap-1.5 shadow-lg transition-all disabled:opacity-50 border border-emerald-400/40"
                  >
                    {isReconstructing ? (
                      <>
                        <Loader2 className="w-3.5 h-3.5 animate-spin" />
                        <span>RECONSTRUCTING 3D MODEL...</span>
                      </>
                    ) : (
                      <>
                        <Sparkles className="w-3.5 h-3.5 text-amber-300" />
                        <span>RUN 3D RECONSTRUCTION</span>
                      </>
                    )}
                  </button>
                )}
              </div>

              {/* Video Player */}
              <div className="flex-1 relative flex items-center justify-center bg-black overflow-hidden">
                <video
                  src={videoUrl}
                  poster={videoPoster}
                  controls
                  loop
                  playsInline
                  autoPlay
                  muted
                  className="w-full h-full object-contain"
                />
                <div className="absolute bottom-4 left-4 right-4 flex items-center justify-between pointer-events-none">
                  <div className="bg-forest-950/90 backdrop-blur px-3 py-1.5 rounded-lg border border-emerald-500/30 font-mono text-[11px] text-emerald-300 pointer-events-auto shadow-2xl">
                    AERIAL DRONE VIDEO LOADED · READY FOR 3D PHOTOGRAMMETRIC SURFACE GENERATION
                  </div>
                  {onRunReconstruction && (
                    <button
                      onClick={onRunReconstruction}
                      disabled={isReconstructing}
                      className="px-4 py-2 rounded-xl bg-gradient-to-r from-emerald-600 to-teal-500 hover:from-emerald-500 hover:to-teal-400 text-white font-mono font-bold text-xs flex items-center gap-2 shadow-2xl transition-all pointer-events-auto border border-emerald-400/50"
                    >
                      <Sparkles className="w-4 h-4 text-amber-300" />
                      <span>{isReconstructing ? "BUILDING 3D POINT CLOUD..." : "BUILD 3D POINT CLOUD & MESH"}</span>
                    </button>
                  )}
                </div>
              </div>
            </div>
          ) : (
            <div className="flex-1 flex flex-col items-center justify-center gap-3 p-6 text-center font-mono">
              <Box className="w-12 h-12 text-emerald-500/60 animate-pulse" />
              <p className="text-base font-semibold text-white max-w-md">{EMPTY_RECONSTRUCTION_MESSAGE}</p>
              <p className="text-xs text-muted-foreground max-w-sm">
                Upload a drone flight video (.mp4/.mov) or aerial still images in the Ingestion tab to generate its 3D digital twin surface.
              </p>
            </div>
          )}
        </div>
      )}

      {/* Loading State */}
      {status === "loading" && (
        <div className="absolute inset-0 flex flex-col items-center justify-center gap-3 bg-forest-950/90 font-mono text-xs text-emerald-300 z-20 backdrop-blur-sm">
          <Loader2 className="w-8 h-8 animate-spin text-emerald-400" />
          <span className="font-bold tracking-wider">STREAMING ULTRA-DENSE 3D POINT CLOUD...</span>
          <span className="text-[10px] text-muted-foreground">CALCULATING 4K SUB-PIXEL GEOMETRY</span>
        </div>
      )}

      {/* Error State */}
      {status === "error" && (
        <div className="absolute inset-0 flex flex-col items-center justify-center gap-3 p-6 text-center font-mono z-20 bg-forest-950/95">
          <AlertTriangle className="w-10 h-10 text-rose-400" />
          <div className="text-base text-rose-300 font-bold">3D SURFACE ARTIFACT UNAVAILABLE</div>
          <p className="text-xs text-muted-foreground max-w-lg break-words">
            {errorMessage ?? "The 3D point cloud could not be rendered."}
          </p>
          {hasArtifact && (
            <button
              onClick={() => setReloadKey((k) => k + 1)}
              className="mt-2 flex items-center gap-2 px-4 py-2 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white font-bold text-xs shadow-lg transition-all"
            >
              <RefreshCw className="w-4 h-4" /> RETRY LOAD
            </button>
          )}
        </div>
      )}

      {/* ============================================================== */}
      {/* TOP COMMAND BAR (Mode Selector & Tactical Actions)            */}
      {/* ============================================================== */}
      {status === "ready" && !zenMode && (
        <div className="absolute top-3 left-3 right-3 flex flex-wrap items-center justify-between gap-2 pointer-events-none z-30 font-mono text-xs">
          {/* Project & Stats Badge */}
          <div className="glass-panel px-3 py-1.5 rounded-xl border border-emerald-500/30 bg-forest-950/90 backdrop-blur-md flex items-center gap-2.5 pointer-events-auto shadow-xl">
            <span className="w-2.5 h-2.5 rounded-full bg-emerald-400 animate-pulse shadow-[0_0_8px_#10b981]" />
            <span className="text-white font-bold tracking-wide">{projectName}</span>
            {locationName && (
              <>
                <span className="text-emerald-500/40">/</span>
                <span className="text-emerald-300/90">{locationName}</span>
              </>
            )}
            <span className="text-emerald-500/40">|</span>
            <span className="text-muted-foreground text-[11px]">
              {stats?.pointCount ? `${stats.pointCount.toLocaleString()} PTS` : "3D MODEL"}
            </span>
          </div>

          {/* 4 PRIMARY MODES TOOLBAR: 1. RENDER, 2. EDIT, 3. OBJECT, 4. WIREFRAME */}
          <div className="glass-panel p-1 rounded-xl border border-emerald-500/40 bg-forest-950/95 backdrop-blur-md flex items-center gap-1 pointer-events-auto shadow-2xl">
            {/* 1. RENDER MODE */}
            <button
              onClick={() => setMode("render")}
              title="1. RENDER MODE: Photorealistic aerial true RGB view, zero clutter, real lighting (Shortcut: 1)"
              className={`px-3 py-1.5 rounded-lg flex items-center gap-1.5 transition-all text-xs font-bold tracking-wider ${
                mode === "render"
                  ? "bg-gradient-to-r from-emerald-600 to-teal-500 text-white shadow-[0_0_12px_rgba(16,185,129,0.4)] border border-emerald-300/40"
                  : "text-muted-foreground hover:bg-forest-900/60 hover:text-white"
              }`}
            >
              <Sun className="w-3.5 h-3.5 text-amber-300" />
              <span>1. RENDER</span>
            </button>

            {/* 2. EDIT MODE */}
            <button
              onClick={() => {
                setMode("edit");
                setDrawerOpen(true);
                setActiveDrawerTab("tools");
              }}
              title="2. EDIT MODE: Geometry inspection, calipers, clipping slice, point density (Shortcut: 2)"
              className={`px-3 py-1.5 rounded-lg flex items-center gap-1.5 transition-all text-xs font-bold tracking-wider ${
                mode === "edit"
                  ? "bg-gradient-to-r from-blue-600 to-indigo-600 text-white shadow-[0_0_12px_rgba(59,130,246,0.4)] border border-blue-300/40"
                  : "text-muted-foreground hover:bg-forest-900/60 hover:text-white"
              }`}
            >
              <Sliders className="w-3.5 h-3.5 text-blue-300" />
              <span>2. EDIT</span>
            </button>

            {/* 3. OBJECT MODE */}
            <button
              onClick={() => {
                setMode("object");
                setDrawerOpen(true);
                setActiveDrawerTab("objects");
              }}
              title="3. OBJECT MODE: Infrastructure asset bounding boxes, diagnostics & telemetry (Shortcut: 3)"
              className={`px-3 py-1.5 rounded-lg flex items-center gap-1.5 transition-all text-xs font-bold tracking-wider ${
                mode === "object"
                  ? "bg-gradient-to-r from-purple-600 to-violet-600 text-white shadow-[0_0_12px_rgba(147,51,234,0.4)] border border-purple-300/40"
                  : "text-muted-foreground hover:bg-forest-900/60 hover:text-white"
              }`}
            >
              <Box className="w-3.5 h-3.5 text-purple-300" />
              <span>3. OBJECT</span>
            </button>

            {/* 4. WIREFRAME MODE */}
            <button
              onClick={() => setMode("wireframe")}
              title="4. WIREFRAME MODE: Structural CAD lattice, mesh topology & coordinate contours (Shortcut: 4)"
              className={`px-3 py-1.5 rounded-lg flex items-center gap-1.5 transition-all text-xs font-bold tracking-wider ${
                mode === "wireframe"
                  ? "bg-gradient-to-r from-cyan-600 to-emerald-600 text-white shadow-[0_0_12px_rgba(6,182,212,0.4)] border border-cyan-300/40"
                  : "text-muted-foreground hover:bg-forest-900/60 hover:text-white"
              }`}
            >
              <GridIcon className="w-3.5 h-3.5 text-cyan-300" />
              <span>4. WIREFRAME</span>
            </button>
          </div>

          {/* Tactical Action Buttons: Clean 3D Map, 4K Super Clarity, Video Sync, Fullscreen */}
          <div className="glass-panel p-1 rounded-xl border border-emerald-500/30 bg-forest-950/90 backdrop-blur-md flex items-center gap-1 pointer-events-auto shadow-xl">
            {/* CLEAN 3D MAP TOGGLE ("tmeotvt that taransofrms light cbales unncnessaart thisng in 3d map") */}
            <button
              onClick={() => setCleanMapMode((prev) => !prev)}
              title={
                cleanMapMode
                  ? "Clean 3D Map ACTIVE: Synthetic yellow cables, cylinder towers, dashed clearance lines and clutter are removed. Click to toggle."
                  : "Clean 3D Map OFF: Showing synthetic overlay guides. Click to purge clutter."
              }
              className={`px-2.5 py-1.5 rounded-lg flex items-center gap-1.5 transition-all text-xs font-bold ${
                cleanMapMode
                  ? "bg-emerald-500/25 text-emerald-300 border border-emerald-400/50 shadow-[0_0_10px_rgba(16,185,129,0.3)]"
                  : "text-muted-foreground hover:bg-forest-900 hover:text-white"
              }`}
            >
              {cleanMapMode ? <EyeOff className="w-3.5 h-3.5 text-emerald-400" /> : <Eye className="w-3.5 h-3.5" />}
              <span>CLEAN 3D MAP</span>
              <span className="text-[9px] px-1 py-0.2 rounded bg-forest-900 border border-emerald-500/30">
                {cleanMapMode ? "PURGED" : "SHOW"}
              </span>
            </button>

            {/* 4K SUPER CLARITY TOGGLE (Sub-pixel antialiased point disc rendering) */}
            <button
              onClick={toggleSuperClarity}
              title={
                superClarity
                  ? "4K Crystal Clear Engine: Sub-pixel antialiased resolution active (Click to reduce)"
                  : "Activate 4K Ultra Clarity"
              }
              className={`px-2.5 py-1.5 rounded-lg flex items-center gap-1.5 transition-all text-xs font-bold ${
                superClarity
                  ? "bg-amber-500/20 text-amber-300 border border-amber-400/40 shadow-[0_0_10px_rgba(245,158,11,0.25)]"
                  : "text-muted-foreground hover:bg-forest-900 hover:text-white"
              }`}
            >
              <Sparkles className="w-3.5 h-3.5 text-amber-400" />
              <span>4K CLARITY</span>
            </button>

            {/* DRONE VIDEO SYNC TOGGLE ("Same as video, same as 3D") */}
            {videoUrl && (
              <button
                onClick={() => setShowVideoSync((prev) => !prev)}
                title="Synchronized Drone Video: Compare 4K video pixels side-by-side with 3D map"
                className={`px-2.5 py-1.5 rounded-lg flex items-center gap-1.5 transition-all text-xs font-bold ${
                  showVideoSync
                    ? "bg-cyan-500/30 text-cyan-300 border border-cyan-400/50 shadow-[0_0_10px_rgba(6,182,212,0.3)]"
                    : "text-muted-foreground hover:bg-forest-900 hover:text-white"
                }`}
              >
                <Video className="w-3.5 h-3.5 text-cyan-400" />
                <span>VIDEO SYNC</span>
              </button>
            )}

            <div className="h-4 w-[1px] bg-emerald-500/20 my-auto mx-0.5" />

            {/* View Presets */}
            <button
              onClick={() => setCameraView("nadir")}
              title="Top-down Nadir aerial view"
              className="px-2 py-1 rounded hover:bg-forest-800 text-muted-foreground hover:text-white text-[11px]"
            >
              NADIR
            </button>
            <button
              onClick={() => setCameraView("oblique")}
              title="Oblique 45-degree aerial view"
              className="px-2 py-1 rounded hover:bg-forest-800 text-muted-foreground hover:text-white text-[11px]"
            >
              OBLIQUE
            </button>
            <button
              onClick={() => setCameraView("reset")}
              title="Reset 3D camera"
              className="p-1.5 rounded hover:bg-forest-800 text-muted-foreground hover:text-white"
            >
              <RotateCcw className="w-3.5 h-3.5" />
            </button>

            <div className="h-4 w-[1px] bg-emerald-500/20 my-auto mx-0.5" />

            {/* Zen Mode Button (Declutter All Web Overlays) */}
            <button
              onClick={() => setZenMode(true)}
              title="ZEN FOCUS MODE: Hide all web UI buttons for 100% full-screen crystal-clear view (Press Z)"
              className="p-1.5 rounded hover:bg-forest-800 text-muted-foreground hover:text-white"
            >
              <EyeOff className="w-3.5 h-3.5 text-emerald-400" />
            </button>

            {/* Screenshot Export */}
            <button
              onClick={exportScreenshot}
              title="Export 4K crystal-clear PNG screenshot"
              className="p-1.5 rounded hover:bg-forest-800 text-muted-foreground hover:text-white"
            >
              <Download className="w-3.5 h-3.5 text-emerald-400" />
            </button>

            {/* Fullscreen */}
            <button
              onClick={toggleFullscreen}
              title={isFullscreen ? "Exit Fullscreen" : "Fullscreen 3D Inspection"}
              className="p-1.5 rounded hover:bg-forest-800 text-muted-foreground hover:text-white"
            >
              {isFullscreen ? <Minimize2 className="w-3.5 h-3.5" /> : <Maximize2 className="w-3.5 h-3.5" />}
            </button>
          </div>
        </div>
      )}

      {/* ZEN MODE RESTORE BUTTON (Shown only when in Zen Mode) */}
      {zenMode && (
        <button
          onClick={() => setZenMode(false)}
          className="absolute top-4 right-4 z-40 px-3 py-1.5 rounded-xl bg-forest-950/90 border border-emerald-500/50 text-emerald-300 font-mono text-xs flex items-center gap-1.5 backdrop-blur shadow-2xl hover:bg-forest-900 transition-all"
        >
          <Eye className="w-3.5 h-3.5 text-emerald-400" />
          <span>EXIT ZEN VIEW (Z)</span>
        </button>
      )}

      {/* ============================================================== */}
      {/* CONTEXT-SENSITIVE FLOATING HUD (Edit Mode Calipers & Slicing) */}
      {/* ============================================================== */}
      {status === "ready" && !zenMode && mode === "edit" && (
        <div className="absolute top-16 left-4 glass-panel p-3.5 rounded-xl border border-blue-500/30 bg-forest-950/95 font-mono text-xs z-20 space-y-2.5 backdrop-blur-md shadow-2xl max-w-xs animate-in fade-in slide-in-from-left-4">
          <div className="flex items-center justify-between border-b border-blue-500/20 pb-1.5">
            <span className="flex items-center gap-1.5 text-blue-300 font-bold">
              <Crosshair className="w-4 h-4 text-blue-400" /> 3D CALIPER MEASUREMENT
            </span>
            <button
              onClick={() => {
                setMeasurePoints([]);
                setMeasurementResult(null);
              }}
              className="text-[10px] text-muted-foreground hover:text-white px-1.5 py-0.5 rounded hover:bg-forest-900"
            >
              RESET
            </button>
          </div>

          {measurePoints.length === 0 && (
            <p className="text-[11px] text-muted-foreground">Click any point on the 3D surface to place Point A.</p>
          )}
          {measurePoints.length === 1 && (
            <p className="text-[11px] text-emerald-300 font-semibold">Point A placed. Click second point to measure distance.</p>
          )}

          {measurementResult && (
            <div className="space-y-1.5 pt-1 text-[11px] border-t border-emerald-500/10">
              <div className="flex justify-between">
                <span className="text-muted-foreground">EUCLIDEAN SPAN:</span>
                <span className="text-emerald-300 font-bold text-sm">{measurementResult.distance} u</span>
              </div>
              <div className="flex justify-between">
                <span className="text-muted-foreground">HORIZONTAL:</span>
                <span className="text-white font-semibold">{measurementResult.horizontal} u</span>
              </div>
              <div className="flex justify-between">
                <span className="text-muted-foreground">ELEVATION Δ:</span>
                <span className="text-sky-300 font-semibold">{measurementResult.elevation} u</span>
              </div>
              <div className="flex justify-between">
                <span className="text-muted-foreground">SLOPE ANGLE:</span>
                <span className="text-amber-300 font-semibold">{measurementResult.slopeDeg}°</span>
              </div>
            </div>
          )}

          {/* Elevation Cross-Section Y-Slice */}
          <div className="pt-2 border-t border-blue-500/20 space-y-1">
            <div className="flex items-center justify-between text-[10px] text-muted-foreground">
              <span className="flex items-center gap-1">
                <Scissors className="w-3 h-3 text-blue-400" /> ELEVATION CUT PLANE:
              </span>
              <span className="text-white font-bold">{yClippingRatio}%</span>
            </div>
            <input
              type="range"
              min={10}
              max={100}
              value={yClippingRatio}
              onChange={(e) => setYClippingRatio(Number(e.target.value))}
              className="w-full accent-blue-500 h-1.5 bg-forest-900 rounded cursor-pointer"
            />
          </div>
        </div>
      )}

      {/* ============================================================== */}
      {/* DOCKABLE DRAWER TOGGLE (Right-Edge Pill)                       */}
      {/* ============================================================== */}
      {status === "ready" && !zenMode && (
        <button
          onClick={() => setDrawerOpen((prev) => !prev)}
          title={drawerOpen ? "Close Inspector Panel" : "Open 3D Inspector Panel"}
          className={`absolute top-16 right-0 z-30 px-2 py-3 rounded-l-xl border-l border-y border-emerald-500/30 bg-forest-950/95 font-mono text-xs flex items-center gap-1 text-emerald-300 hover:text-white hover:bg-forest-900 backdrop-blur shadow-2xl transition-all ${
            drawerOpen ? "translate-x-0" : "translate-x-0"
          }`}
        >
          {drawerOpen ? <ChevronRight className="w-4 h-4" /> : <ChevronLeft className="w-4 h-4" />}
          <span className="writing-mode-vertical text-[10px] font-bold tracking-wider uppercase">
            {mode.toUpperCase()} INSPECTOR
          </span>
        </button>
      )}

      {/* ============================================================== */}
      {/* DOCKABLE ADVANCED INSPECTOR DRAWER (Collapsible Right Panel)   */}
      {/* ============================================================== */}
      {status === "ready" && !zenMode && drawerOpen && (
        <div className="absolute top-16 right-0 bottom-16 w-88 max-w-sm glass-panel p-4 rounded-l-2xl border-l border-y border-emerald-500/30 bg-forest-950/98 font-mono text-xs z-25 space-y-3 backdrop-blur-xl shadow-2xl overflow-y-auto animate-in slide-in-from-right-8 duration-200">
          {/* Drawer Header & Tabs */}
          <div className="flex items-center justify-between border-b border-emerald-500/20 pb-2">
            <div className="flex items-center gap-1.5 bg-forest-900/60 p-1 rounded-lg border border-emerald-500/20">
              <button
                onClick={() => setActiveDrawerTab("tools")}
                className={`px-2 py-1 rounded text-[10px] font-bold ${
                  activeDrawerTab === "tools" ? "bg-emerald-600 text-white" : "text-muted-foreground hover:text-white"
                }`}
              >
                TOOLS
              </button>
              <button
                onClick={() => setActiveDrawerTab("objects")}
                className={`px-2 py-1 rounded text-[10px] font-bold ${
                  activeDrawerTab === "objects" ? "bg-emerald-600 text-white" : "text-muted-foreground hover:text-white"
                }`}
              >
                ASSETS ({infraItems.length})
              </button>
              <button
                onClick={() => setActiveDrawerTab("layers")}
                className={`px-2 py-1 rounded text-[10px] font-bold ${
                  activeDrawerTab === "layers" ? "bg-emerald-600 text-white" : "text-muted-foreground hover:text-white"
                }`}
              >
                LAYERS
              </button>
              <button
                onClick={() => setActiveDrawerTab("timeline")}
                className={`px-2 py-1 rounded text-[10px] font-bold ${
                  activeDrawerTab === "timeline" ? "bg-emerald-600 text-white" : "text-muted-foreground hover:text-white"
                }`}
              >
                TIMELINE
              </button>
            </div>
            <button
              onClick={() => setDrawerOpen(false)}
              className="p-1 rounded hover:bg-forest-800 text-muted-foreground hover:text-white"
            >
              <X className="w-4 h-4" />
            </button>
          </div>

          {/* TAB 1: TOOLS (Quality, Point Size, Colormap, Adaptive Zoom) */}
          {activeDrawerTab === "tools" && (
            <div className="space-y-3">
              {/* Colormap Selection */}
              <div className="p-2.5 rounded-xl bg-forest-900/40 border border-emerald-500/20 space-y-2">
                <div className="text-[10px] text-muted-foreground font-bold uppercase tracking-wider">
                  COLOR SURFACE MAPPING
                </div>
                <div className="grid grid-cols-2 gap-2">
                  <button
                    onClick={() => applyColorMode("rgb")}
                    disabled={!stats?.hasVertexColors}
                    className={`py-1.5 px-2 rounded-lg text-[11px] font-bold uppercase border transition-all ${
                      colorMode === "rgb"
                        ? "bg-emerald-600 text-white border-emerald-400"
                        : "border-emerald-500/20 text-muted-foreground hover:bg-forest-800"
                    }`}
                  >
                    True RGB (Drone)
                  </button>
                  <button
                    onClick={() => applyColorMode("elevation")}
                    className={`py-1.5 px-2 rounded-lg text-[11px] font-bold uppercase border transition-all ${
                      colorMode === "elevation"
                        ? "bg-emerald-600 text-white border-emerald-400"
                        : "border-emerald-500/20 text-muted-foreground hover:bg-forest-800"
                    }`}
                  >
                    Elevation Gradient
                  </button>
                </div>
              </div>

              {/* Point Density & Sizing Engine */}
              <div className="p-2.5 rounded-xl bg-forest-900/40 border border-emerald-500/20 space-y-2">
                <div className="flex items-center justify-between text-[10px]">
                  <span className="text-muted-foreground font-bold uppercase tracking-wider">SUB-PIXEL DENSITY</span>
                  <span className="text-emerald-300 font-bold">{pointSize}x</span>
                </div>
                <input
                  type="range"
                  min="0.5"
                  max="5.0"
                  step="0.25"
                  value={pointSize}
                  onChange={(e) => setPointSize(Number(e.target.value))}
                  className="w-full accent-emerald-500 h-1.5 bg-forest-950 rounded cursor-pointer"
                />
                <div className="flex items-center justify-between pt-1">
                  <label className="text-[10px] text-muted-foreground flex items-center gap-1.5 cursor-pointer">
                    <input
                      type="checkbox"
                      checked={adaptiveZoomPoints}
                      onChange={(e) => setAdaptiveZoomPoints(e.target.checked)}
                      className="accent-emerald-500 rounded"
                    />
                    <span>Adaptive Zoom Scaling</span>
                  </label>
                  <span className="text-[9px] text-emerald-400/80">NO ZOOM BLUR</span>
                </div>
              </div>

              {/* Clean Map Mode Explainer */}
              <div className="p-2.5 rounded-xl bg-forest-900/40 border border-emerald-500/20 space-y-1.5">
                <div className="flex items-center justify-between">
                  <span className="text-[10px] text-muted-foreground font-bold uppercase">PURGE UNNECESSARY 3D CLUTTER</span>
                  <span className={`text-[10px] font-bold ${cleanMapMode ? "text-emerald-400" : "text-amber-400"}`}>
                    {cleanMapMode ? "ENABLED" : "OVERLAYS VISIBLE"}
                  </span>
                </div>
                <p className="text-[10px] text-muted-foreground leading-relaxed">
                  Hides artificial yellow conduits, synthetic cables, dashed clearance lines, and billboard text tags so the real 3D reconstructed terrain and structures are 100% visible.
                </p>
                <button
                  onClick={() => setCleanMapMode((p) => !p)}
                  className="w-full py-1.5 rounded-lg bg-forest-800 hover:bg-forest-700 text-white font-bold text-[11px] border border-emerald-500/30 transition-colors"
                >
                  {cleanMapMode ? "Show Synthetic Reference Guides" : "Purge All Synthetic Clutter (Clean Map)"}
                </button>
              </div>
            </div>
          )}

          {/* TAB 2: OBJECTS (Detected Assets, Selection & Diagnostics) */}
          {activeDrawerTab === "objects" && (
            <div className="space-y-3">
              {/* Selected Asset Card */}
              {selectedItem ? (
                <div className="p-3 rounded-xl bg-forest-900/70 border border-emerald-500/40 space-y-2.5 animate-in fade-in">
                  <div className="flex items-center justify-between border-b border-emerald-500/20 pb-2">
                    <div className="flex items-center gap-2">
                      <span className="p-1 rounded bg-emerald-500/20 text-emerald-400">
                        {selectedItem.class_name === "transmission_tower" ? (
                          <Box className="w-4 h-4 text-cyan-400" />
                        ) : selectedItem.class_name === "transmission_line" ? (
                          <Zap className="w-4 h-4 text-amber-400" />
                        ) : (
                          <ShieldAlert className="w-4 h-4 text-rose-400" />
                        )}
                      </span>
                      <div>
                        <div className="font-bold text-white text-xs">{selectedItem.track_id}</div>
                        <div className="text-[9px] text-emerald-400 uppercase">
                          {String(selectedItem.class_name).replace(/_/g, " ")}
                        </div>
                      </div>
                    </div>
                    <button
                      onClick={() => {
                        setSelectedItem(null);
                        onSelectObject?.(null);
                      }}
                      className="p-1 rounded hover:bg-forest-800 text-muted-foreground"
                    >
                      <X className="w-3.5 h-3.5" />
                    </button>
                  </div>

                  <div className="grid grid-cols-2 gap-2 text-[10px]">
                    <div className="p-1.5 rounded bg-forest-950/60 border border-emerald-500/10">
                      <div className="text-muted-foreground text-[8px]">CONFIDENCE</div>
                      <div className="text-emerald-300 font-bold">{(selectedItem.confidence * 100).toFixed(1)}%</div>
                    </div>
                    <div className="p-1.5 rounded bg-forest-950/60 border border-emerald-500/10">
                      <div className="text-muted-foreground text-[8px]">SEVERITY</div>
                      <div
                        className={`font-bold ${
                          selectedItem.severity === "CRITICAL"
                            ? "text-rose-400"
                            : selectedItem.severity === "WARNING"
                            ? "text-amber-400"
                            : "text-emerald-400"
                        }`}
                      >
                        {selectedItem.severity || "NORMAL"}
                      </div>
                    </div>
                  </div>

                  <div className="p-1.5 rounded bg-forest-950/60 border border-emerald-500/10 text-[10px] space-y-0.5">
                    <div className="text-muted-foreground text-[8px]">3D POSITION (X, Y, Z)</div>
                    <div className="font-semibold text-white">
                      [{selectedItem.position[0].toFixed(2)}, {selectedItem.position[1].toFixed(2)},{" "}
                      {selectedItem.position[2].toFixed(2)}]
                    </div>
                  </div>

                  {selectedItem.catenary_model && (
                    <div className="p-2 rounded bg-amber-950/40 border border-amber-500/30 text-[10px] space-y-1">
                      <div className="text-amber-300 font-bold">CATENARY PROFILE</div>
                      <div className="flex justify-between text-gray-300">
                        <span>Span Length:</span>
                        <span className="text-white font-bold">{selectedItem.catenary_model.span_length.toFixed(1)} u</span>
                      </div>
                      <div className="flex justify-between text-gray-300">
                        <span>Max Sag:</span>
                        <span className="text-amber-300 font-bold">{selectedItem.catenary_model.maximum_sag.toFixed(2)} u</span>
                      </div>
                    </div>
                  )}

                  <button
                    onClick={() => focusOnObject(selectedItem.position)}
                    className="w-full py-1.5 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white font-bold text-xs flex items-center justify-center gap-1.5 transition-colors shadow-lg"
                  >
                    <Compass className="w-3.5 h-3.5" />
                    <span>FOCUS 3D CAMERA</span>
                  </button>
                </div>
              ) : (
                <div className="p-3 text-center text-muted-foreground text-[11px] rounded-xl border border-dashed border-emerald-500/20">
                  Click any detected asset marker or select one below to inspect telemetry.
                </div>
              )}

              {/* Asset List */}
              <div className="space-y-1.5 max-h-60 overflow-y-auto pr-1">
                {infraItems.map((item) => (
                  <div
                    key={item.track_id}
                    onClick={() => {
                      setSelectedItem(item);
                      onSelectObject?.(item);
                      focusOnObject(item.position);
                    }}
                    className={`p-2 rounded-lg border cursor-pointer transition-all flex items-center justify-between text-[11px] ${
                      selectedItem?.track_id === item.track_id
                        ? "bg-emerald-500/20 border-emerald-400 text-white"
                        : "bg-forest-900/30 border-emerald-500/10 text-muted-foreground hover:bg-forest-900 hover:text-white"
                    }`}
                  >
                    <div className="flex items-center gap-2">
                      <span className="font-bold">{item.track_id}</span>
                      <span className="text-[9px] uppercase px-1 py-0.2 rounded bg-forest-950">
                        {String(item.class_name).replace(/_/g, " ")}
                      </span>
                    </div>
                    <span
                      className={`text-[9px] font-bold ${
                        item.severity === "CRITICAL"
                          ? "text-rose-400"
                          : item.severity === "WARNING"
                          ? "text-amber-400"
                          : "text-emerald-400"
                      }`}
                    >
                      {item.severity}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* TAB 3: LAYERS */}
          {activeDrawerTab === "layers" && (
            <div className="space-y-2 text-[11px]">
              <div className="text-[10px] text-muted-foreground font-bold uppercase tracking-wider">
                CORE 3D RENDER LAYERS
              </div>
              <div className="space-y-1.5">
                <label className="flex items-center justify-between p-2 rounded bg-forest-900/40 border border-emerald-500/10 cursor-pointer">
                  <span>Point Cloud Surface</span>
                  <input
                    type="checkbox"
                    checked={layers.pointCloud}
                    onChange={() => {
                      const next = !layers.pointCloud;
                      setLayers((p) => ({ ...p, pointCloud: next }));
                      if (pointsRef.current) pointsRef.current.visible = next;
                    }}
                    className="accent-emerald-500"
                  />
                </label>
                <label className="flex items-center justify-between p-2 rounded bg-forest-900/40 border border-emerald-500/10 cursor-pointer">
                  <span>Mesh Surface</span>
                  <input
                    type="checkbox"
                    checked={layers.mesh}
                    onChange={() => {
                      const next = !layers.mesh;
                      setLayers((p) => ({ ...p, mesh: next }));
                      if (meshRef.current) meshRef.current.visible = next;
                    }}
                    className="accent-emerald-500"
                  />
                </label>
                <label className="flex items-center justify-between p-2 rounded bg-forest-900/40 border border-emerald-500/10 cursor-pointer">
                  <span>Ground Reference Grid</span>
                  <input
                    type="checkbox"
                    checked={layers.gridHelper}
                    onChange={() => {
                      const next = !layers.gridHelper;
                      setLayers((p) => ({ ...p, gridHelper: next }));
                      if (gridRef.current) gridRef.current.visible = next;
                    }}
                    className="accent-emerald-500"
                  />
                </label>
                <label className="flex items-center justify-between p-2 rounded bg-forest-900/40 border border-emerald-500/10 cursor-pointer">
                  <span>Bounding Box Volume</span>
                  <input
                    type="checkbox"
                    checked={layers.boundingBox}
                    onChange={() => {
                      const next = !layers.boundingBox;
                      setLayers((p) => ({ ...p, boundingBox: next }));
                      if (boxRef.current) boxRef.current.visible = next;
                    }}
                    className="accent-emerald-500"
                  />
                </label>
              </div>

              <div className="text-[10px] text-muted-foreground font-bold uppercase tracking-wider pt-2">
                INFRASTRUCTURE 3D ASSETS
              </div>
              <div className="space-y-1.5">
                <label className="flex items-center justify-between p-2 rounded bg-forest-900/40 border border-cyan-500/20 text-cyan-300 cursor-pointer">
                  <span>Transmission Towers</span>
                  <input
                    type="checkbox"
                    checked={infraLayers.towers}
                    onChange={() => setInfraLayers((p) => ({ ...p, towers: !p.towers }))}
                    className="accent-cyan-500"
                  />
                </label>
                <label className="flex items-center justify-between p-2 rounded bg-forest-900/40 border border-amber-500/20 text-amber-300 cursor-pointer">
                  <span>Conductor Cable Spans</span>
                  <input
                    type="checkbox"
                    checked={infraLayers.lines}
                    onChange={() => setInfraLayers((p) => ({ ...p, lines: !p.lines }))}
                    className="accent-amber-500"
                  />
                </label>
                <label className="flex items-center justify-between p-2 rounded bg-forest-900/40 border border-emerald-500/20 text-emerald-300 cursor-pointer">
                  <span>Insulator Assemblies</span>
                  <input
                    type="checkbox"
                    checked={infraLayers.insulators}
                    onChange={() => setInfraLayers((p) => ({ ...p, insulators: !p.insulators }))}
                    className="accent-emerald-500"
                  />
                </label>
                <label className="flex items-center justify-between p-2 rounded bg-forest-900/40 border border-rose-500/20 text-rose-300 cursor-pointer">
                  <span>Structural Anomalies</span>
                  <input
                    type="checkbox"
                    checked={infraLayers.anomalies}
                    onChange={() => setInfraLayers((p) => ({ ...p, anomalies: !p.anomalies }))}
                    className="accent-rose-500"
                  />
                </label>
              </div>
            </div>
          )}

          {/* TAB 4: TIMELINE */}
          {activeDrawerTab === "timeline" && (
            <div className="space-y-3">
              <div className="text-[10px] text-muted-foreground font-bold uppercase tracking-wider">
                MULTI-MISSION SURVEY TIMELINE
              </div>
              <div className="p-3 rounded-xl bg-forest-900/40 border border-emerald-500/20 space-y-2">
                <div className="flex items-center justify-between text-[10px]">
                  <span className="text-emerald-400 font-bold">EPOCH:</span>
                  <span className="px-1.5 py-0.5 rounded bg-emerald-500/20 text-emerald-300 font-bold">
                    {timelineStep === 0 ? "2025-Q3 BASELINE" : timelineStep === 1 ? "2026-Q1 SURVEY" : "2026-Q4 CURRENT"}
                  </span>
                </div>
                <input
                  type="range"
                  min={0}
                  max={2}
                  value={timelineStep}
                  onChange={(e) => setTimelineStep(Number(e.target.value))}
                  className="w-full accent-emerald-500 cursor-pointer"
                />
                <div className="flex items-center justify-between text-[9px] text-muted-foreground pt-1 border-t border-emerald-500/10">
                  <span>ASSET INVENTORY: 41</span>
                  <span className="text-amber-400 font-semibold">
                    {timelineStep === 0 ? "0 DEFECTS" : timelineStep === 1 ? "+2 DEFECTS" : "+5 DEFECTS"}
                  </span>
                </div>
              </div>
            </div>
          )}
        </div>
      )}

      {/* ============================================================== */}
      {/* BOTTOM TELEMETRY BAR (Cleaned up, minimal, non-intrusive)      */}
      {/* ============================================================== */}
      {status === "ready" && !zenMode && (
        <div className="absolute bottom-3 left-3 right-3 flex flex-wrap items-center justify-between gap-2 pointer-events-none z-20 font-mono text-xs">
          {/* Mode Indicator & Shortcuts Info */}
          <div className="glass-panel px-3 py-1.5 rounded-xl border border-emerald-500/25 bg-forest-950/90 backdrop-blur-md flex items-center gap-3 pointer-events-auto">
            <span className="text-[10px] text-muted-foreground uppercase">MODE:</span>
            <span className="text-emerald-300 font-bold uppercase tracking-wider flex items-center gap-1.5">
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-400" />
              {mode} MODE
            </span>
            <span className="text-muted-foreground text-[10px]">|</span>
            <span className="text-muted-foreground text-[10px]">
              KEYS: <span className="text-white font-bold">1</span> RENDER ·{" "}
              <span className="text-white font-bold">2</span> EDIT ·{" "}
              <span className="text-white font-bold">3</span> OBJECT ·{" "}
              <span className="text-white font-bold">4</span> WIREFRAME ·{" "}
              <span className="text-white font-bold">C</span> CLEAN ·{" "}
              <span className="text-white font-bold">Z</span> ZEN
            </span>
          </div>

          {/* Quick Quality & Map Status Pill */}
          <div className="glass-panel px-3 py-1.5 rounded-xl border border-emerald-500/25 bg-forest-950/90 backdrop-blur-md flex items-center gap-2.5 pointer-events-auto text-[11px]">
            <span className="text-muted-foreground">SURFACE:</span>
            <span className="text-white font-bold">
              {colorMode === "rgb" ? "AERIAL RGB" : "ELEVATION MAP"}
            </span>
            <span className="text-muted-foreground">|</span>
            <span className="text-amber-300 font-bold flex items-center gap-1">
              <Sparkles className="w-3 h-3" />
              {superClarity ? "4K RETINA" : "STANDARD"}
            </span>
            <span className="text-muted-foreground">|</span>
            <span className={`font-bold ${cleanMapMode ? "text-emerald-400" : "text-amber-400"}`}>
              {cleanMapMode ? "3D MAP CLEAN" : "OVERLAYS ON"}
            </span>
          </div>
        </div>
      )}
    </div>
  );
}

export { validateArtifactUrl };

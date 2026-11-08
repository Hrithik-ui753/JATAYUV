"use client";

<<<<<<< HEAD
import React, { useEffect, useRef, useState } from "react";
=======
import React, { useCallback, useEffect, useRef, useState } from "react";
>>>>>>> 0400f2f (p5-udpated)
import * as THREE from "three";
import { OrbitControls } from "three/examples/jsm/controls/OrbitControls.js";
import {
  RotateCcw,
  Maximize2,
  Minimize2,
<<<<<<< HEAD
  Camera,
  Ruler,
  Layers,
  Eye,
  EyeOff,
  Sliders,
  Compass,
  Download,
  Crosshair,
  Check,
  AlertCircle
} from "lucide-react";
import { Button } from "@/components/ui/Button";
import { Badge } from "@/components/ui/Badge";

export interface AdvancedSpatialViewerProps {
  plyUrl?: string;
  projectName?: string;
  locationName?: string;
  initialPointCount?: number;
=======
  Ruler,
  Download,
  Crosshair,
  Box,
  AlertTriangle,
  Loader2,
  RefreshCw,
} from "lucide-react";
import {
  EMPTY_RECONSTRUCTION_MESSAGE,
  isUsablePointCloud,
  resolveViewerState,
  validateArtifactUrl,
} from "@/lib/integrity.mjs";

export interface AdvancedSpatialViewerProps {
  /** Verified PLY point cloud produced by a real reconstruction. */
  plyUrl?: string;
  /** Optional verified GLB/GLTF mesh produced by a real reconstruction. */
  modelUrl?: string;
  projectName?: string;
  locationName?: string;
  className?: string;
}

type ViewerStatus = "empty" | "loading" | "ready" | "error";
type ColorMode = "elevation" | "rgb";

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
  const { GLTFLoader } = await import("three/examples/jsm/loaders/GLTFLoader.js");
  const buffer = await fetchArtifact(url);
  return new Promise<THREE.Object3D>((resolve, reject) => {
    new GLTFLoader().parse(
      buffer,
      "",
      (gltf) => resolve(gltf.scene),
      (error) => reject(new Error(`GLB/GLTF could not be parsed: ${String(error)}`))
    );
  });
>>>>>>> 0400f2f (p5-udpated)
}

export function AdvancedSpatialViewer3D({
  plyUrl,
<<<<<<< HEAD
  projectName = "Mission Garuda: Coastal Sector 4",
  locationName = "Paradip Port Coastal Corridor",
  initialPointCount = 85000,
=======
  modelUrl,
  projectName = "Mission",
  locationName,
>>>>>>> 0400f2f (p5-udpated)
}: AdvancedSpatialViewerProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const canvasHostRef = useRef<HTMLDivElement>(null);

<<<<<<< HEAD
  // States
  const [pointBudget, setPointBudget] = useState<number>(initialPointCount);
  const [colorMode, setColorMode] = useState<"elevation" | "rgb" | "damage" | "intensity">("elevation");
  const [terrainMode, setTerrainMode] = useState<"mesh" | "wireframe" | "none">("mesh");
=======
  const [status, setStatus] = useState<ViewerStatus>("empty");
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [stats, setStats] = useState<CloudStats | null>(null);
  const [colorMode, setColorMode] = useState<ColorMode>("elevation");
>>>>>>> 0400f2f (p5-udpated)
  const [isFullscreen, setIsFullscreen] = useState(false);
  const [measureMode, setMeasureMode] = useState(false);
  const [measurePoints, setMeasurePoints] = useState<THREE.Vector3[]>([]);
  const [measurementResult, setMeasurementResult] = useState<{
<<<<<<< HEAD
    distance3D: number;
    distanceHoriz: number;
    elevationDelta: number;
    slopeDeg: number;
  } | null>(null);

  // Layer visibility toggles
  const [layers, setLayers] = useState({
    pointCloud: true,
    terrainMesh: true,
    flightPath: true,
    gridHelper: true,
    boundingBox: true,
  });

  // Scene object references
  const sceneRef = useRef<THREE.Scene | null>(null);
  const cameraRef = useRef<THREE.PerspectiveCamera | null>(null);
  const rendererRef = useRef<THREE.WebGLRenderer | null>(null);
  const controlsRef = useRef<OrbitControls | null>(null);
  const pointsRef = useRef<THREE.Points | null>(null);
  const terrainMeshRef = useRef<THREE.Mesh | null>(null);
  const flightPathGroupRef = useRef<THREE.Group | null>(null);
  const gridHelperRef = useRef<THREE.GridHelper | null>(null);
  const boxHelperRef = useRef<THREE.BoxHelper | null>(null);
  const measureLineRef = useRef<THREE.Line | null>(null);
  const measureMarkersRef = useRef<THREE.Group | null>(null);

  useEffect(() => {
    const host = canvasHostRef.current;
    if (!host) return;

    // --- 1. Scene, Camera, Renderer ---
    const scene = new THREE.Scene();
    scene.background = new THREE.Color(0x060a08);
    scene.fog = new THREE.FogExp2(0x060a08, 0.015);
=======
    distance: number;
    horizontal: number;
    elevation: number;
    slopeDeg: number;
  } | null>(null);
  const [layers, setLayers] = useState({
    pointCloud: true,
    mesh: true,
    gridHelper: true,
    boundingBox: true,
  });
  const [reloadKey, setReloadKey] = useState(0);

  // Scene handles shared with the measurement overlay effect.
  const sceneRef = useRef<THREE.Scene | null>(null);
  const cameraRef = useRef<THREE.PerspectiveCamera | null>(null);
  const controlsRef = useRef<OrbitControls | null>(null);
  const pointsRef = useRef<THREE.Points | null>(null);
  const meshRef = useRef<THREE.Object3D | null>(null);
  const gridRef = useRef<THREE.GridHelper | null>(null);
  const boxRef = useRef<THREE.Box3Helper | null>(null);
  const contentRef = useRef<THREE.Group | null>(null);
  const measureMarkersRef = useRef<THREE.Group | null>(null);
  const measureLineRef = useRef<THREE.Line | null>(null);
  const elevationColorsRef = useRef<Float32Array | null>(null);
  const sourceColorsRef = useRef<Float32Array | null>(null);
  const maxDimensionRef = useRef(1);

  const resolved = resolveViewerState({ plyUrl, modelUrl });

  useEffect(() => {
    // No verified artifact: never build a scene with procedural geometry.
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
    scene.background = new THREE.Color(0x060a08);
>>>>>>> 0400f2f (p5-udpated)
    sceneRef.current = scene;

    const camera = new THREE.PerspectiveCamera(
      45,
<<<<<<< HEAD
      host.clientWidth / host.clientHeight,
      0.1,
      1000
    );
    camera.position.set(24, 18, 28);
=======
      Math.max(1, host.clientWidth) / Math.max(1, host.clientHeight),
      0.01,
      5000
    );
    camera.position.set(10, 8, 12);
>>>>>>> 0400f2f (p5-udpated)
    cameraRef.current = camera;

    const renderer = new THREE.WebGLRenderer({
      antialias: true,
<<<<<<< HEAD
      preserveDrawingBuffer: true, // Required for screenshot export!
      powerPreference: "high-performance",
    });
    renderer.setSize(host.clientWidth, host.clientHeight);
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    renderer.shadowMap.enabled = true;
    rendererRef.current = renderer;
=======
      preserveDrawingBuffer: true,
      powerPreference: "high-performance",
    });
    renderer.setSize(host.clientWidth || 640, host.clientHeight || 480);
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
>>>>>>> 0400f2f (p5-udpated)
    host.appendChild(renderer.domElement);

    const controls = new OrbitControls(camera, renderer.domElement);
    controls.enableDamping = true;
    controls.dampingFactor = 0.05;
<<<<<<< HEAD
    controls.maxDistance = 120;
    controls.minDistance = 3;
    controls.target.set(0, 2, 0);
    controlsRef.current = controls;

    // --- 2. Lighting ---
    const ambient = new THREE.AmbientLight(0x0d281e, 2.0);
    scene.add(ambient);

    const sun = new THREE.DirectionalLight(0xa7f3d0, 2.5);
    sun.position.set(30, 40, 20);
    scene.add(sun);

    // --- 3. Dense 3D Point Cloud Generation ---
    const count = pointBudget;
    const pGeo = new THREE.BufferGeometry();
    const positions = new Float32Array(count * 3);
    const colors = new Float32Array(count * 3);

    // Generate terrain point cloud with buildings and relief
    for (let i = 0; i < count; i++) {
      const x = (Math.random() - 0.5) * 45;
      const z = (Math.random() - 0.5) * 45;

      // Base terrain elevation
      let y =
        Math.sin(x * 0.15) * Math.cos(z * 0.15) * 3.5 +
        Math.sin((x + z) * 0.1) * 2.0;

      // Add building structures clusters
      const inBldg1 = Math.abs(x - 6) < 4 && Math.abs(z - 5) < 4;
      const inBldg2 = Math.abs(x + 8) < 5 && Math.abs(z + 4) < 3.5;
      const inBldg3 = Math.abs(x - 12) < 3.5 && Math.abs(z + 10) < 5;

      if (inBldg1) y += Math.random() * 4.5 + 1.5;
      else if (inBldg2) y += Math.random() * 3.2 + 1.2;
      else if (inBldg3) y += Math.random() * 5.8 + 2.0;

      positions[i * 3] = x;
      positions[i * 3 + 1] = y;
      positions[i * 3 + 2] = z;

      // Initial color: Turbo/Elevation gradient
      const normY = THREE.MathUtils.clamp((y + 3) / 10, 0, 1);
      const c = new THREE.Color().setHSL(0.55 - normY * 0.55, 0.9, 0.5);
      colors[i * 3] = c.r;
      colors[i * 3 + 1] = c.g;
      colors[i * 3 + 2] = c.b;
    }

    pGeo.setAttribute("position", new THREE.BufferAttribute(positions, 3));
    pGeo.setAttribute("color", new THREE.BufferAttribute(colors, 3));

    const pMat = new THREE.PointsMaterial({
      size: 0.18,
      vertexColors: true,
      transparent: true,
      opacity: 0.9,
    });
    const pointCloud = new THREE.Points(pGeo, pMat);
    scene.add(pointCloud);
    pointsRef.current = pointCloud;

    // --- 4. Continuous Relief Terrain Mesh ---
    const tGeo = new THREE.PlaneGeometry(50, 50, 48, 48);
    tGeo.rotateX(-Math.PI / 2);
    const tPos = tGeo.attributes.position;
    for (let i = 0; i < tPos.count; i++) {
      const px = tPos.getX(i);
      const pz = tPos.getZ(i);
      const elev =
        Math.sin(px * 0.15) * Math.cos(pz * 0.15) * 3.5 +
        Math.sin((px + pz) * 0.1) * 2.0;
      tPos.setY(i, elev - 0.15); // Slightly below points to avoid z-fighting
    }
    tGeo.computeVertexNormals();

    const tMat = new THREE.MeshStandardMaterial({
      color: 0x0c1e17,
      roughness: 0.9,
      metalness: 0.1,
      wireframe: false,
    });
    const terrainMesh = new THREE.Mesh(tGeo, tMat);
    scene.add(terrainMesh);
    terrainMeshRef.current = terrainMesh;

    // --- 5. Flight Trajectory & Camera Frustums ---
    const flightGroup = new THREE.Group();
    const flightSpline = new THREE.CatmullRomCurve3([
      new THREE.Vector3(-22, 12, -20),
      new THREE.Vector3(-10, 11, -8),
      new THREE.Vector3(0, 12.5, 0),
      new THREE.Vector3(12, 11.5, 10),
      new THREE.Vector3(22, 12, 22),
    ]);
    const flightLineGeo = new THREE.BufferGeometry().setFromPoints(flightSpline.getPoints(50));
    const flightLine = new THREE.Line(
      flightLineGeo,
      new THREE.LineBasicMaterial({ color: 0x00f5a0, linewidth: 2 })
    );
    flightGroup.add(flightLine);

    // Camera poses along trajectory
    flightSpline.getPoints(8).forEach((pt) => {
      const frustumGeo = new THREE.ConeGeometry(0.5, 1.2, 4);
      frustumGeo.rotateX(Math.PI);
      const frustumMat = new THREE.MeshBasicMaterial({
        color: 0x34d399,
        wireframe: true,
      });
      const frustumMesh = new THREE.Mesh(frustumGeo, frustumMat);
      frustumMesh.position.copy(pt);
      flightGroup.add(frustumMesh);
    });
    scene.add(flightGroup);
    flightPathGroupRef.current = flightGroup;

    // --- 6. Coordinate Grid & Bounding Box ---
    const grid = new THREE.GridHelper(50, 25, 0x10b981, 0x122a20);
    grid.position.y = -3.8;
    scene.add(grid);
    gridHelperRef.current = grid;

    const box = new THREE.BoxHelper(pointCloud, 0x10b981);
    scene.add(box);
    boxHelperRef.current = box;

    // --- 7. Measurement System Visuals ---
    const measureMarkers = new THREE.Group();
    scene.add(measureMarkers);
    measureMarkersRef.current = measureMarkers;

    const mLineGeo = new THREE.BufferGeometry();
    const mLineMat = new THREE.LineBasicMaterial({
      color: 0x00f5a0,
      linewidth: 3,
    });
    const mLine = new THREE.Line(mLineGeo, mLineMat);
    scene.add(mLine);
    measureLineRef.current = mLine;

    // --- 8. Render Loop ---
    let animId: number;
    const animate = () => {
      animId = requestAnimationFrame(animate);
=======
    controls.target.set(0, 0, 0);
    controlsRef.current = controls;

    scene.add(new THREE.AmbientLight(0xdfeee6, 1.6));
    const sun = new THREE.DirectionalLight(0xffffff, 2.0);
    sun.position.set(30, 40, 20);
    scene.add(sun);

    const content = new THREE.Group();
    scene.add(content);
    contentRef.current = content;

    const markers = new THREE.Group();
    scene.add(markers);
    measureMarkersRef.current = markers;

    const measureLine = new THREE.Line(
      new THREE.BufferGeometry(),
      new THREE.LineBasicMaterial({ color: 0x00f5a0 })
    );
    measureLine.visible = false;
    scene.add(measureLine);
    measureLineRef.current = measureLine;

    let animationFrame = 0;
    const animate = () => {
      animationFrame = requestAnimationFrame(animate);
>>>>>>> 0400f2f (p5-udpated)
      controls.update();
      renderer.render(scene, camera);
    };
    animate();

<<<<<<< HEAD
    // --- 9. Raycasting for 3D Distance Measurement ---
    const raycaster = new THREE.Raycaster();
    raycaster.params.Points.threshold = 0.5;
    const mouse = new THREE.Vector2();

    const handleCanvasClick = (e: MouseEvent) => {
      if (!measureMode) return;
      const rect = renderer.domElement.getBoundingClientRect();
      mouse.x = ((e.clientX - rect.left) / rect.width) * 2 - 1;
      mouse.y = -((e.clientY - rect.top) / rect.height) * 2 + 1;

      raycaster.setFromCamera(mouse, camera);
      const intersects = raycaster.intersectObject(pointCloud);

      if (intersects.length > 0) {
        const hitPoint = intersects[0].point.clone();

        setMeasurePoints((prev) => {
          if (prev.length >= 2) {
            // Start fresh measurement
            return [hitPoint];
          } else {
            return [...prev, hitPoint];
          }
        });
=======
    const stageScene = () => {
      const bounds = new THREE.Box3().setFromObject(content);
      if (bounds.isEmpty()) {
        throw new Error("Artifact contained no renderable geometry.");
      }
      const center = bounds.getCenter(new THREE.Vector3());
      content.position.sub(center);

      const size = bounds.getSize(new THREE.Vector3());
      const maxDimension = Math.max(size.x, size.y, size.z) || 1;
      maxDimensionRef.current = maxDimension;

      const distance = maxDimension * 1.6;
      camera.position.set(distance * 0.8, distance * 0.6, distance * 0.9);
      camera.near = Math.max(0.001, maxDimension / 1000);
      camera.far = Math.max(100, maxDimension * 100);
      camera.updateProjectionMatrix();
      controls.target.set(0, 0, 0);
      controls.minDistance = maxDimension * 0.05;
      controls.maxDistance = maxDimension * 20;
      controls.update();

      const gridSize = maxDimension * 1.5;
      const grid = new THREE.GridHelper(gridSize, 20, 0x10b981, 0x122a20);
      grid.position.y = -size.y / 2;
      scene.add(grid);
      gridRef.current = grid;
      disposables.push(grid.geometry, grid.material as THREE.Material);

      const box = new THREE.Box3Helper(new THREE.Box3().setFromObject(content), 0x10b981);
      scene.add(box);
      boxRef.current = box;
      disposables.push(box.geometry, box.material as THREE.Material);
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

          const material = new THREE.PointsMaterial({
            size: maxDimensionRef.current * 0.004 || 0.05,
            vertexColors: true,
            transparent: true,
            opacity: 0.95,
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
        }
      }

      if (cancelled) return;

      stageScene();

      if (pointsRef.current) {
        const material = pointsRef.current.material as THREE.PointsMaterial;
        material.size = Math.max(maxDimensionRef.current * 0.002, 0.005);
      }

      setStats({
        pointCount,
        hasVertexColors,
        units: "reconstruction units (unscaled)",
      });
      setColorMode("elevation");
      setStatus("ready");
    };

    load().catch((error: unknown) => {
      if (cancelled) return;
      setErrorMessage(error instanceof Error ? error.message : String(error));
      setStatus("error");
    });

    const raycaster = new THREE.Raycaster();
    raycaster.params.Points.threshold = maxDimensionRef.current * 0.01;
    const pointer = new THREE.Vector2();

    const handleCanvasClick = (event: MouseEvent) => {
      if (!measureMode || !pointsRef.current) return;
      const rect = renderer.domElement.getBoundingClientRect();
      pointer.x = ((event.clientX - rect.left) / rect.width) * 2 - 1;
      pointer.y = -((event.clientY - rect.top) / rect.height) * 2 + 1;
      raycaster.params.Points.threshold = Math.max(maxDimensionRef.current * 0.01, 0.001);
      raycaster.setFromCamera(pointer, camera);
      const intersects = raycaster.intersectObject(pointsRef.current);
      if (intersects.length > 0) {
        const hit = intersects[0].point.clone();
        setMeasurePoints((previous) => (previous.length >= 2 ? [hit] : [...previous, hit]));
>>>>>>> 0400f2f (p5-udpated)
      }
    };

    renderer.domElement.addEventListener("click", handleCanvasClick);

<<<<<<< HEAD
    // Resize handler
    const handleResize = () => {
      if (!host) return;
      camera.aspect = host.clientWidth / host.clientHeight;
      camera.updateProjectionMatrix();
      renderer.setSize(host.clientWidth, host.clientHeight);
    };
    window.addEventListener("resize", handleResize);

    // --- 10. Memory Leak Prevention & Disposal ---
    return () => {
      window.removeEventListener("resize", handleResize);
      renderer.domElement.removeEventListener("click", handleCanvasClick);
      cancelAnimationFrame(animId);

      controls.dispose();
      pGeo.dispose();
      pMat.dispose();
      tGeo.dispose();
      tMat.dispose();
      flightLineGeo.dispose();
      mLineGeo.dispose();
      mLineMat.dispose();
      renderer.dispose();

      if (host.contains(renderer.domElement)) {
        host.removeChild(renderer.domElement);
      }
    };
  }, [pointBudget]);

  // Update Measurement Visuals when points change
=======
    const handleResize = () => {
      if (!host) return;
      const width = host.clientWidth || 1;
      const height = host.clientHeight || 1;
      camera.aspect = width / height;
      camera.updateProjectionMatrix();
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
      pointsRef.current = null;
      meshRef.current = null;
      sceneRef.current = null;
      cameraRef.current = null;
      controlsRef.current = null;
      gridRef.current = null;
      boxRef.current = null;
      measureMarkersRef.current = null;
      measureLineRef.current = null;
      elevationColorsRef.current = null;
      sourceColorsRef.current = null;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [plyUrl, modelUrl, reloadKey]);

  // Measurement overlay
>>>>>>> 0400f2f (p5-udpated)
  useEffect(() => {
    const markers = measureMarkersRef.current;
    const line = measureLineRef.current;
    if (!markers || !line) return;

<<<<<<< HEAD
    // Clear old markers
=======
>>>>>>> 0400f2f (p5-udpated)
    while (markers.children.length > 0) {
      markers.remove(markers.children[0]);
    }

<<<<<<< HEAD
    measurePoints.forEach((pt, i) => {
      const sphere = new THREE.Mesh(
        new THREE.SphereGeometry(0.35, 16, 16),
        new THREE.MeshBasicMaterial({ color: i === 0 ? 0x10b981 : 0x00f5a0 })
      );
      sphere.position.copy(pt);
=======
    const markerRadius = maxDimensionRef.current * 0.006;
    measurePoints.forEach((point, index) => {
      const sphere = new THREE.Mesh(
        new THREE.SphereGeometry(Math.max(markerRadius, 0.001), 16, 16),
        new THREE.MeshBasicMaterial({ color: index === 0 ? 0x10b981 : 0x00f5a0 })
      );
      sphere.position.copy(point);
>>>>>>> 0400f2f (p5-udpated)
      markers.add(sphere);
    });

    if (measurePoints.length === 2) {
<<<<<<< HEAD
      const p1 = measurePoints[0];
      const p2 = measurePoints[1];

      line.geometry.dispose();
      line.geometry = new THREE.BufferGeometry().setFromPoints([p1, p2]);
      line.visible = true;

      const d3D = p1.distanceTo(p2);
      const dH = Math.sqrt(Math.pow(p2.x - p1.x, 2) + Math.pow(p2.z - p1.z, 2));
      const dElev = Math.abs(p2.y - p1.y);
      const slope = Math.atan2(dElev, dH) * (180 / Math.PI);

      setMeasurementResult({
        distance3D: +d3D.toFixed(2),
        distanceHoriz: +dH.toFixed(2),
        elevationDelta: +dElev.toFixed(2),
=======
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
>>>>>>> 0400f2f (p5-udpated)
        slopeDeg: +slope.toFixed(1),
      });
    } else {
      line.visible = false;
<<<<<<< HEAD
      if (measurePoints.length === 0) {
        setMeasurementResult(null);
      }
    }
  }, [measurePoints]);

  // Update Color Modes
  const applyColorMode = (mode: "elevation" | "rgb" | "damage" | "intensity") => {
    setColorMode(mode);
    const points = pointsRef.current;
    if (!points) return;

    const geo = points.geometry;
    const pos = geo.attributes.position;
    const colAttr = geo.attributes.color;
    const colors = colAttr.array as Float32Array;

    for (let i = 0; i < pos.count; i++) {
      const y = pos.getY(i);
      const x = pos.getX(i);
      const z = pos.getZ(i);

      if (mode === "elevation") {
        const normY = THREE.MathUtils.clamp((y + 3) / 10, 0, 1);
        const c = new THREE.Color().setHSL(0.55 - normY * 0.55, 0.9, 0.5);
        colors[i * 3] = c.r;
        colors[i * 3 + 1] = c.g;
        colors[i * 3 + 2] = c.b;
      } else if (mode === "rgb") {
        // Photorealistic aerial tone
        const c = new THREE.Color(0x3d5a45);
        if (y > 3) c.setHex(0x9a8370); // rooftops / structures
        colors[i * 3] = c.r;
        colors[i * 3 + 1] = c.g;
        colors[i * 3 + 2] = c.b;
      } else if (mode === "damage") {
        // xBD 4-tier damage classification color scheme
        const c = new THREE.Color();
        if (y > 5) c.setHex(0xef4444); // Destroyed
        else if (y > 3.5) c.setHex(0xf97316); // Major
        else if (y > 2) c.setHex(0xeab308); // Minor
        else c.setHex(0x10b981); // Intact
        colors[i * 3] = c.r;
        colors[i * 3 + 1] = c.g;
        colors[i * 3 + 2] = c.b;
      } else if (mode === "intensity") {
        const val = 0.3 + (Math.sin(x * 0.5) * 0.2 + 0.3);
        colors[i * 3] = val;
        colors[i * 3 + 1] = val;
        colors[i * 3 + 2] = val;
      }
    }
    colAttr.needsUpdate = true;
  };

  // Toggle Layer Visibility
  const toggleLayer = (layerKey: keyof typeof layers) => {
    const updated = !layers[layerKey];
    setLayers((prev) => ({ ...prev, [layerKey]: updated }));

    if (layerKey === "pointCloud" && pointsRef.current) {
      pointsRef.current.visible = updated;
    } else if (layerKey === "terrainMesh" && terrainMeshRef.current) {
      terrainMeshRef.current.visible = updated;
    } else if (layerKey === "flightPath" && flightPathGroupRef.current) {
      flightPathGroupRef.current.visible = updated;
    } else if (layerKey === "gridHelper" && gridHelperRef.current) {
      gridHelperRef.current.visible = updated;
    } else if (layerKey === "boundingBox" && boxHelperRef.current) {
      boxHelperRef.current.visible = updated;
    }
  };

  // Camera presets
  const setCameraView = (view: "ortho" | "perspective" | "oblique" | "reset") => {
    const camera = cameraRef.current;
    const controls = controlsRef.current;
    if (!camera || !controls) return;

    if (view === "ortho") {
      camera.position.set(0, 45, 0.1);
      controls.target.set(0, 0, 0);
    } else if (view === "perspective" || view === "reset") {
      camera.position.set(24, 18, 28);
      controls.target.set(0, 2, 0);
    } else if (view === "oblique") {
      camera.position.set(30, 12, 30);
      controls.target.set(0, 0, 0);
    }
  };

  // Export Screenshot with Watermark
  const exportScreenshot = () => {
    const renderer = rendererRef.current;
    if (!renderer) return;

    const dataUrl = renderer.domElement.toDataURL("image/png");
    const a = document.createElement("a");
    a.href = dataUrl;
    a.download = `JATAYUV_3D_SURVEY_${Date.now()}.png`;
    a.click();
  };

  // Toggle Fullscreen Mode
  const toggleFullscreen = () => {
    const container = containerRef.current;
    if (!container) return;

    if (!document.fullscreenElement) {
      container.requestFullscreen().then(() => setIsFullscreen(true)).catch(console.error);
    } else {
      document.exitFullscreen().then(() => setIsFullscreen(false)).catch(console.error);
    }
  };

=======
      if (measurePoints.length === 0) setMeasurementResult(null);
    }
  }, [measurePoints]);

  const applyColorMode = useCallback((mode: ColorMode) => {
    const points = pointsRef.current;
    if (!points) return;
    const geometry = points.geometry;
    const position = geometry.getAttribute("position");
    const target = mode === "rgb" ? sourceColorsRef.current : elevationColorsRef.current;
    if (!target) return;
    const colors = new Float32Array(position.count * 3);
    colors.set(target.subarray(0, colors.length));
    geometry.setAttribute("color", new THREE.BufferAttribute(colors, 3));
    const colorAttr = geometry.getAttribute("color");
    if (colorAttr) colorAttr.needsUpdate = true;
    setColorMode(mode);
  }, []);

  const toggleLayer = (key: keyof typeof layers) => {
    const next = !layers[key];
    setLayers((previous) => ({ ...previous, [key]: next }));
    if (key === "pointCloud" && pointsRef.current) pointsRef.current.visible = next;
    if (key === "mesh" && meshRef.current) meshRef.current.visible = next;
    if (key === "gridHelper" && gridRef.current) gridRef.current.visible = next;
    if (key === "boundingBox" && boxRef.current) boxRef.current.visible = next;
  };

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

  const exportScreenshot = () => {
    const renderer = canvasHostRef.current?.querySelector("canvas");
    if (!renderer) return;
    const link = document.createElement("a");
    link.href = (renderer as HTMLCanvasElement).toDataURL("image/png");
    link.download = `JATAYUV_3D_VIEW_${Date.now()}.png`;
    link.click();
  };

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

  const hasArtifact = Boolean(plyUrl || modelUrl);

>>>>>>> 0400f2f (p5-udpated)
  return (
    <div
      ref={containerRef}
      className={`relative w-full rounded-xl overflow-hidden border border-emerald-500/25 bg-forest-950 select-none ${
        isFullscreen ? "h-screen w-screen" : "h-[620px]"
      }`}
    >
<<<<<<< HEAD
      {/* WebGL Canvas Host */}
      <div ref={canvasHostRef} className="w-full h-full cursor-grab active:cursor-grabbing" />

      {/* Tactical HUD Corners */}
      <div className="hud-corner-tl m-3 pointer-events-none" />
      <div className="hud-corner-tr m-3 pointer-events-none" />
      <div className="hud-corner-bl m-3 pointer-events-none" />
      <div className="hud-corner-br m-3 pointer-events-none" />

      {/* Top Telemetry & Controls Ribbon */}
      <div className="absolute top-4 left-4 right-4 flex flex-wrap items-center justify-between gap-3 pointer-events-none">
        <div className="glass-panel px-3.5 py-1.5 rounded flex items-center gap-3 font-mono text-xs">
          <div className="flex items-center gap-2">
            <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
            <span className="text-white font-bold">{projectName}</span>
          </div>
          <span className="text-muted-foreground">|</span>
          <span className="text-emerald-300">{locationName}</span>
          <span className="text-muted-foreground">|</span>
          <span className="text-muted-foreground">{pointBudget.toLocaleString()} PTS (SfM Dense)</span>
        </div>

        {/* Action Controls Toolbar (Interactive) */}
        <div className="flex items-center gap-1.5 glass-panel p-1 rounded pointer-events-auto font-mono text-xs">
          <button
            onClick={() => setCameraView("reset")}
            title="Reset Camera Orientation"
            className="p-1.5 rounded hover:bg-forest-800 text-muted-foreground hover:text-white transition-colors"
          >
            <RotateCcw className="w-4 h-4" />
          </button>

          <button
            onClick={() => setCameraView("ortho")}
            title="Nadir Top-Down View"
            className="px-2 py-1 rounded hover:bg-forest-800 text-muted-foreground hover:text-white transition-colors"
          >
            NADIR
          </button>

          <button
            onClick={() => setCameraView("oblique")}
            title="45° Oblique Survey Angle"
            className="px-2 py-1 rounded hover:bg-forest-800 text-muted-foreground hover:text-white transition-colors"
          >
            OBLIQUE
          </button>

          <div className="h-4 w-[1px] bg-emerald-500/20 my-auto" />

          {/* 3D Measurement Mode Toggle */}
          <button
            onClick={() => {
              setMeasureMode(!measureMode);
              setMeasurePoints([]);
            }}
            className={`px-2.5 py-1 rounded flex items-center gap-1.5 transition-all ${
              measureMode
                ? "bg-emerald-600 text-white font-bold"
                : "text-muted-foreground hover:bg-forest-800 hover:text-white"
            }`}
          >
            <Ruler className="w-3.5 h-3.5" />
            <span>MEASURE 3D</span>
          </button>

          <div className="h-4 w-[1px] bg-emerald-500/20 my-auto" />

          {/* Screenshot Export */}
          <button
            onClick={exportScreenshot}
            title="Export High-Res Screenshot"
            className="p-1.5 rounded hover:bg-forest-800 text-muted-foreground hover:text-white transition-colors"
          >
            <Download className="w-4 h-4 text-emerald-400" />
          </button>

          {/* Fullscreen Toggle */}
          <button
            onClick={toggleFullscreen}
            title={isFullscreen ? "Exit Fullscreen" : "Fullscreen View"}
            className="p-1.5 rounded hover:bg-forest-800 text-muted-foreground hover:text-white transition-colors"
          >
            {isFullscreen ? <Minimize2 className="w-4 h-4" /> : <Maximize2 className="w-4 h-4" />}
          </button>
        </div>
      </div>

      {/* Floating Measurement HUD (Active when measureMode is ON) */}
      {measureMode && (
        <div className="absolute top-16 left-4 glass-panel p-3.5 rounded max-w-xs font-mono text-xs border-l-2 border-l-emerald-400 z-10 pointer-events-auto space-y-2">
          <div className="flex items-center justify-between text-emerald-400 font-bold border-b border-emerald-500/20 pb-1">
            <span className="flex items-center gap-1.5">
              <Crosshair className="w-3.5 h-3.5" /> 3D SPATIAL MEASUREMENT
=======
      <div ref={canvasHostRef} className="w-full h-full" />

      {/* Empty state: no verified reconstruction is available. */}
      {status === "empty" && (
        <div className="absolute inset-0 flex flex-col items-center justify-center gap-3 p-6 text-center font-mono">
          <Box className="w-10 h-10 text-emerald-500/60" />
          <p className="text-sm text-muted-foreground max-w-md">{EMPTY_RECONSTRUCTION_MESSAGE}</p>
          <p className="text-[11px] text-muted-foreground/70">
            Procedural or placeholder geometry is never shown as a reconstruction.
          </p>
        </div>
      )}

      {/* Loading state */}
      {status === "loading" && (
        <div className="absolute inset-0 flex flex-col items-center justify-center gap-2 bg-forest-950/80 font-mono text-xs text-emerald-300">
          <Loader2 className="w-5 h-5 animate-spin" />
          <span>LOADING VERIFIED RECONSTRUCTION ARTIFACT…</span>
        </div>
      )}

      {/* Error state */}
      {status === "error" && (
        <div className="absolute inset-0 flex flex-col items-center justify-center gap-3 p-6 text-center font-mono">
          <AlertTriangle className="w-9 h-9 text-rose-400" />
          <div className="text-sm text-rose-300 font-bold">3D RECONSTRUCTION UNAVAILABLE</div>
          <p className="text-[11px] text-muted-foreground max-w-lg break-words">
            {errorMessage ?? "The reconstruction artifact could not be loaded."}
          </p>
          {hasArtifact && (
            <button
              onClick={() => setReloadKey((key) => key + 1)}
              className="mt-1 flex items-center gap-1.5 px-3 py-1.5 rounded border border-emerald-500/30 text-emerald-300 hover:bg-forest-800 text-[11px]"
            >
              <RefreshCw className="w-3.5 h-3.5" /> RETRY LOAD
            </button>
          )}
        </div>
      )}

      {/* Top telemetry ribbon (only for a verified artifact) */}
      {status === "ready" && (
        <div className="absolute top-4 left-4 right-4 flex flex-wrap items-center justify-between gap-3 pointer-events-none">
          <div className="glass-panel px-3.5 py-1.5 rounded flex items-center gap-3 font-mono text-xs">
            <div className="flex items-center gap-2">
              <span className="w-2 h-2 rounded-full bg-emerald-400" />
              <span className="text-white font-bold">{projectName}</span>
            </div>
            {locationName && (
              <>
                <span className="text-muted-foreground">|</span>
                <span className="text-emerald-300">{locationName}</span>
              </>
            )}
            <span className="text-muted-foreground">|</span>
            <span className="text-muted-foreground">
              {stats && stats.pointCount > 0
                ? `${stats.pointCount.toLocaleString()} PTS`
                : "MESH MODEL"}{" "}
              · COLMAP
            </span>
            <span className="text-muted-foreground">|</span>
            <span className="text-muted-foreground">{stats?.units}</span>
          </div>

          <div className="flex items-center gap-1.5 glass-panel p-1 rounded pointer-events-auto font-mono text-xs">
            <button
              onClick={() => setCameraView("reset")}
              title="Reset camera"
              className="p-1.5 rounded hover:bg-forest-800 text-muted-foreground hover:text-white"
            >
              <RotateCcw className="w-4 h-4" />
            </button>
            <button
              onClick={() => setCameraView("nadir")}
              title="Top-down view"
              className="px-2 py-1 rounded hover:bg-forest-800 text-muted-foreground hover:text-white"
            >
              NADIR
            </button>
            <button
              onClick={() => setCameraView("oblique")}
              title="Oblique view"
              className="px-2 py-1 rounded hover:bg-forest-800 text-muted-foreground hover:text-white"
            >
              OBLIQUE
            </button>
            <div className="h-4 w-[1px] bg-emerald-500/20 my-auto" />
            <button
              onClick={() => {
                setMeasureMode(!measureMode);
                setMeasurePoints([]);
              }}
              disabled={!pointsRef.current}
              className={`px-2.5 py-1 rounded flex items-center gap-1.5 transition-all disabled:opacity-40 ${
                measureMode
                  ? "bg-emerald-600 text-white font-bold"
                  : "text-muted-foreground hover:bg-forest-800 hover:text-white"
              }`}
            >
              <Ruler className="w-3.5 h-3.5" />
              <span>MEASURE</span>
            </button>
            <div className="h-4 w-[1px] bg-emerald-500/20 my-auto" />
            <button
              onClick={exportScreenshot}
              title="Export screenshot"
              className="p-1.5 rounded hover:bg-forest-800 text-muted-foreground hover:text-white"
            >
              <Download className="w-4 h-4 text-emerald-400" />
            </button>
            <button
              onClick={toggleFullscreen}
              title={isFullscreen ? "Exit fullscreen" : "Fullscreen"}
              className="p-1.5 rounded hover:bg-forest-800 text-muted-foreground hover:text-white"
            >
              {isFullscreen ? <Minimize2 className="w-4 h-4" /> : <Maximize2 className="w-4 h-4" />}
            </button>
          </div>
        </div>
      )}

      {/* Measurement HUD */}
      {status === "ready" && measureMode && (
        <div className="absolute top-16 left-4 glass-panel p-3.5 rounded max-w-xs font-mono text-xs border-l-2 border-l-emerald-400 z-10 space-y-2">
          <div className="flex items-center justify-between text-emerald-400 font-bold border-b border-emerald-500/20 pb-1">
            <span className="flex items-center gap-1.5">
              <Crosshair className="w-3.5 h-3.5" /> 3D MEASUREMENT
>>>>>>> 0400f2f (p5-udpated)
            </span>
            <button
              onClick={() => setMeasurePoints([])}
              className="text-[10px] text-muted-foreground hover:text-white"
            >
              CLEAR
            </button>
          </div>

          {measurePoints.length === 0 && (
<<<<<<< HEAD
            <p className="text-muted-foreground text-[11px]">
              Click on the point cloud to place Point A.
            </p>
          )}

          {measurePoints.length === 1 && (
            <p className="text-emerald-300 text-[11px] animate-pulse">
              Point A set! Click a second point for 3D distance.
            </p>
          )}

          {measurementResult && (
            <div className="space-y-1.5 pt-1">
              <div className="flex justify-between">
                <span className="text-muted-foreground">EUCLIDEAN (3D):</span>
                <span className="text-emerald-300 font-bold text-sm">
                  {measurementResult.distance3D} m
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-muted-foreground">HORIZONTAL (dX, dZ):</span>
                <span className="text-white font-semibold">
                  {measurementResult.distanceHoriz} m
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-muted-foreground">ELEVATION DELTA (dY):</span>
                <span className="text-sky-300 font-semibold">
                  {measurementResult.elevationDelta} m
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-muted-foreground">SLOPE ANGLE:</span>
                <span className="text-amber-300 font-semibold">
                  {measurementResult.slopeDeg}°
                </span>
              </div>
=======
            <p className="text-muted-foreground text-[11px]">Click the cloud to place point A.</p>
          )}
          {measurePoints.length === 1 && (
            <p className="text-emerald-300 text-[11px]">Point A set. Click point B.</p>
          )}
          {measurementResult && (
            <div className="space-y-1.5 pt-1">
              <div className="flex justify-between">
                <span className="text-muted-foreground">EUCLIDEAN:</span>
                <span className="text-emerald-300 font-bold text-sm">
                  {measurementResult.distance} u
                </span>
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
                <span className="text-muted-foreground">SLOPE:</span>
                <span className="text-amber-300 font-semibold">{measurementResult.slopeDeg}°</span>
              </div>
              <p className="text-[9px] text-muted-foreground pt-1">
                Units are unscaled reconstruction units, not metres.
              </p>
>>>>>>> 0400f2f (p5-udpated)
            </div>
          )}
        </div>
      )}

<<<<<<< HEAD
      {/* Bottom Floating Control Bar */}
      <div className="absolute bottom-4 left-4 right-4 flex flex-wrap items-center justify-between gap-3 pointer-events-none">
        {/* Colormap Selector */}
        <div className="glass-panel p-1.5 rounded flex items-center gap-2 pointer-events-auto font-mono text-xs">
          <span className="text-[10px] text-muted-foreground px-1 uppercase tracking-wider">
            COLORMAP:
          </span>
          {(["elevation", "rgb", "damage", "intensity"] as const).map((m) => (
            <button
              key={m}
              onClick={() => applyColorMode(m)}
              className={`px-2.5 py-1 rounded uppercase text-[11px] transition-all ${
                colorMode === m
                  ? "bg-emerald-600 text-white font-bold shadow-sm"
                  : "text-muted-foreground hover:bg-forest-800 hover:text-white"
              }`}
            >
              {m}
            </button>
          ))}
        </div>

        {/* Layer Visibility Toggles */}
        <div className="glass-panel p-1.5 rounded flex items-center gap-2 pointer-events-auto font-mono text-xs">
          <span className="text-[10px] text-muted-foreground px-1 uppercase tracking-wider">
            LAYERS:
          </span>
          <button
            onClick={() => toggleLayer("pointCloud")}
            className={`px-2 py-1 rounded text-[11px] ${
              layers.pointCloud ? "text-emerald-400 font-bold" : "text-muted-foreground line-through opacity-50"
            }`}
          >
            POINTS
          </button>

          <button
            onClick={() => toggleLayer("terrainMesh")}
            className={`px-2 py-1 rounded text-[11px] ${
              layers.terrainMesh ? "text-emerald-400 font-bold" : "text-muted-foreground line-through opacity-50"
            }`}
          >
            TERRAIN
          </button>

          <button
            onClick={() => toggleLayer("flightPath")}
            className={`px-2 py-1 rounded text-[11px] ${
              layers.flightPath ? "text-emerald-400 font-bold" : "text-muted-foreground line-through opacity-50"
            }`}
          >
            FLIGHT PATH
          </button>

          <button
            onClick={() => toggleLayer("gridHelper")}
            className={`px-2 py-1 rounded text-[11px] ${
              layers.gridHelper ? "text-emerald-400 font-bold" : "text-muted-foreground line-through opacity-50"
            }`}
          >
            GRID
          </button>
        </div>
      </div>
=======
      {/* Bottom control bar */}
      {status === "ready" && (
        <div className="absolute bottom-4 left-4 right-4 flex flex-wrap items-center justify-between gap-3 pointer-events-none">
          <div className="glass-panel p-1.5 rounded flex items-center gap-2 pointer-events-auto font-mono text-xs">
            <span className="text-[10px] text-muted-foreground px-1 uppercase tracking-wider">
              COLORMAP:
            </span>
            <button
              onClick={() => applyColorMode("elevation")}
              className={`px-2.5 py-1 rounded uppercase text-[11px] ${
                colorMode === "elevation"
                  ? "bg-emerald-600 text-white font-bold"
                  : "text-muted-foreground hover:bg-forest-800 hover:text-white"
              }`}
            >
              elevation
            </button>
            <button
              onClick={() => applyColorMode("rgb")}
              disabled={!stats?.hasVertexColors}
              title={
                stats?.hasVertexColors
                  ? "Use the colours stored in the PLY"
                  : "This PLY carries no vertex colours"
              }
              className={`px-2.5 py-1 rounded uppercase text-[11px] disabled:opacity-30 ${
                colorMode === "rgb"
                  ? "bg-emerald-600 text-white font-bold"
                  : "text-muted-foreground hover:bg-forest-800 hover:text-white"
              }`}
            >
              rgb
            </button>
          </div>

          <div className="glass-panel p-1.5 rounded flex items-center gap-2 pointer-events-auto font-mono text-xs">
            <span className="text-[10px] text-muted-foreground px-1 uppercase tracking-wider">
              LAYERS:
            </span>
            <button
              onClick={() => toggleLayer("pointCloud")}
              disabled={!pointsRef.current}
              className={`px-2 py-1 rounded text-[11px] disabled:opacity-40 ${
                layers.pointCloud ? "text-emerald-400 font-bold" : "text-muted-foreground line-through opacity-50"
              }`}
            >
              POINTS
            </button>
            <button
              onClick={() => toggleLayer("mesh")}
              disabled={!meshRef.current}
              className={`px-2 py-1 rounded text-[11px] disabled:opacity-40 ${
                layers.mesh ? "text-emerald-400 font-bold" : "text-muted-foreground line-through opacity-50"
              }`}
            >
              MESH
            </button>
            <button
              onClick={() => toggleLayer("gridHelper")}
              className={`px-2 py-1 rounded text-[11px] ${
                layers.gridHelper ? "text-emerald-400 font-bold" : "text-muted-foreground line-through opacity-50"
              }`}
            >
              GRID
            </button>
            <button
              onClick={() => toggleLayer("boundingBox")}
              className={`px-2 py-1 rounded text-[11px] ${
                layers.boundingBox ? "text-emerald-400 font-bold" : "text-muted-foreground line-through opacity-50"
              }`}
            >
              BBOX
            </button>
          </div>
        </div>
      )}
>>>>>>> 0400f2f (p5-udpated)
    </div>
  );
}

<<<<<<< HEAD
=======
export { validateArtifactUrl };
>>>>>>> 0400f2f (p5-udpated)

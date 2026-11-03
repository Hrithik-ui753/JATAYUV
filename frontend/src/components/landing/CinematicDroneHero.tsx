"use client";

import React, { useEffect, useRef, useState } from "react";
import * as THREE from "three";
import { OrbitControls } from "three/examples/jsm/controls/OrbitControls.js";
import { 
  Compass, 
  Activity, 
  Layers, 
  Maximize2, 
  RotateCcw, 
  Eye, 
  Radio, 
  Navigation, 
  Crosshair,
  ShieldCheck,
  Zap
} from "lucide-react";

export function CinematicDroneHero() {
  const containerRef = useRef<HTMLDivElement>(null);
  const [cameraMode, setCameraMode] = useState<"tactical" | "chase" | "sensor" | "wide">("tactical");
  const [isScanning, setIsScanning] = useState(true);
  const [showFlightPath, setShowFlightPath] = useState(true);
  const [telemetry, setTelemetry] = useState({
    altitude: 124.8,
    groundSpeed: 14.2,
    heading: 42,
    batteryPct: 88,
    lat: "20°18'57.6\"N",
    lon: "86°36'41.0\"E",
    pulseRate: "300 kHz",
    gsd: "1.8 cm/px",
    pointsCollected: 148290,
  });

  // Keep ref to control camera transitions
  const controlsRef = useRef<OrbitControls | null>(null);
  const cameraRef = useRef<THREE.PerspectiveCamera | null>(null);

  useEffect(() => {
    const container = containerRef.current;
    if (!container) return;

    // Check prefers-reduced-motion
    const prefersReducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

    // --- 1. Scene, Camera, Renderer ---
    const scene = new THREE.Scene();
    scene.background = new THREE.Color(0x060908);
    scene.fog = new THREE.FogExp2(0x060908, 0.018);

    const camera = new THREE.PerspectiveCamera(
      45,
      container.clientWidth / container.clientHeight,
      0.1,
      1000
    );
    camera.position.set(18, 14, 22);
    cameraRef.current = camera;

    const renderer = new THREE.WebGLRenderer({
      antialias: true,
      powerPreference: "high-performance",
      alpha: false,
    });
    renderer.setSize(container.clientWidth, container.clientHeight);
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    renderer.shadowMap.enabled = true;
    renderer.shadowMap.type = THREE.PCFSoftShadowMap;
    renderer.toneMapping = THREE.ACESFilmicToneMapping;
    renderer.toneMappingExposure = 1.15;
    container.appendChild(renderer.domElement);

    const controls = new OrbitControls(camera, renderer.domElement);
    controls.enableDamping = true;
    controls.dampingFactor = 0.05;
    controls.maxPolarAngle = Math.PI / 2 - 0.05; // Prevent camera sinking under terrain
    controls.minDistance = 6;
    controls.maxDistance = 65;
    controls.target.set(0, 3, 0);
    controlsRef.current = controls;

    // --- 2. Lighting ---
    const ambientLight = new THREE.AmbientLight(0x0d281e, 1.8);
    scene.add(ambientLight);

    const sunLight = new THREE.DirectionalLight(0xa7f3d0, 2.8);
    sunLight.position.set(30, 45, 20);
    sunLight.castShadow = true;
    sunLight.shadow.mapSize.width = 2048;
    sunLight.shadow.mapSize.height = 2048;
    sunLight.shadow.camera.near = 10;
    sunLight.shadow.camera.far = 100;
    sunLight.shadow.camera.left = -25;
    sunLight.shadow.camera.right = 25;
    sunLight.shadow.camera.top = 25;
    sunLight.shadow.camera.bottom = -25;
    scene.add(sunLight);

    const rimLight = new THREE.DirectionalLight(0x10b981, 1.4);
    rimLight.position.set(-25, 20, -25);
    scene.add(rimLight);

    // --- 3. Procedural 3D Terrain Environment ---
    const terrainSize = 70;
    const terrainSegments = 70;
    const terrainGeo = new THREE.PlaneGeometry(terrainSize, terrainSize, terrainSegments, terrainSegments);
    terrainGeo.rotateX(-Math.PI / 2);

    const pos = terrainGeo.attributes.position;
    const colors = new Float32Array(pos.count * 3);

    // Generate procedural hills and valleys using sinusoidal multi-frequencies
    for (let i = 0; i < pos.count; i++) {
      const x = pos.getX(i);
      const z = pos.getZ(i);

      // Procedural height formula
      const elevation =
        Math.sin(x * 0.12) * Math.cos(z * 0.12) * 2.8 +
        Math.sin(x * 0.25 + 1.2) * Math.cos(z * 0.2) * 1.5 +
        Math.sin((x + z) * 0.08) * 2.2 -
        Math.exp(-((x * x + z * z) / 220)) * 2.0; // Central depression / river basin

      pos.setY(i, elevation);

      // Color mapping based on elevation (Deep forest dark to emerald peaks)
      const normY = THREE.MathUtils.clamp((elevation + 4) / 9, 0, 1);
      const c1 = new THREE.Color(0x07120d); // deep valley
      const c2 = new THREE.Color(0x0e2e21); // mid slope
      const c3 = new THREE.Color(0x10b981); // ridge peak
      const cFinal = new THREE.Color();

      if (normY < 0.5) {
        cFinal.lerpColors(c1, c2, normY * 2);
      } else {
        cFinal.lerpColors(c2, c3, (normY - 0.5) * 2);
      }

      colors[i * 3] = cFinal.r;
      colors[i * 3 + 1] = cFinal.g;
      colors[i * 3 + 2] = cFinal.b;
    }

    terrainGeo.setAttribute("color", new THREE.BufferAttribute(colors, 3));
    terrainGeo.computeVertexNormals();

    const terrainMat = new THREE.MeshStandardMaterial({
      vertexColors: true,
      roughness: 0.85,
      metalness: 0.15,
      flatShading: true,
    });
    const terrainMesh = new THREE.Mesh(terrainGeo, terrainMat);
    terrainMesh.receiveShadow = true;
    scene.add(terrainMesh);

    // Topographic Wireframe Overlay
    const wireMat = new THREE.MeshBasicMaterial({
      color: 0x10b981,
      wireframe: true,
      transparent: true,
      opacity: 0.12,
    });
    const terrainWire = new THREE.Mesh(terrainGeo, wireMat);
    terrainWire.position.y += 0.02;
    scene.add(terrainWire);

    // Coordinate Grid Base
    const gridHelper = new THREE.GridHelper(70, 35, 0x10b981, 0x0c251b);
    gridHelper.position.y = -4.2;
    scene.add(gridHelper);

    // --- 4. Detailed Stylized UAV / Drone ---
    const droneGroup = new THREE.Group();
    droneGroup.position.set(0, 6.5, 0);
    scene.add(droneGroup);

    // Drone Materials
    const chassisMat = new THREE.MeshStandardMaterial({
      color: 0x111614,
      metalness: 0.85,
      roughness: 0.25,
    });
    const carbonMat = new THREE.MeshStandardMaterial({
      color: 0x090c0b,
      metalness: 0.5,
      roughness: 0.5,
    });
    const emeraldAccentMat = new THREE.MeshBasicMaterial({
      color: 0x00f5a0,
    });
    const rotorBladeMat = new THREE.MeshStandardMaterial({
      color: 0x22362c,
      transparent: true,
      opacity: 0.8,
    });

    // Central Fuselage
    const bodyGeo = new THREE.BoxGeometry(1.6, 0.45, 1.4);
    const bodyMesh = new THREE.Mesh(bodyGeo, chassisMat);
    bodyMesh.castShadow = true;
    droneGroup.add(bodyMesh);

    // Aerodynamic top canopy
    const canopyGeo = new THREE.ConeGeometry(0.7, 0.45, 4);
    canopyGeo.rotateY(Math.PI / 4);
    const canopyMesh = new THREE.Mesh(canopyGeo, chassisMat);
    canopyMesh.position.set(0, 0.35, 0);
    droneGroup.add(canopyMesh);

    // GPS / Satellite Antenna Dome
    const gpsDomeGeo = new THREE.CylinderGeometry(0.2, 0.25, 0.15, 16);
    const gpsDome = new THREE.Mesh(gpsDomeGeo, carbonMat);
    gpsDome.position.set(0, 0.55, -0.2);
    droneGroup.add(gpsDome);

    // 4 Quadcopter Arms & Rotors
    const rotorGroups: THREE.Group[] = [];
    const armAngles = [
      Math.PI / 4,
      (3 * Math.PI) / 4,
      (5 * Math.PI) / 4,
      (7 * Math.PI) / 4,
    ];
    const armDistance = 2.0;

    armAngles.forEach((angle, idx) => {
      const armGroup = new THREE.Group();
      armGroup.rotation.y = angle;

      // Arm spar
      const sparGeo = new THREE.CylinderGeometry(0.07, 0.07, armDistance, 8);
      sparGeo.rotateZ(Math.PI / 2);
      const sparMesh = new THREE.Mesh(sparGeo, carbonMat);
      sparMesh.position.set(armDistance / 2, 0, 0);
      armGroup.add(sparMesh);

      // Motor mount pod
      const podGeo = new THREE.CylinderGeometry(0.22, 0.2, 0.35, 16);
      const podMesh = new THREE.Mesh(podGeo, chassisMat);
      podMesh.position.set(armDistance, 0.1, 0);
      armGroup.add(podMesh);

      // Motor top cap
      const capGeo = new THREE.CylinderGeometry(0.08, 0.08, 0.15, 8);
      const capMesh = new THREE.Mesh(capGeo, emeraldAccentMat);
      capMesh.position.set(armDistance, 0.3, 0);
      armGroup.add(capMesh);

      // Rotor Blades Assembly
      const rotorAssembly = new THREE.Group();
      rotorAssembly.position.set(armDistance, 0.32, 0);

      const bladeGeo = new THREE.BoxGeometry(1.6, 0.02, 0.14);
      const bladeMesh = new THREE.Mesh(bladeGeo, rotorBladeMat);
      rotorAssembly.add(bladeMesh);

      // Rotor disc blur visual
      const blurGeo = new THREE.CylinderGeometry(0.85, 0.85, 0.01, 24);
      const blurMat = new THREE.MeshBasicMaterial({
        color: 0x10b981,
        transparent: true,
        opacity: 0.15,
        side: THREE.DoubleSide,
      });
      const blurMesh = new THREE.Mesh(blurGeo, blurMat);
      rotorAssembly.add(blurMesh);

      armGroup.add(rotorAssembly);
      rotorGroups.push(rotorAssembly);

      // Navigation LEDs on arm tips
      const ledGeo = new THREE.SphereGeometry(0.06, 8, 8);
      const ledColor = idx === 0 ? 0xef4444 : idx === 1 ? 0x10b981 : 0x00f5a0;
      const ledMat = new THREE.MeshBasicMaterial({ color: ledColor });
      const ledMesh = new THREE.Mesh(ledGeo, ledMat);
      ledMesh.position.set(armDistance + 0.1, 0, 0);
      armGroup.add(ledMesh);

      droneGroup.add(armGroup);
    });

    // 3-Axis Gimbal Sensor Turret (Below fuselage)
    const gimbalGroup = new THREE.Group();
    gimbalGroup.position.set(0, -0.35, 0.2);

    const gimbalBase = new THREE.Mesh(
      new THREE.CylinderGeometry(0.18, 0.18, 0.15, 12),
      carbonMat
    );
    gimbalGroup.add(gimbalBase);

    const cameraPod = new THREE.Mesh(
      new THREE.SphereGeometry(0.24, 16, 16),
      chassisMat
    );
    cameraPod.position.y = -0.15;
    gimbalGroup.add(cameraPod);

    const lensGeo = new THREE.CylinderGeometry(0.11, 0.11, 0.15, 16);
    lensGeo.rotateX(Math.PI / 2);
    const lensMat = new THREE.MeshStandardMaterial({
      color: 0x059669,
      roughness: 0.1,
      metalness: 0.9,
    });
    const lensMesh = new THREE.Mesh(lensGeo, lensMat);
    lensMesh.position.set(0, -0.18, 0.15);
    gimbalGroup.add(lensMesh);

    droneGroup.add(gimbalGroup);

    // --- 5. Volumetric-Looking Scanning Beam ---
    const scanBeamGroup = new THREE.Group();
    droneGroup.add(scanBeamGroup);

    // Conical LiDAR Scanning Frustum
    const coneRadius = 6.0;
    const coneHeight = 10.0;
    const beamGeo = new THREE.ConeGeometry(coneRadius, coneHeight, 32, 1, true);
    beamGeo.translate(0, -coneHeight / 2, 0);

    const beamMat = new THREE.MeshBasicMaterial({
      color: 0x00f5a0,
      transparent: true,
      opacity: 0.12,
      side: THREE.DoubleSide,
      blending: THREE.AdditiveBlending,
      depthWrite: false,
    });
    const beamMesh = new THREE.Mesh(beamGeo, beamMat);
    scanBeamGroup.add(beamMesh);

    // Scanning Ground Projection Ring
    const ringGeo = new THREE.RingGeometry(coneRadius - 0.2, coneRadius, 48);
    ringGeo.rotateX(-Math.PI / 2);
    const ringMat = new THREE.MeshBasicMaterial({
      color: 0x10b981,
      transparent: true,
      opacity: 0.6,
      side: THREE.DoubleSide,
      blending: THREE.AdditiveBlending,
    });
    const groundRing = new THREE.Mesh(ringGeo, ringMat);
    groundRing.position.y = -coneHeight + 0.05;
    scanBeamGroup.add(groundRing);

    // Crosshair Laser Sweep
    const sweepGeo = new THREE.PlaneGeometry(coneRadius * 2, 0.15);
    sweepGeo.rotateX(-Math.PI / 2);
    const sweepMat = new THREE.MeshBasicMaterial({
      color: 0x34d399,
      transparent: true,
      opacity: 0.8,
      blending: THREE.AdditiveBlending,
    });
    const laserSweep = new THREE.Mesh(sweepGeo, sweepMat);
    laserSweep.position.y = -coneHeight + 0.06;
    scanBeamGroup.add(laserSweep);

    // --- 6. Flight Path Visualization Spline ---
    const curvePoints = [
      new THREE.Vector3(-22, 5.5, -16),
      new THREE.Vector3(-12, 6.0, -8),
      new THREE.Vector3(0, 6.5, 0),
      new THREE.Vector3(12, 7.2, 8),
      new THREE.Vector3(20, 6.8, 18),
    ];
    const flightCurve = new THREE.CatmullRomCurve3(curvePoints);
    const flightGeo = new THREE.BufferGeometry().setFromPoints(flightCurve.getPoints(80));
    const flightMat = new THREE.LineBasicMaterial({
      color: 0x10b981,
      linewidth: 2,
      transparent: true,
      opacity: 0.65,
    });
    const flightLine = new THREE.Line(flightGeo, flightMat);
    scene.add(flightLine);

    // Waypoint Markers
    const waypointsGroup = new THREE.Group();
    curvePoints.forEach((pt, i) => {
      const wpMesh = new THREE.Mesh(
        new THREE.OctahedronGeometry(0.35, 0),
        new THREE.MeshBasicMaterial({ color: 0x00f5a0, wireframe: true })
      );
      wpMesh.position.copy(pt);
      waypointsGroup.add(wpMesh);

      // Vertical tether to ground
      const tetherGeo = new THREE.BufferGeometry().setFromPoints([
        new THREE.Vector3(pt.x, -2, pt.z),
        pt,
      ]);
      const tetherLine = new THREE.Line(
        tetherGeo,
        new THREE.LineDashedMaterial({
          color: 0x10b981,
          dashSize: 0.4,
          gapSize: 0.3,
          transparent: true,
          opacity: 0.3,
        })
      );
      tetherLine.computeLineDistances();
      waypointsGroup.add(tetherLine);
    });
    scene.add(waypointsGroup);

    // --- 7. Floating LiDAR Particle Dust ---
    const particleCount = 450;
    const particleGeo = new THREE.BufferGeometry();
    const particlePositions = new Float32Array(particleCount * 3);
    for (let i = 0; i < particleCount * 3; i += 3) {
      particlePositions[i] = (Math.random() - 0.5) * 55;
      particlePositions[i + 1] = Math.random() * 18 - 2;
      particlePositions[i + 2] = (Math.random() - 0.5) * 55;
    }
    particleGeo.setAttribute("position", new THREE.BufferAttribute(particlePositions, 3));
    const particleMat = new THREE.PointsMaterial({
      color: 0x34d399,
      size: 0.12,
      transparent: true,
      opacity: 0.5,
      blending: THREE.AdditiveBlending,
    });
    const particles = new THREE.Points(particleGeo, particleMat);
    scene.add(particles);

    // --- 8. Animation & Render Loop ---
    let animationFrameId: number;
    let clock = new THREE.Clock();

    const animate = () => {
      animationFrameId = requestAnimationFrame(animate);

      const delta = clock.getDelta();
      const elapsed = clock.getElapsedTime();

      // Spin rotors at realistic RPM
      const rotorSpeed = prefersReducedMotion ? 5 : 45;
      rotorGroups.forEach((r, idx) => {
        r.rotation.y += (idx % 2 === 0 ? 1 : -1) * rotorSpeed * delta;
      });

      // Subtle drone hover motion
      if (!prefersReducedMotion) {
        droneGroup.position.y = 6.5 + Math.sin(elapsed * 1.8) * 0.18;
        droneGroup.rotation.x = Math.sin(elapsed * 1.2) * 0.025;
        droneGroup.rotation.z = Math.cos(elapsed * 1.5) * 0.035;

        // Gimbal pitch & yaw tracking
        gimbalGroup.rotation.y = Math.sin(elapsed * 0.5) * 0.25;
        gimbalGroup.rotation.x = -0.15 + Math.cos(elapsed * 0.7) * 0.1;

        // Laser scan sweep rotation
        laserSweep.rotation.y += 1.8 * delta;

        // Scan beam pulsing
        beamMat.opacity = 0.09 + Math.sin(elapsed * 3) * 0.04;

        // Particle drift
        const pArr = particleGeo.attributes.position.array as Float32Array;
        for (let i = 1; i < particleCount * 3; i += 3) {
          pArr[i] += 0.8 * delta;
          if (pArr[i] > 16) pArr[i] = -2;
        }
        particleGeo.attributes.position.needsUpdate = true;
      }

      controls.update();
      renderer.render(scene, camera);
    };

    animate();

    // Telemetry periodic updater
    const telemTimer = setInterval(() => {
      setTelemetry((prev) => ({
        ...prev,
        altitude: +(124.5 + Math.sin(Date.now() / 1500) * 1.2).toFixed(1),
        groundSpeed: +(14.0 + Math.cos(Date.now() / 2000) * 0.6).toFixed(1),
        heading: (prev.heading + 0.1) % 360,
        pointsCollected: prev.pointsCollected + Math.floor(Math.random() * 45 + 15),
      }));
    }, 400);

    // --- 9. Window Resize Handling ---
    const handleResize = () => {
      if (!container) return;
      camera.aspect = container.clientWidth / container.clientHeight;
      camera.updateProjectionMatrix();
      renderer.setSize(container.clientWidth, container.clientHeight);
    };
    window.addEventListener("resize", handleResize);

    // --- 10. Memory Leak Prevention & Disposal ---
    return () => {
      clearInterval(telemTimer);
      window.removeEventListener("resize", handleResize);
      cancelAnimationFrame(animationFrameId);

      controls.dispose();

      // Dispose Geometries
      terrainGeo.dispose();
      bodyGeo.dispose();
      canopyGeo.dispose();
      gpsDomeGeo.dispose();
      beamGeo.dispose();
      ringGeo.dispose();
      sweepGeo.dispose();
      flightGeo.dispose();
      particleGeo.dispose();

      // Dispose Materials
      terrainMat.dispose();
      wireMat.dispose();
      chassisMat.dispose();
      carbonMat.dispose();
      rotorBladeMat.dispose();
      beamMat.dispose();
      ringMat.dispose();
      sweepMat.dispose();
      flightMat.dispose();
      particleMat.dispose();

      renderer.dispose();
      if (container.contains(renderer.domElement)) {
        container.removeChild(renderer.domElement);
      }
    };
  }, []);

  // Camera preset transitions
  const transitionCamera = (mode: "tactical" | "chase" | "sensor" | "wide") => {
    setCameraMode(mode);
    const camera = cameraRef.current;
    const controls = controlsRef.current;
    if (!camera || !controls) return;

    if (mode === "tactical") {
      camera.position.set(18, 14, 22);
      controls.target.set(0, 3, 0);
    } else if (mode === "chase") {
      camera.position.set(0, 8.5, -9);
      controls.target.set(0, 6.5, 8);
    } else if (mode === "sensor") {
      camera.position.set(0, 19, 0.1);
      controls.target.set(0, 0, 0);
    } else if (mode === "wide") {
      camera.position.set(38, 28, 42);
      controls.target.set(0, 0, 0);
    }
  };

  return (
    <div className="relative w-full h-[680px] lg:h-[780px] overflow-hidden bg-forest-950 border-b border-emerald-500/20 select-none">
      {/* 3D WebGL Canvas Mounting Node */}
      <div ref={containerRef} className="w-full h-full cursor-grab active:cursor-grabbing" />

      {/* Technical Coordinate Overlay Grid (Screen corners) */}
      <div className="hud-corner-tl m-4 pointer-events-none" />
      <div className="hud-corner-tr m-4 pointer-events-none" />
      <div className="hud-corner-bl m-4 pointer-events-none" />
      <div className="hud-corner-br m-4 pointer-events-none" />

      {/* Aerospace Telemetry Top Header */}
      <div className="absolute top-6 left-6 right-6 flex flex-wrap items-center justify-between gap-4 pointer-events-none">
        <div className="flex items-center gap-3">
          <div className="glass-panel px-3.5 py-1.5 rounded flex items-center gap-2.5">
            <span className="relative flex h-2 w-2">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75" />
              <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500" />
            </span>
            <span className="font-mono text-xs text-emerald-400 font-semibold tracking-wider">
              UAV ACTIVE // JATAYUV-01
            </span>
            <span className="text-muted-foreground text-xs font-mono">|</span>
            <span className="text-xs font-mono text-emerald-200">
              RTK-FIX ±1.2cm
            </span>
          </div>

          <div className="hidden sm:flex glass-panel px-3 py-1.5 rounded items-center gap-2 font-mono text-xs text-muted-foreground">
            <Radio className="w-3.5 h-3.5 text-emerald-400" />
            <span>LINK 5.8 GHz [100%]</span>
          </div>
        </div>

        {/* Camera Preset Toolbar (Pointer-events active) */}
        <div className="flex items-center gap-1.5 glass-panel p-1 rounded pointer-events-auto">
          <span className="text-[10px] font-mono uppercase tracking-wider text-muted-foreground px-2 hidden md:inline">
            CAMERA:
          </span>
          {(["tactical", "chase", "sensor", "wide"] as const).map((mode) => (
            <button
              key={mode}
              onClick={() => transitionCamera(mode)}
              className={`px-2.5 py-1 text-xs font-mono uppercase rounded transition-all ${
                cameraMode === mode
                  ? "bg-emerald-500/20 text-emerald-300 border border-emerald-400/40"
                  : "text-muted-foreground hover:text-white hover:bg-forest-800/60"
              }`}
            >
              {mode}
            </button>
          ))}
        </div>
      </div>

      {/* Floating Tactical Telemetry Panels (Left HUD) */}
      <div className="absolute top-24 left-6 hidden md:flex flex-col gap-3 pointer-events-none max-w-[240px]">
        <div className="glass-panel p-3.5 rounded text-xs space-y-2 font-mono border-l-2 border-l-emerald-500">
          <div className="flex items-center justify-between text-muted-foreground text-[10px] uppercase tracking-wider border-b border-emerald-500/15 pb-1">
            <span>SURVEY TELEMETRY</span>
            <Activity className="w-3 h-3 text-emerald-400" />
          </div>

          <div className="flex items-center justify-between">
            <span className="text-muted-foreground">ALTITUDE (AGL)</span>
            <span className="text-emerald-300 font-semibold">{telemetry.altitude} m</span>
          </div>

          <div className="flex items-center justify-between">
            <span className="text-muted-foreground">GROUND SPEED</span>
            <span className="text-emerald-300 font-semibold">{telemetry.groundSpeed} m/s</span>
          </div>

          <div className="flex items-center justify-between">
            <span className="text-muted-foreground">HEADING</span>
            <span className="text-white font-semibold">{telemetry.heading.toFixed(0)}° NE</span>
          </div>

          <div className="flex items-center justify-between">
            <span className="text-muted-foreground">BATTERY</span>
            <span className="text-emerald-400 font-semibold">{telemetry.batteryPct}% [24.2V]</span>
          </div>
        </div>

        <div className="glass-panel p-3 rounded text-[11px] space-y-1.5 font-mono">
          <div className="text-[10px] text-muted-foreground uppercase tracking-wider">PAYLOAD SENSOR</div>
          <div className="text-white font-medium flex items-center gap-1.5">
            <Zap className="w-3 h-3 text-emerald-400" /> Dual 42MP RGB + Multi-Lidar
          </div>
          <div className="text-muted-foreground text-[10px]">PULSE: {telemetry.pulseRate} | GSD: {telemetry.gsd}</div>
          <div className="text-emerald-400 font-semibold text-xs pt-0.5">
            {telemetry.pointsCollected.toLocaleString()} PTS INGESTED
          </div>
        </div>
      </div>

      {/* Right Tactical GPS & Compass Widget */}
      <div className="absolute top-24 right-6 hidden lg:flex flex-col gap-3 pointer-events-none max-w-[220px]">
        <div className="glass-panel p-3.5 rounded text-xs font-mono space-y-2">
          <div className="flex items-center justify-between text-[10px] text-muted-foreground uppercase tracking-wider border-b border-emerald-500/15 pb-1">
            <span>GEOLOCATION (WGS84)</span>
            <Navigation className="w-3 h-3 text-emerald-400" />
          </div>
          <div className="text-emerald-300 text-xs font-semibold">{telemetry.lat}</div>
          <div className="text-emerald-300 text-xs font-semibold">{telemetry.lon}</div>
          <div className="text-muted-foreground text-[10px]">UTM ZONE: 45N | ELLIPSOID H: 142.1m</div>
        </div>

        <div className="glass-panel p-2.5 rounded text-[11px] font-mono flex items-center justify-between">
          <span className="text-muted-foreground">FLIGHT LAW</span>
          <span className="text-emerald-400 font-semibold flex items-center gap-1">
            <ShieldCheck className="w-3 h-3" /> AUTO SURVEY
          </span>
        </div>
      </div>

      {/* Hero Headline & Tactical Action Bar (Bottom Overlay) */}
      <div className="absolute bottom-6 left-6 right-6 flex flex-col md:flex-row md:items-end justify-between gap-6 pointer-events-none">
        <div className="max-w-xl pointer-events-auto">
          <div className="inline-flex items-center gap-2 px-2.5 py-1 rounded bg-emerald-500/10 border border-emerald-500/25 text-emerald-400 text-xs font-mono mb-3">
            <Crosshair className="w-3.5 h-3.5" />
            <span>MODULE 02 // CINEMATIC GEOSPATIAL INTELLIGENCE</span>
          </div>

          <h1 className="text-3xl sm:text-4xl lg:text-5xl font-black tracking-tight text-white leading-tight">
            Autonomous Aerial AI &amp; <br />
            <span className="text-transparent bg-clip-text bg-gradient-to-r from-emerald-400 via-mint-bright to-emerald-300">
              3D Photogrammetry
            </span>
          </h1>

          <p className="mt-2.5 text-xs sm:text-sm text-gray-300 font-normal leading-relaxed">
            Convert UAV and aerial surveys into metric depth maps, 8-class land-use segmentation,
            humanitarian building damage evaluations, and dense 3D point cloud surface reconstructions.
          </p>
        </div>

        {/* Quick Interaction Buttons */}
        <div className="flex flex-wrap items-center gap-3 pointer-events-auto">
          <a
            href="/dashboard"
            className="inline-flex items-center justify-center h-10 px-5 text-sm font-semibold rounded bg-emerald-600 text-white hover:bg-emerald-500 border border-emerald-400/30 shadow-lg shadow-emerald-950/60 transition-all"
          >
            Launch Mission Control
          </a>
          <a
            href="#capabilities"
            className="inline-flex items-center justify-center h-10 px-4 text-sm font-medium rounded border border-emerald-500/30 bg-forest-900/80 hover:bg-emerald-500/15 text-emerald-300 hover:text-white transition-all font-mono"
          >
            Explore Capabilities ↓
          </a>
        </div>
      </div>

      {/* Interactive Helper Hint */}
      <div className="absolute bottom-2 left-1/2 -translate-x-1/2 text-[10px] font-mono text-muted-foreground/80 pointer-events-none hidden md:block">
        [ DRAG TO ORBIT // SCROLL TO ZOOM // MOUSE PARALLAX ACTIVE ]
      </div>
    </div>
  );
}


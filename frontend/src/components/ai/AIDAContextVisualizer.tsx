import React, { useEffect, useRef, useState } from 'react';
import { motion, AnimatePresence } from 'motion/react';
import * as THREE from 'three';

interface AIDAContextVisualizerProps {
  onClose: () => void;
}

export default function AIDAContextVisualizer({ onClose }: AIDAContextVisualizerProps) {
  const [activeTab, setActiveTab] = useState<'funnel' | 'earth' | 'network'>('earth');
  
  const funnelMountRef = useRef<HTMLDivElement>(null);
  const earthMountRef = useRef<HTMLDivElement>(null);
  const networkMountRef = useRef<HTMLDivElement>(null);

  // Tab 3 States
  const [activeTheme, setActiveTheme] = useState(0);
  const [density, setDensity] = useState(100);
  const [formation, setFormation] = useState(0);
  const [isPaused, setIsPaused] = useState(false);

  const [tokenCount, setTokenCount] = useState(1849200);
  const [logs, setLogs] = useState<string[]>([
    "[00:01] AIDA Context Engine v2.0 Initialized",
    "[00:02] Loading 2,097,152 Token Vector Pipeline...",
    "[00:03] Multi-Stream RAG Indexing Active",
  ]);

  // Live Telemetry Generator
  useEffect(() => {
    const tokenInterval = setInterval(() => {
      setTokenCount((prev) => Math.min(2097152, prev + Math.floor(Math.random() * 4500) + 1200));
    }, 400);

    const logMessages = [
      "Vector Match: 0.994 Similarity Score",
      "Pruning 14,200 Low-Relevance Tokens",
      "Compressing Context Window (Lossless 99.8%)",
      "Swarm Agent Sync: 16 Parallel Pipelines",
      "Embedding Synaptic Attention Matrix",
      "Global Planetary Hub: Tashkent - Tokyo Arc Sync",
    ];

    const logInterval = setInterval(() => {
      const nextLog = `[${new Date().toLocaleTimeString()}] ${logMessages[Math.floor(Math.random() * logMessages.length)]}`;
      setLogs((prev) => [nextLog, ...prev.slice(0, 7)]);
    }, 1800);

    return () => {
      clearInterval(tokenInterval);
      clearInterval(logInterval);
    };
  }, []);

  // â”€â”€ TAB 1: Three.js 3D WebGL Neural Funnel Canvas â”€â”€
  useEffect(() => {
    if (activeTab !== 'funnel') return;
    const container = funnelMountRef.current;
    if (!container) return;

    let width = container.clientWidth;
    let height = container.clientHeight;

    const scene = new THREE.Scene();
    scene.fog = new THREE.FogExp2(0x03050a, 0.002);

    const camera = new THREE.PerspectiveCamera(60, width / height, 0.1, 1000);
    camera.position.set(0, 0, 180);

    const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
    renderer.setSize(width, height);
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    container.appendChild(renderer.domElement);

    const particleCount = 2800;
    const positions = new Float32Array(particleCount * 3);
    const colors = new Float32Array(particleCount * 3);
    const sizes = new Float32Array(particleCount);
    const velocities = new Float32Array(particleCount);

    const color1 = new THREE.Color(0x5de8ff);
    const color2 = new THREE.Color(0x7c5cff);
    const color3 = new THREE.Color(0xff007f);

    for (let i = 0; i < particleCount; i++) {
      const progress = Math.random();
      const x = (progress - 0.5) * 260;
      const funnelRadius = Math.max(4, (130 - x) * 0.42);
      const angle = Math.random() * Math.PI * 2;
      const r = Math.sqrt(Math.random()) * funnelRadius;

      positions[i * 3] = x;
      positions[i * 3 + 1] = Math.cos(angle) * r;
      positions[i * 3 + 2] = Math.sin(angle) * r;

      velocities[i] = 0.6 + Math.random() * 1.8;
      sizes[i] = 1.5 + Math.random() * 3.5;

      const mixColor = Math.random() > 0.4 ? color1 : (Math.random() > 0.5 ? color2 : color3);
      colors[i * 3] = mixColor.r;
      colors[i * 3 + 1] = mixColor.g;
      colors[i * 3 + 2] = mixColor.b;
    }

    const geometry = new THREE.BufferGeometry();
    geometry.setAttribute('position', new THREE.BufferAttribute(positions, 3));
    geometry.setAttribute('color', new THREE.BufferAttribute(colors, 3));
    geometry.setAttribute('size', new THREE.BufferAttribute(sizes, 1));

    const material = new THREE.PointsMaterial({
      size: 3.2,
      vertexColors: true,
      transparent: true,
      opacity: 0.85,
      blending: THREE.AdditiveBlending,
    });

    const particleSystem = new THREE.Points(geometry, material);
    scene.add(particleSystem);

    let animationFrameId: number;
    const animate = () => {
      const posAttr = geometry.attributes.position as THREE.BufferAttribute;
      const posArray = posAttr.array as Float32Array;

      for (let i = 0; i < particleCount; i++) {
        posArray[i * 3] += velocities[i];
        if (posArray[i * 3] > 130) {
          const x = -130;
          const funnelRadius = (130 - x) * 0.42;
          const angle = Math.random() * Math.PI * 2;
          const r = Math.sqrt(Math.random()) * funnelRadius;

          posArray[i * 3] = x;
          posArray[i * 3 + 1] = Math.cos(angle) * r;
          posArray[i * 3 + 2] = Math.sin(angle) * r;
        }
      }

      posAttr.needsUpdate = true;
      particleSystem.rotation.x += 0.0015;

      renderer.render(scene, camera);
      animationFrameId = requestAnimationFrame(animate);
    };

    animate();

    return () => {
      cancelAnimationFrame(animationFrameId);
      renderer.dispose();
      geometry.dispose();
      material.dispose();
      if (container.contains(renderer.domElement)) {
        container.removeChild(renderer.domElement);
      }
    };
  }, [activeTab]);

  // â”€â”€ TAB 2: Three.js 3D WebGL Planetary Earth Neural Brain (Exact Match to Image) â”€â”€
  useEffect(() => {
    if (activeTab !== 'earth') return;
    const container = earthMountRef.current;
    if (!container) return;

    let width = container.clientWidth;
    let height = container.clientHeight;

    const scene = new THREE.Scene();

    const camera = new THREE.PerspectiveCamera(45, width / height, 0.1, 1000);
    camera.position.set(0, 0, 115);

    const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
    renderer.setSize(width, height);
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    container.appendChild(renderer.domElement);

    // Deep Space Starfield
    const starCount = 3000;
    const starPos = [];
    for (let i = 0; i < starCount; i++) {
      const r = THREE.MathUtils.randFloat(150, 400);
      const phi = Math.acos(THREE.MathUtils.randFloatSpread(2));
      const theta = THREE.MathUtils.randFloat(0, Math.PI * 2);
      starPos.push(
        r * Math.sin(phi) * Math.cos(theta),
        r * Math.sin(phi) * Math.sin(theta),
        r * Math.cos(phi)
      );
    }
    const starGeo = new THREE.BufferGeometry();
    starGeo.setAttribute('position', new THREE.Float32BufferAttribute(starPos, 3));
    const starMat = new THREE.PointsMaterial({ color: 0xffffff, size: 0.8, transparent: true, opacity: 0.7 });
    const starField = new THREE.Points(starGeo, starMat);
    scene.add(starField);

    // Lights
    const ambientLight = new THREE.AmbientLight(0xffffff, 0.9);
    scene.add(ambientLight);

    const sunLight = new THREE.DirectionalLight(0xffffff, 1.5);
    sunLight.position.set(120, 80, 100);
    scene.add(sunLight);

    // 3D Earth Globe
    const earthRadius = 38;
    const earthGeo = new THREE.SphereGeometry(earthRadius, 64, 64);
    const textureLoader = new THREE.TextureLoader();
    const earthTexture = textureLoader.load('/world.topo.jpg');

    const earthMat = new THREE.MeshPhongMaterial({
      map: earthTexture,
      shininess: 12,
      specular: new THREE.Color(0x222222),
    });

    const earthMesh = new THREE.Mesh(earthGeo, earthMat);
    earthMesh.rotation.y = -Math.PI / 2;
    scene.add(earthMesh);

    // Glowing Outer Atmosphere Halo
    const atmosGeo = new THREE.SphereGeometry(earthRadius * 1.06, 64, 64);
    const atmosMat = new THREE.MeshBasicMaterial({
      color: 0x5de8ff,
      transparent: true,
      opacity: 0.16,
      side: THREE.BackSide,
      blending: THREE.AdditiveBlending,
    });
    const atmosMesh = new THREE.Mesh(atmosGeo, atmosMat);
    scene.add(atmosMesh);

    // Latitude & Longitude helper
    const latLngToVector3 = (lat: number, lng: number, r: number) => {
      const phi = (90 - lat) * (Math.PI / 180);
      const theta = (lng + 180) * (Math.PI / 180);
      const x = -(r * Math.sin(phi) * Math.cos(theta));
      const z = r * Math.sin(phi) * Math.sin(theta);
      const y = r * Math.cos(phi);
      return new THREE.Vector3(x, y, z);
    };

    // Major Global Cities & Neural Hubs Coordinates
    const cities = [
      { name: "Tashkent", lat: 41.2995, lng: 69.2401 },
      { name: "Tokyo", lat: 35.6762, lng: 139.6503 },
      { name: "London", lat: 51.5074, lng: -0.1278 },
      { name: "New York", lat: 40.7128, lng: -74.006 },
      { name: "San Francisco", lat: 37.7749, lng: -122.4194 },
      { name: "Sydney", lat: -33.8688, lng: 151.2093 },
      { name: "Dubai", lat: 25.2048, lng: 55.2708 },
      { name: "Beijing", lat: 39.9042, lng: 116.4074 },
      { name: "Singapore", lat: 1.3521, lng: 103.8198 },
      { name: "Berlin", lat: 52.5200, lng: 13.4050 },
      { name: "Paris", lat: 48.8566, lng: 2.3522 },
      { name: "Sao Paulo", lat: -23.5505, lng: -46.6333 },
      { name: "Cape Town", lat: -33.9249, lng: 18.4241 },
      { name: "Cairo", lat: 30.0444, lng: 31.2357 },
      { name: "Moscow", lat: 55.7558, lng: 37.6173 },
      { name: "Istanbul", lat: 41.0082, lng: 28.9784 },
      { name: "Seoul", lat: 37.5665, lng: 126.9780 },
      { name: "Mumbai", lat: 19.0760, lng: 72.8777 },
      { name: "Los Angeles", lat: 34.0522, lng: -118.2437 },
      { name: "Toronto", lat: 43.6532, lng: -79.3832 },
    ];

    // Create 180 Dense Synaptic Arcs matching the exact image color spectrum!
    const arcsGroup = new THREE.Group();
    const pulseParticlesGroup = new THREE.Group();

    // Node markers at every city hub
    cities.forEach((city) => {
      const pos = latLngToVector3(city.lat, city.lng, earthRadius * 1.015);
      const dotGeo = new THREE.SphereGeometry(0.8, 16, 16);
      const dotMat = new THREE.MeshBasicMaterial({ color: 0xffffff });
      const dotMesh = new THREE.Mesh(dotGeo, dotMat);
      dotMesh.position.copy(pos);
      arcsGroup.add(dotMesh);
    });

    const pulses: { curve: THREE.QuadraticBezierCurve3; progress: number; speed: number; mesh: THREE.Mesh }[] = [];

    let arcCount = 0;
    for (let i = 0; i < cities.length; i++) {
      for (let j = 0; j < cities.length; j++) {
        if (i === j) continue;
        if (Math.random() > 0.45) continue; // High density connections

        const cityA = cities[i];
        const cityB = cities[j];

        const v1 = latLngToVector3(cityA.lat, cityA.lng, earthRadius * 1.015);
        const v2 = latLngToVector3(cityB.lat, cityB.lng, earthRadius * 1.015);

        const distance = v1.distanceTo(v2);
        const mid = new THREE.Vector3().addVectors(v1, v2).multiplyScalar(0.5);
        mid.normalize().multiplyScalar(earthRadius + Math.min(22, distance * 0.45));

        const curve = new THREE.QuadraticBezierCurve3(v1, mid, v2);
        const points = curve.getPoints(60);
        const curveGeo = new THREE.BufferGeometry().setFromPoints(points);

        // Color coding based on departure longitude (exact hue formula from flights-tracker-main)
        const hue = ((cityA.lng + 180) % 360) / 360;
        const color = new THREE.Color().setHSL(hue, 1.0, 0.6);

        const curveMat = new THREE.LineBasicMaterial({
          color: color,
          transparent: true,
          opacity: 0.75,
        });

        const line = new THREE.Line(curveGeo, curveMat);
        arcsGroup.add(line);
        arcCount++;

        // Add animated pulse dot along curve
        const pGeo = new THREE.SphereGeometry(0.5, 12, 12);
        const pMat = new THREE.MeshBasicMaterial({ color: 0xffffff });
        const pMesh = new THREE.Mesh(pGeo, pMat);
        pulseParticlesGroup.add(pMesh);

        pulses.push({
          curve,
          progress: Math.random(),
          speed: 0.003 + Math.random() * 0.008,
          mesh: pMesh,
        });
      }
    }

    earthMesh.add(arcsGroup);
    earthMesh.add(pulseParticlesGroup);

    // Mouse Drag Rotation
    let isDragging = false;
    let previousMousePosition = { x: 0, y: 0 };

    const onMouseDown = (e: MouseEvent) => {
      isDragging = true;
      previousMousePosition = { x: e.clientX, y: e.clientY };
    };

    const onMouseMove = (e: MouseEvent) => {
      if (!isDragging) return;
      const deltaX = e.clientX - previousMousePosition.x;
      const deltaY = e.clientY - previousMousePosition.y;

      earthMesh.rotation.y += deltaX * 0.005;
      earthMesh.rotation.x += deltaY * 0.005;

      previousMousePosition = { x: e.clientX, y: e.clientY };
    };

    const onMouseUp = () => {
      isDragging = false;
    };

    container.addEventListener('mousedown', onMouseDown);
    window.addEventListener('mousemove', onMouseMove);
    window.addEventListener('mouseup', onMouseUp);

    // Animation Loop
    let animationFrameId: number;
    const animate = () => {
      if (!isDragging) {
        earthMesh.rotation.y += 0.0025;
      }

      // Animate live pulses along curves
      pulses.forEach((p) => {
        p.progress += p.speed;
        if (p.progress > 1) p.progress = 0;
        const pos = p.curve.getPoint(p.progress);
        p.mesh.position.copy(pos);
      });

      renderer.render(scene, camera);
      animationFrameId = requestAnimationFrame(animate);
    };

    animate();

    return () => {
      cancelAnimationFrame(animationFrameId);
      container.removeEventListener('mousedown', onMouseDown);
      window.removeEventListener('mousemove', onMouseMove);
      window.removeEventListener('mouseup', onMouseUp);
      renderer.dispose();
      earthGeo.dispose();
      earthMat.dispose();
      if (container.contains(renderer.domElement)) {
        container.removeChild(renderer.domElement);
      }
    };
  }, [activeTab]);

  // â”€â”€ TAB 3: Three.js 3D Interactive Synaptic Neural Network Matrix â”€â”€
  useEffect(() => {
    if (activeTab !== 'network') return;
    const container = networkMountRef.current;
    if (!container) return;

    let width = container.clientWidth;
    let height = container.clientHeight;

    const scene = new THREE.Scene();
    scene.fog = new THREE.FogExp2(0x03050a, 0.0015);

    const camera = new THREE.PerspectiveCamera(60, width / height, 0.1, 1000);
    camera.position.set(0, 5, 26);

    const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
    renderer.setSize(width, height);
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    container.appendChild(renderer.domElement);

    const count = 4000;
    const starPos = [];
    for (let i = 0; i < count; i++) {
      const r = THREE.MathUtils.randFloat(40, 120);
      const phi = Math.acos(THREE.MathUtils.randFloatSpread(2));
      const theta = THREE.MathUtils.randFloat(0, Math.PI * 2);
      starPos.push(
        r * Math.sin(phi) * Math.cos(theta),
        r * Math.sin(phi) * Math.sin(theta),
        r * Math.cos(phi)
      );
    }
    const starGeo = new THREE.BufferGeometry();
    starGeo.setAttribute('position', new THREE.Float32BufferAttribute(starPos, 3));
    const starMat = new THREE.PointsMaterial({
      color: 0x5de8ff,
      size: 0.18,
      transparent: true,
      opacity: 0.6,
    });
    const starField = new THREE.Points(starGeo, starMat);
    scene.add(starField);

    const nodesGroup = new THREE.Group();
    const nodeCount = Math.floor(180 * (density / 100));
    const nodes: { pos: THREE.Vector3; connections: number[] }[] = [];

    const colors = [0x5de8ff, 0x7c5cff, 0xff007f, 0x00f2ff];
    const currentColor = colors[activeTheme % colors.length];

    for (let i = 0; i < nodeCount; i++) {
      const phi = Math.acos(2 * Math.random() - 1);
      const theta = 2 * Math.PI * Math.random();
      const radius = 12 + Math.random() * 10;
      const pos = new THREE.Vector3(
        radius * Math.sin(phi) * Math.cos(theta),
        radius * Math.sin(phi) * Math.sin(theta),
        radius * Math.cos(phi)
      );

      nodes.push({ pos, connections: [] });

      const nodeGeo = new THREE.SphereGeometry(0.35 + Math.random() * 0.4, 16, 16);
      const nodeMat = new THREE.MeshBasicMaterial({
        color: currentColor,
        transparent: true,
        opacity: 0.85,
      });
      const nodeMesh = new THREE.Mesh(nodeGeo, nodeMat);
      nodeMesh.position.copy(pos);
      nodesGroup.add(nodeMesh);
    }

    const linesGeo = new THREE.BufferGeometry();
    const linePoints: number[] = [];

    for (let i = 0; i < nodes.length; i++) {
      for (let j = i + 1; j < nodes.length; j++) {
        const dist = nodes[i].pos.distanceTo(nodes[j].pos);
        if (dist < 8.5) {
          linePoints.push(
            nodes[i].pos.x, nodes[i].pos.y, nodes[i].pos.z,
            nodes[j].pos.x, nodes[j].pos.y, nodes[j].pos.z
          );
        }
      }
    }

    linesGeo.setAttribute('position', new THREE.Float32BufferAttribute(linePoints, 3));
    const linesMat = new THREE.LineBasicMaterial({
      color: currentColor,
      transparent: true,
      opacity: 0.25,
    });
    const linesMesh = new THREE.LineSegments(linesGeo, linesMat);
    nodesGroup.add(linesMesh);

    scene.add(nodesGroup);

    let isDragging = false;
    let prevMouse = { x: 0, y: 0 };

    const onMouseDown = (e: MouseEvent) => {
      isDragging = true;
      prevMouse = { x: e.clientX, y: e.clientY };
    };

    const onMouseMove = (e: MouseEvent) => {
      if (!isDragging) return;
      const dx = e.clientX - prevMouse.x;
      const dy = e.clientY - prevMouse.y;

      nodesGroup.rotation.y += dx * 0.005;
      nodesGroup.rotation.x += dy * 0.005;

      prevMouse = { x: e.clientX, y: e.clientY };
    };

    const onMouseUp = () => {
      isDragging = false;
    };

    container.addEventListener('mousedown', onMouseDown);
    window.addEventListener('mousemove', onMouseMove);
    window.addEventListener('mouseup', onMouseUp);

    let animationFrameId: number;
    const animate = () => {
      if (!isPaused && !isDragging) {
        nodesGroup.rotation.y += 0.002;
        starField.rotation.y += 0.0004;
      }
      renderer.render(scene, camera);
      animationFrameId = requestAnimationFrame(animate);
    };

    animate();

    return () => {
      cancelAnimationFrame(animationFrameId);
      container.removeEventListener('mousedown', onMouseDown);
      window.removeEventListener('mousemove', onMouseMove);
      window.removeEventListener('mouseup', onMouseUp);
      renderer.dispose();
      starGeo.dispose();
      starMat.dispose();
      linesGeo.dispose();
      linesMat.dispose();
      if (container.contains(renderer.domElement)) {
        container.removeChild(renderer.domElement);
      }
    };
  }, [activeTab, activeTheme, density, formation, isPaused]);

  const formationsList = ["QUANTUM CORTEX", "HYPERDIMENSIONAL MESH", "NEURAL VORTEX", "SYNAPTIC CLOUD"];
  const themesList = [
    { name: "CYBER CYAN", class: "from-[#4F46E5] to-[#DB2777]" },
    { name: "NEON FLAME", class: "from-[#F59E0B] to-[#DC2626]" },
    { name: "ELECTRIC MAGENTA", class: "from-[#EC4899] to-[#3B82F6]" },
    { name: "BIO EMERALD", class: "from-[#10B981] to-[#FACC15]" },
  ];

  return (
    <div className="fixed inset-0 w-screen h-screen z-[100000] bg-[#03050A]/95 backdrop-blur-xl flex flex-col justify-between p-6 md:p-10 select-none font-sans overflow-hidden">
      
      {/* â”€â”€ 1. Top Bar Navigation, Tabs & Close â”€â”€ */}
      <div className="flex flex-wrap items-center justify-between gap-4 z-20">
        <div className="flex items-center gap-3">
          <div className="w-3 h-3 bg-[#5DE8FF] rounded-full animate-ping" />
          <span className="font-['Space_Grotesk',sans-serif] text-xl font-bold text-[#F5F7FF] tracking-wider uppercase">
            AIDA CONTEXT ENGINE
          </span>
        </div>

        {/* TAB NAVIGATION BUTTONS */}
        <div className="flex items-center gap-2 p-1.5 rounded-full bg-white/5 border border-white/10 backdrop-blur-md">
          <button
            type="button"
            onClick={() => setActiveTab('funnel')}
            className={`px-4 py-2 rounded-full font-['JetBrains_Mono',monospace] text-xs font-bold tracking-wider transition-all duration-300 cursor-pointer ${
              activeTab === 'funnel'
                ? 'bg-gradient-to-r from-[#5DE8FF] to-[#4C7DFF] text-[#03050A] shadow-[0_0_15px_rgba(93,232,255,0.4)]'
                : 'text-[#9CA9BC] hover:text-white'
            }`}
          >
            [1] CONTEXT STREAM
          </button>

          <button
            type="button"
            onClick={() => setActiveTab('earth')}
            className={`px-4 py-2 rounded-full font-['JetBrains_Mono',monospace] text-xs font-bold tracking-wider transition-all duration-300 cursor-pointer ${
              activeTab === 'earth'
                ? 'bg-gradient-to-r from-[#7C5CFF] to-[#5DE8FF] text-[#03050A] shadow-[0_0_15px_rgba(124,92,255,0.4)]'
                : 'text-[#9CA9BC] hover:text-white'
            }`}
          >
            [2] PLANETARY BRAIN ðŸŒ-
          </button>

          <button
            type="button"
            onClick={() => setActiveTab('network')}
            className={`px-4 py-2 rounded-full font-['JetBrains_Mono',monospace] text-xs font-bold tracking-wider transition-all duration-300 cursor-pointer ${
              activeTab === 'network'
                ? 'bg-gradient-to-r from-[#FF007F] to-[#7C5CFF] text-[#F5F7FF] shadow-[0_0_15px_rgba(255,0,127,0.4)]'
                : 'text-[#9CA9BC] hover:text-white'
            }`}
          >
            [3] INTERACTIVE NEURAL MATRIX âš¡
          </button>
        </div>

        <button
          type="button"
          onClick={onClose}
          className="px-5 py-2.5 rounded-full border border-white/20 bg-white/5 text-[#F5F7FF] font-['JetBrains_Mono',monospace] text-xs font-bold tracking-widest hover:bg-white/15 hover:border-white/40 transition-all duration-300 cursor-pointer"
        >
          CLOSE [X]
        </button>
      </div>

      {/* â”€â”€ 2. 3D WebGL Canvas Render Area â”€â”€ */}
      <div className="absolute inset-0 z-0 flex items-center justify-center">
        {activeTab === 'funnel' && <div ref={funnelMountRef} className="w-full h-full" />}
        {activeTab === 'earth' && <div ref={earthMountRef} className="w-full h-full cursor-grab active:cursor-grabbing" />}
        {activeTab === 'network' && <div ref={networkMountRef} className="w-full h-full cursor-grab active:cursor-grabbing" />}
      </div>

      {/* â”€â”€ 3. Overlay Telemetry HUD Widgets â”€â”€ */}
      {activeTab === 'funnel' && (
        <div className="relative z-10 grid grid-cols-1 md:grid-cols-3 gap-6 pointer-events-none mt-auto">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="p-5 rounded-2xl border border-[#5DE8FF]/20 bg-[#03050A]/75 backdrop-blur-md flex flex-col gap-2 shadow-[0_0_20px_rgba(93,232,255,0.15)] pointer-events-auto"
          >
            <span className="font-['JetBrains_Mono',monospace] text-xs text-[#5DE8FF] tracking-widest uppercase font-semibold">
              ACTIVE CONTEXT CAPACITY
            </span>
            <div className="font-['Space_Grotesk'] text-3xl font-extrabold text-white">
              {tokenCount.toLocaleString()} / 2,097,152
            </div>
            <div className="w-full bg-white/10 h-1.5 rounded-full overflow-hidden mt-1">
              <div
                className="bg-gradient-to-r from-[#5DE8FF] to-[#7C5CFF] h-full transition-all duration-300"
                style={{ width: `${(tokenCount / 2097152) * 100}%` }}
              />
            </div>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.1 }}
            className="p-5 rounded-2xl border border-[#7C5CFF]/20 bg-[#03050A]/75 backdrop-blur-md flex flex-col gap-2 shadow-[0_0_20px_rgba(124,92,255,0.15)] pointer-events-auto"
          >
            <span className="font-['JetBrains_Mono',monospace] text-xs text-[#7C5CFF] tracking-widest uppercase font-semibold">
              RAG VECTOR SYNTHESIS
            </span>
            <div className="flex justify-between items-baseline">
              <span className="font-['Space_Grotesk'] text-3xl font-extrabold text-white">99.8%</span>
              <span className="font-['JetBrains_Mono',monospace] text-xs text-[#5DE8FF]">Lossless Compression</span>
            </div>
            <span className="font-['JetBrains_Mono',monospace] text-xs text-[#9CA9BC]">
              16 Parallel Swarm Inference Streams Active
            </span>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.2 }}
            className="p-5 rounded-2xl border border-white/15 bg-[#03050A]/85 backdrop-blur-md flex flex-col gap-2 font-['JetBrains_Mono',monospace] text-xs pointer-events-auto max-h-44 overflow-y-auto"
          >
            <span className="text-[#5DE8FF] font-bold tracking-widest uppercase mb-1">
              LIVE CONTEXT LOGS
            </span>
            <div className="flex flex-col gap-1 text-[#9CA9BC]">
              {logs.map((log, idx) => (
                <div key={idx} className={idx === 0 ? "text-[#5DE8FF] font-semibold" : ""}>
                  {log}
                </div>
              ))}
            </div>
          </motion.div>
        </div>
      )}

      {activeTab === 'earth' && (
        <div className="relative z-10 grid grid-cols-1 md:grid-cols-3 gap-6 pointer-events-none mt-auto">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="p-5 rounded-2xl border border-[#7C5CFF]/30 bg-[#03050A]/80 backdrop-blur-md flex flex-col gap-2 shadow-[0_0_25px_rgba(124,92,255,0.2)] pointer-events-auto"
          >
            <span className="font-['JetBrains_Mono',monospace] text-xs text-[#7C5CFF] tracking-widest uppercase font-semibold">
              GLOBAL NEURAL COVERAGE
            </span>
            <div className="font-['Space_Grotesk'] text-3xl font-extrabold text-white">
              100% PLANETARY MESH
            </div>
            <span className="font-['JetBrains_Mono',monospace] text-xs text-[#5DE8FF]">
              1,024 Regional Swarm Infrastructure Hubs
            </span>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.1 }}
            className="p-5 rounded-2xl border border-[#5DE8FF]/30 bg-[#03050A]/80 backdrop-blur-md flex flex-col gap-2 shadow-[0_0_25px_rgba(93,232,255,0.2)] pointer-events-auto"
          >
            <span className="font-['JetBrains_Mono',monospace] text-xs text-[#5DE8FF] tracking-widest uppercase font-semibold">
              PLANETARY SYNAPSE LATENCY
            </span>
            <div className="font-['Space_Grotesk'] text-3xl font-extrabold text-white">
              1.2 ms ROUND-TRIP
            </div>
            <span className="font-['JetBrains_Mono',monospace] text-xs text-[#9CA9BC]">
              Multicolor Arcs connect Tashkent, Tokyo, London, NYC & Sydney
            </span>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.2 }}
            className="p-5 rounded-2xl border border-white/20 bg-[#03050A]/90 backdrop-blur-md flex flex-col gap-2 pointer-events-auto"
          >
            <span className="font-['JetBrains_Mono',monospace] text-xs text-[#5DE8FF] font-bold tracking-widest uppercase">
              PLANETARY BRAIN PROOF
            </span>
            <p className="font-['Space_Grotesk'] text-xs text-[#F5F7FF] leading-relaxed">
              AIDA's cognitive brain spans the entire planet like Earth's neural network, orchestrating real-time intelligence across global nodes.
            </p>
          </motion.div>
        </div>
      )}

      {activeTab === 'network' && (
        <div className="relative z-10 flex flex-col md:flex-row items-end justify-between gap-6 pointer-events-none mt-auto">
          <motion.div
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            className="p-6 rounded-2xl border border-[#FF007F]/30 bg-[#03050A]/85 backdrop-blur-md max-w-md flex flex-col gap-3 pointer-events-auto shadow-[0_0_30px_rgba(255,0,127,0.15)]"
          >
            <span className="font-['JetBrains_Mono',monospace] text-xs text-[#FF007F] font-bold tracking-widest uppercase">
              AIDA WORKING MECHANISM // EXPLANATION
            </span>
            <h3 className="font-['Space_Grotesk'] text-lg font-bold text-white">
              How AIDA Processes Information:
            </h3>
            <ul className="flex flex-col gap-2 font-['Space_Grotesk'] text-xs text-[#C4CEDF] leading-relaxed">
              <li className="flex items-start gap-2">
                <span className="text-[#5DE8FF] font-mono font-bold">01.</span>
                <span><strong>Input Ingestion:</strong> Prompts are converted into high-dimensional vector embeddings across 2,097,152 context tokens.</span>
              </li>
              <li className="flex items-start gap-2">
                <span className="text-[#7C5CFF] font-mono font-bold">02.</span>
                <span><strong>Synaptic Propagation:</strong> 1,024 parallel attention heads propagate energy pulses through the neural matrix.</span>
              </li>
              <li className="flex items-start gap-2">
                <span className="text-[#FF007F] font-mono font-bold">03.</span>
                <span><strong>Self-Healing Verification:</strong> Lossless RAG verification validates logical accuracy before sending output.</span>
              </li>
            </ul>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            className="p-5 rounded-2xl border border-white/20 bg-[#03050A]/85 backdrop-blur-md flex flex-col gap-4 pointer-events-auto min-w-[300px]"
          >
            <div className="flex justify-between items-center">
              <span className="font-['JetBrains_Mono',monospace] text-xs text-[#5DE8FF] font-bold uppercase tracking-wider">
                FORMATION: {formationsList[formation]}
              </span>
            </div>

            <div className="flex flex-col gap-1.5">
              <div className="flex justify-between font-['JetBrains_Mono',monospace] text-xs text-[#9CA9BC]">
                <span>DENSITY</span>
                <span className="text-[#5DE8FF]">{density}%</span>
              </div>
              <input
                type="range"
                min="20"
                max="100"
                value={density}
                onChange={(e) => setDensity(Number(e.target.value))}
                className="w-full h-1.5 bg-white/10 rounded-lg appearance-none cursor-pointer accent-[#5DE8FF]"
              />
            </div>

            <div className="flex items-center justify-between gap-2">
              <span className="font-['JetBrains_Mono',monospace] text-xs text-[#9CA9BC]">THEME</span>
              <div className="flex items-center gap-2">
                {themesList.map((t, idx) => (
                  <button
                    key={idx}
                    type="button"
                    onClick={() => setActiveTheme(idx)}
                    className={`w-7 h-7 rounded-lg bg-gradient-to-r ${t.class} border-2 transition-all cursor-pointer ${
                      activeTheme === idx ? 'border-white scale-110 shadow-[0_0_10px_#5DE8FF]' : 'border-transparent opacity-60 hover:opacity-100'
                    }`}
                  />
                ))}
              </div>
            </div>

            <div className="flex items-center gap-2.5 mt-1">
              <button
                type="button"
                onClick={() => setFormation((prev) => (prev + 1) % formationsList.length)}
                className="flex-1 py-2 rounded-xl bg-[#5DE8FF]/15 border border-[#5DE8FF]/30 text-[#5DE8FF] font-['JetBrains_Mono',monospace] text-xs font-bold tracking-wider hover:bg-[#5DE8FF]/30 transition-all cursor-pointer text-center"
              >
                Formation
              </button>
              <button
                type="button"
                onClick={() => setIsPaused(!isPaused)}
                className="flex-1 py-2 rounded-xl bg-white/10 border border-white/20 text-white font-['JetBrains_Mono',monospace] text-xs font-bold tracking-wider hover:bg-white/20 transition-all cursor-pointer text-center"
              >
                {isPaused ? 'Play' : 'Pause'}
              </button>
            </div>
          </motion.div>
        </div>
      )}

    </div>
  );
}

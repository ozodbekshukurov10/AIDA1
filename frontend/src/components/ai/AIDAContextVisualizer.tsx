import React, { useEffect, useRef, useState } from 'react';
import { motion } from 'motion/react';
import * as THREE from 'three';

interface AIDAContextVisualizerProps {
  onClose: () => void;
}

export default function AIDAContextVisualizer({ onClose }: AIDAContextVisualizerProps) {
  const mountRef = useRef<HTMLDivElement>(null);
  const [tokenCount, setTokenCount] = useState(1849200);
  const [activeSignal, setActiveSignal] = useState('CYBER_CYAN');
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
      "Memory Retrieval: Fast Vector Cache hit",
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

  // Three.js 3D WebGL Neural Funnel Particle Stream Engine
  useEffect(() => {
    const container = mountRef.current;
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

    // Create 3D Funnel Particle Geometry
    const particleCount = 2800;
    const positions = new Float32Array(particleCount * 3);
    const colors = new Float32Array(particleCount * 3);
    const sizes = new Float32Array(particleCount);
    const velocities = new Float32Array(particleCount);

    const color1 = new THREE.Color(0x5de8ff); // Cyan
    const color2 = new THREE.Color(0x7c5cff); // Purple
    const color3 = new THREE.Color(0xff007f); // Magenta

    for (let i = 0; i < particleCount; i++) {
      // Funnel shape: wide on left (negative X), tight beam on right (positive X)
      const progress = Math.random(); // 0 to 1 along X axis
      const x = (progress - 0.5) * 260; // -130 to +130
      
      // Radius shrinks dramatically as X increases to form the funnel
      const funnelRadius = Math.max(4, (130 - x) * 0.42);
      const angle = Math.random() * Math.PI * 2;
      const r = Math.sqrt(Math.random()) * funnelRadius;

      positions[i * 3] = x;
      positions[i * 3 + 1] = Math.cos(angle) * r;
      positions[i * 3 + 2] = Math.sin(angle) * r;

      velocities[i] = 0.6 + Math.random() * 1.8;
      sizes[i] = 1.5 + Math.random() * 3.5;

      // Color gradient
      const mixColor = Math.random() > 0.4 ? color1 : (Math.random() > 0.5 ? color2 : color3);
      colors[i * 3] = mixColor.r;
      colors[i * 3 + 1] = mixColor.g;
      colors[i * 3 + 2] = mixColor.b;
    }

    const geometry = new THREE.BufferGeometry();
    geometry.setAttribute('position', new THREE.BufferAttribute(positions, 3));
    geometry.setAttribute('color', new THREE.BufferAttribute(colors, 3));
    geometry.setAttribute('size', new THREE.BufferAttribute(sizes, 1));

    // Particle Material
    const material = new THREE.PointsMaterial({
      size: 3.2,
      vertexColors: true,
      transparent: true,
      opacity: 0.85,
      blending: THREE.AdditiveBlending,
    });

    const particleSystem = new THREE.Points(geometry, material);
    scene.add(particleSystem);

    // Add Central Glowing Synapse Line Beam
    const lineGeometry = new THREE.BufferGeometry();
    const linePoints = [];
    for (let x = -140; x <= 140; x += 5) {
      linePoints.push(new THREE.Vector3(x, 0, 0));
    }
    lineGeometry.setFromPoints(linePoints);

    const lineMaterial = new THREE.LineBasicMaterial({
      color: 0x5de8ff,
      transparent: true,
      opacity: 0.6,
      linewidth: 2,
    });
    const lineBeam = new THREE.Line(lineGeometry, lineMaterial);
    scene.add(lineBeam);

    // Animation Loop
    let animationFrameId: number;
    const animate = () => {
      const posAttr = geometry.attributes.position as THREE.BufferAttribute;
      const posArray = posAttr.array as Float32Array;

      for (let i = 0; i < particleCount; i++) {
        // Move particles along funnel (left to right)
        posArray[i * 3] += velocities[i];

        // Reset particle if it passes end of funnel
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

    const handleResize = () => {
      if (!container) return;
      width = container.clientWidth;
      height = container.clientHeight;
      camera.aspect = width / height;
      camera.updateProjectionMatrix();
      renderer.setSize(width, height);
    };

    window.addEventListener('resize', handleResize);

    return () => {
      cancelAnimationFrame(animationFrameId);
      window.removeEventListener('resize', handleResize);
      renderer.dispose();
      geometry.dispose();
      material.dispose();
      if (container.contains(renderer.domElement)) {
        container.removeChild(renderer.domElement);
      }
    };
  }, []);

  return (
    <div className="fixed inset-0 w-screen h-screen z-[100000] bg-[#03050A]/95 backdrop-blur-xl flex flex-col justify-between p-6 md:p-10 select-none font-sans overflow-hidden">
      
      {/* â”€â”€ 1. Top Bar Navigation & Close â”€â”€ */}
      <div className="flex items-center justify-between z-20">
        <div className="flex items-center gap-3">
          <div className="w-3 h-3 bg-[#5DE8FF] rounded-full animate-ping" />
          <span className="font-['Space_Grotesk',sans-serif] text-xl font-bold text-[#F5F7FF] tracking-wider uppercase">
            AIDA CONTEXT ENGINE
          </span>
          <span className="px-3 py-1 rounded-full bg-[#5DE8FF]/15 border border-[#5DE8FF]/30 text-[#5DE8FF] font-['JetBrains_Mono',monospace] text-xs font-bold uppercase">
            2,097,152 TOKENS LIVE
          </span>
        </div>

        <button
          type="button"
          onClick={onClose}
          className="px-5 py-2.5 rounded-full border border-white/20 bg-white/5 text-[#F5F7FF] font-['JetBrains_Mono',monospace] text-xs font-bold tracking-widest hover:bg-white/15 hover:border-white/40 transition-all duration-300 cursor-pointer"
        >
          CLOSE [X]
        </button>
      </div>

      {/* â”€â”€ 2. Three.js 3D WebGL Neural Funnel Canvas â”€â”€ */}
      <div className="absolute inset-0 z-0 flex items-center justify-center">
        <div ref={mountRef} className="w-full h-full" />
      </div>

      {/* â”€â”€ 3. Overlay Telemetry HUD Widgets â”€â”€ */}
      <div className="relative z-10 grid grid-cols-1 md:grid-cols-3 gap-6 pointer-events-none mt-auto">
        
        {/* Widget 1: Token Capacity Meter */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="p-5 rounded-2xl border border-[#5DE8FF]/20 bg-[#03050A]/75 backdrop-blur-md flex flex-col gap-2 shadow-[0_0_20px_rgba(93,232,255,0.15)] pointer-events-auto"
        >
          <span className="font-['JetBrains_Mono',monospace] text-xs text-[#5DE8FF] tracking-widest uppercase">
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

        {/* Widget 2: Compression & Latency */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
          className="p-5 rounded-2xl border border-[#7C5CFF]/20 bg-[#03050A]/75 backdrop-blur-md flex flex-col gap-2 shadow-[0_0_20px_rgba(124,92,255,0.15)] pointer-events-auto"
        >
          <span className="font-['JetBrains_Mono',monospace] text-xs text-[#7C5CFF] tracking-widest uppercase">
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

        {/* Widget 3: Live Telemetry Terminal Logs */}
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

    </div>
  );
}

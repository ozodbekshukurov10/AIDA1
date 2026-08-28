/**
 * AIBrain.tsx — Phase 4 Neural Intelligence Visualization
 *
 * Canvas 2D implementation of a scientifically-inspired computational
 * neural architecture. 7 named intelligence clusters + central core +
 * signal propagation + active region system + 3D depth + breathing.
 *
 * Color semantics:
 *   Cyan   #5DE8FF → INPUT / PERCEPTION (active intelligence)
 *   Blue   #4C7DFF → CONTEXT (information processing)
 *   Violet #7C5CFF → REASONING (logic & planning)
 *   Purple #A78BFA → TOOLS (capability layer)
 *   White  #F5F7FF → VERIFICATION / RESPONSE (output)
 */

import React, { useEffect, useRef, useCallback } from 'react';

// ─── Types ─────────────────────────────────────────────────────────────────

export type BrainRegion =
  | 'idle'
  | 'perception'
  | 'context'
  | 'reasoning'
  | 'planning'
  | 'tools'
  | 'memory'
  | 'verification'
  | 'response';

export interface AIBrainProps {
  activeRegion?: BrainRegion;
  autoCycle?: boolean;       // auto-rotate through regions (hero idle demo)
  className?: string;
}

// ─── Constants ─────────────────────────────────────────────────────────────

const CLUSTERS: {
  id: BrainRegion;
  label: string;
  // Normalized position -1..1, scaled to canvas
  nx: number;
  ny: number;
  nodeCount: number;
  spreadRadius: number; // normalized spread
  color: string;
  signalColor: string;
}[] = [
  { id: 'perception',   label: 'PERCEPTION',   nx: -0.52, ny: -0.22, nodeCount: 14, spreadRadius: 0.12, color: '#5DE8FF', signalColor: '#5DE8FF' },
  { id: 'context',      label: 'CONTEXT',       nx: -0.24, ny: -0.46, nodeCount: 12, spreadRadius: 0.11, color: '#4C7DFF', signalColor: '#4C7DFF' },
  { id: 'reasoning',    label: 'REASONING',     nx: 0.26,  ny: -0.42, nodeCount: 16, spreadRadius: 0.13, color: '#7C5CFF', signalColor: '#7C5CFF' },
  { id: 'planning',     label: 'PLANNING',      nx: 0.50,  ny: -0.12, nodeCount: 10, spreadRadius: 0.10, color: '#6B7FFF', signalColor: '#6B7FFF' },
  { id: 'tools',        label: 'TOOLS',         nx: 0.46,  ny: 0.28,  nodeCount: 12, spreadRadius: 0.11, color: '#A78BFA', signalColor: '#A78BFA' },
  { id: 'memory',       label: 'MEMORY',        nx: -0.16, ny: 0.46,  nodeCount: 11, spreadRadius: 0.10, color: '#7C5CFF', signalColor: '#8B70FF' },
  { id: 'verification', label: 'VERIFICATION',  nx: -0.50, ny: 0.20,  nodeCount: 13, spreadRadius: 0.12, color: '#5DE8FF', signalColor: '#C8F5FF' },
];

const CYCLE_ORDER: BrainRegion[] = [
  'perception', 'context', 'reasoning', 'planning',
  'tools', 'memory', 'verification', 'response',
];

const CYCLE_DURATION = 3800; // ms per region in auto cycle

// ─── Utility ───────────────────────────────────────────────────────────────

function rand(min: number, max: number) {
  return min + Math.random() * (max - min);
}

function hexToRgb(hex: string): [number, number, number] {
  const r = parseInt(hex.slice(1, 3), 16);
  const g = parseInt(hex.slice(3, 5), 16);
  const b = parseInt(hex.slice(5, 7), 16);
  return [r, g, b];
}

// ─── Internal data structures ───────────────────────────────────────────────

interface BrainNode {
  // canvas-space coords (set each resize based on canvas size)
  x: number;
  y: number;
  z: number;            // depth -1..1
  cluster: BrainRegion | 'core' | 'bg';
  color: string;
  baseRadius: number;
  brightness: number;   // 0..1, animated
  pulse: number;        // local phase offset
}

interface Connection {
  a: number;   // node index
  b: number;   // node index
  strength: number;  // 0..1
  interCluster: boolean;
  flashDecay: number; // 0..1 → decays when signal passes
}

interface Signal {
  // travels along a connection edge
  connIdx: number;
  progress: number;   // 0..1
  forward: boolean;   // direction along edge
  color: string;
  alpha: number;
  speed: number;
  active: boolean;
}

// ─── Brain Engine Class ─────────────────────────────────────────────────────

class BrainEngine {
  private nodes: BrainNode[] = [];
  private connections: Connection[] = [];
  private signals: Signal[] = [];
  private signalPool: Signal[] = [];

  private W = 0;
  private H = 0;
  private isMobile = false;

  // Normalized cluster positions → canvas coords
  private clusterCenters: { [key: string]: { x: number; y: number } } = {};

  // State
  activeRegion: BrainRegion = 'idle';
  private breathPhase = 0;
  private breathScale = 1;
  private time = 0;

  // Preallocate signal pool
  constructor() {
    for (let i = 0; i < 20; i++) {
      this.signalPool.push({
        connIdx: 0, progress: 0, forward: true,
        color: '#5DE8FF', alpha: 0, speed: 0, active: false,
      });
    }
  }

  resize(W: number, H: number) {
    this.W = W;
    this.H = H;
    this.isMobile = W < 768;
    this.rebuildNodes();
    this.rebuildConnections();
  }

  private toCanvas(nx: number, ny: number) {
    const margin = this.isMobile ? 0.7 : 0.82;
    return {
      x: this.W / 2 + nx * (this.W / 2) * margin,
      y: this.H / 2 + ny * (this.H / 2) * margin,
    };
  }

  private rebuildNodes() {
    this.nodes = [];
    this.clusterCenters = {};

    const isMobile = this.isMobile;
    const bgCount = isMobile ? 30 : 80;
    const fgCount = isMobile ? 8 : 18;

    // Background scatter (tiny dim nodes)
    for (let i = 0; i < bgCount; i++) {
      this.nodes.push({
        x: rand(0, this.W),
        y: rand(0, this.H),
        z: rand(-1, -0.4),
        cluster: 'bg',
        color: '#4C7DFF',
        baseRadius: rand(0.8, 1.6),
        brightness: rand(0.1, 0.2),
        pulse: rand(0, Math.PI * 2),
      });
    }

    // Central CORE node
    this.nodes.push({
      x: this.W / 2,
      y: this.H / 2,
      z: 0.5,
      cluster: 'core',
      color: '#5DE8FF',
      baseRadius: isMobile ? 5 : 7,
      brightness: 1,
      pulse: 0,
    });

    // Cluster nodes
    CLUSTERS.forEach(cluster => {
      const cc = this.toCanvas(cluster.nx, cluster.ny);
      this.clusterCenters[cluster.id] = cc;

      const count = isMobile ? Math.ceil(cluster.nodeCount * 0.55) : cluster.nodeCount;

      for (let i = 0; i < count; i++) {
        const angle = (i / count) * Math.PI * 2 + rand(-0.3, 0.3);
        const dist = rand(0, cluster.spreadRadius * Math.min(this.W, this.H) * 0.5);
        this.nodes.push({
          x: cc.x + Math.cos(angle) * dist,
          y: cc.y + Math.sin(angle) * dist,
          z: rand(-0.2, 0.8),
          cluster: cluster.id,
          color: cluster.color,
          baseRadius: rand(1.5, isMobile ? 3 : 4),
          brightness: 0.3,
          pulse: rand(0, Math.PI * 2),
        });
      }
    });

    // Foreground accent nodes (larger, near center)
    for (let i = 0; i < fgCount; i++) {
      const angle = (i / fgCount) * Math.PI * 2;
      const dist = rand(0.08, 0.18) * Math.min(this.W, this.H);
      this.nodes.push({
        x: this.W / 2 + Math.cos(angle) * dist,
        y: this.H / 2 + Math.sin(angle) * dist,
        z: rand(0.5, 1),
        cluster: 'core',
        color: i % 3 === 0 ? '#5DE8FF' : i % 3 === 1 ? '#4C7DFF' : '#7C5CFF',
        baseRadius: rand(2.5, isMobile ? 4 : 5.5),
        brightness: 0.5,
        pulse: rand(0, Math.PI * 2),
      });
    }
  }

  private rebuildConnections() {
    this.connections = [];
    const maxDist = this.isMobile ? 110 : 160;
    const maxInterClusterDist = this.isMobile ? 180 : 240;
    const coreNode = this.nodes.findIndex(n => n.cluster === 'core' && n.z > 0.4);

    for (let i = 0; i < this.nodes.length; i++) {
      const ni = this.nodes[i];
      if (ni.cluster === 'bg') continue;

      for (let j = i + 1; j < this.nodes.length; j++) {
        const nj = this.nodes[j];
        if (nj.cluster === 'bg') continue;

        const dx = ni.x - nj.x;
        const dy = ni.y - nj.y;
        const d = Math.sqrt(dx * dx + dy * dy);

        const isSame = ni.cluster === nj.cluster;
        const isOneCore = ni.cluster === 'core' || nj.cluster === 'core';
        const limit = isOneCore ? maxInterClusterDist * 1.3 : (isSame ? maxDist : maxInterClusterDist);

        if (d < limit) {
          const strength = 1 - d / limit;
          this.connections.push({
            a: i, b: j,
            strength: strength * (isSame ? 1 : 0.45),
            interCluster: !isSame,
            flashDecay: 0,
          });
        }
      }
    }

    // Limit total connections for performance
    const maxConn = this.isMobile ? 200 : 600;
    if (this.connections.length > maxConn) {
      this.connections.sort((a, b) => b.strength - a.strength);
      this.connections = this.connections.slice(0, maxConn);
    }
  }

  setActiveRegion(region: BrainRegion) {
    this.activeRegion = region;
  }

  private getSignalFromPool(): Signal | null {
    return this.signalPool.find(s => !s.active) ?? null;
  }

  private spawnSignal() {
    const region = this.activeRegion;
    if (region === 'idle') return;

    const cluster = CLUSTERS.find(c => c.id === region);
    const signalColor = cluster?.signalColor ?? '#5DE8FF';

    // Find connections within active cluster
    const clusterConns = this.connections.filter(conn => {
      const na = this.nodes[conn.a];
      const nb = this.nodes[conn.b];
      return na.cluster === region || nb.cluster === region;
    });

    if (clusterConns.length === 0) return;

    const conn = clusterConns[Math.floor(Math.random() * clusterConns.length)];
    const connIdx = this.connections.indexOf(conn);
    if (connIdx < 0) return;

    const sig = this.getSignalFromPool();
    if (!sig) return;

    sig.connIdx = connIdx;
    sig.progress = 0;
    sig.forward = Math.random() > 0.5;
    sig.color = signalColor;
    sig.alpha = 1;
    sig.speed = rand(0.008, 0.018);
    sig.active = true;
  }

  update(deltaTime: number) {
    this.time += deltaTime;

    // Breathing
    this.breathPhase += deltaTime * 0.55;
    this.breathScale = 0.975 + 0.025 * Math.sin(this.breathPhase);

    const active = this.activeRegion;

    // Update node brightness
    this.nodes.forEach((node, i) => {
      const isActive = node.cluster === active;
      const isCoreActive = node.cluster === 'core';
      const targetBrightness = isActive ? rand(0.75, 1) : (isCoreActive ? 0.7 : (node.cluster === 'bg' ? 0.12 : 0.18));
      node.brightness += (targetBrightness - node.brightness) * deltaTime * 2.5;
    });

    // Update signals
    this.signalPool.forEach(sig => {
      if (!sig.active) return;
      sig.progress += sig.speed;
      sig.alpha -= deltaTime * 0.3;

      if (sig.progress >= 1 || sig.alpha <= 0) {
        sig.active = false;
        return;
      }

      // Flash the connection
      if (sig.connIdx < this.connections.length) {
        this.connections[sig.connIdx].flashDecay = Math.max(
          this.connections[sig.connIdx].flashDecay,
          sig.alpha
        );
      }
    });

    // Decay connection flashes
    this.connections.forEach(c => {
      c.flashDecay = Math.max(0, c.flashDecay - deltaTime * 2.5);
    });

    // Spawn new signals
    if (active !== 'idle' && Math.random() < deltaTime * 4) {
      this.spawnSignal();
    }

    // Response: extra convergence signals from all clusters to core
    if (active === 'response' && Math.random() < deltaTime * 8) {
      const coreConns = this.connections.filter(c => {
        return this.nodes[c.a].cluster === 'core' || this.nodes[c.b].cluster === 'core';
      });
      if (coreConns.length > 0) {
        const conn = coreConns[Math.floor(Math.random() * coreConns.length)];
        const idx = this.connections.indexOf(conn);
        const sig = this.getSignalFromPool();
        if (sig && idx >= 0) {
          const aCore = this.nodes[conn.a].cluster === 'core';
          sig.connIdx = idx;
          sig.progress = 0;
          sig.forward = aCore ? false : true; // towards core
          sig.color = '#F5F7FF';
          sig.alpha = 1;
          sig.speed = rand(0.012, 0.022);
          sig.active = true;
        }
      }
    }
  }

  draw(ctx: CanvasRenderingContext2D) {
    const W = this.W;
    const H = this.H;
    const t = this.time;
    const bs = this.breathScale;
    const active = this.activeRegion;

    ctx.clearRect(0, 0, W, H);

    // --- Background radial glow ---
    const bgGrad = ctx.createRadialGradient(W / 2, H / 2, 0, W / 2, H / 2, Math.max(W, H) * 0.65);
    bgGrad.addColorStop(0, 'rgba(76,125,255,0.04)');
    bgGrad.addColorStop(0.5, 'rgba(93,232,255,0.02)');
    bgGrad.addColorStop(1, 'transparent');
    ctx.fillStyle = bgGrad;
    ctx.beginPath();
    ctx.arc(W / 2, H / 2, Math.max(W, H) * 0.65, 0, Math.PI * 2);
    ctx.fill();

    // Active cluster glow
    if (active !== 'idle' && active !== 'response') {
      const cc = this.clusterCenters[active];
      const cluster = CLUSTERS.find(c => c.id === active);
      if (cc && cluster) {
        const [r, g, b] = hexToRgb(cluster.color);
        const glow = ctx.createRadialGradient(cc.x, cc.y, 0, cc.x, cc.y, 100);
        glow.addColorStop(0, `rgba(${r},${g},${b},0.14)`);
        glow.addColorStop(1, 'transparent');
        ctx.fillStyle = glow;
        ctx.beginPath();
        ctx.arc(cc.x, cc.y, 100, 0, Math.PI * 2);
        ctx.fill();
      }
    }

    // Response: core convergence glow
    if (active === 'response') {
      const coreGrad = ctx.createRadialGradient(W / 2, H / 2, 0, W / 2, H / 2, 140 * bs);
      coreGrad.addColorStop(0, 'rgba(93,232,255,0.22)');
      coreGrad.addColorStop(0.5, 'rgba(76,125,255,0.08)');
      coreGrad.addColorStop(1, 'transparent');
      ctx.fillStyle = coreGrad;
      ctx.beginPath();
      ctx.arc(W / 2, H / 2, 140 * bs, 0, Math.PI * 2);
      ctx.fill();
    }

    // --- Depth-sort nodes for drawing ---
    const sortedIndices = this.nodes
      .map((_, i) => i)
      .sort((a, b) => this.nodes[a].z - this.nodes[b].z);

    // --- Draw connections ---
    this.connections.forEach(conn => {
      const na = this.nodes[conn.a];
      const nb = this.nodes[conn.b];

      const baseAlpha = conn.strength * 0.18;
      const flashAlpha = conn.flashDecay * 0.7;
      const alpha = Math.min(1, baseAlpha + flashAlpha);
      if (alpha < 0.01) return;

      const [r, g, b] = hexToRgb(conn.flashDecay > 0.1 ? na.color : '#4C7DFF');
      ctx.strokeStyle = `rgba(${r},${g},${b},${alpha})`;
      ctx.lineWidth = conn.interCluster ? 0.5 : (0.6 + conn.strength * 0.6);
      ctx.beginPath();
      ctx.moveTo(na.x, na.y);
      ctx.lineTo(nb.x, nb.y);
      ctx.stroke();
    });

    // --- Draw signal particles ---
    this.signalPool.forEach(sig => {
      if (!sig.active || sig.connIdx >= this.connections.length) return;
      const conn = this.connections[sig.connIdx];
      const na = this.nodes[conn.a];
      const nb = this.nodes[conn.b];

      const p = sig.forward ? sig.progress : 1 - sig.progress;
      const sx = na.x + (nb.x - na.x) * p;
      const sy = na.y + (nb.y - na.y) * p;

      const [r, g, bl] = hexToRgb(sig.color);
      const glow = ctx.createRadialGradient(sx, sy, 0, sx, sy, 10);
      glow.addColorStop(0, `rgba(${r},${g},${bl},${sig.alpha})`);
      glow.addColorStop(0.4, `rgba(${r},${g},${bl},${sig.alpha * 0.35})`);
      glow.addColorStop(1, 'transparent');
      ctx.fillStyle = glow;
      ctx.beginPath();
      ctx.arc(sx, sy, 10, 0, Math.PI * 2);
      ctx.fill();

      // Bright core dot
      ctx.fillStyle = `rgba(${r},${g},${bl},${sig.alpha * 0.95})`;
      ctx.beginPath();
      ctx.arc(sx, sy, 2.2, 0, Math.PI * 2);
      ctx.fill();
    });

    // --- Draw nodes ---
    sortedIndices.forEach(i => {
      const node = this.nodes[i];
      const depthAlpha = (node.z + 1) / 2; // 0..1
      const pulseMod = 1 + 0.1 * Math.sin(t * 1.4 + node.pulse);
      const r = node.baseRadius * pulseMod * (node.cluster === 'core' && node.z > 0.4 ? bs : 1);

      const [nr, ng, nb] = hexToRgb(node.color);
      const alpha = depthAlpha * node.brightness;

      // Glow halo for bright nodes
      if (node.brightness > 0.5 && node.cluster !== 'bg') {
        const halo = ctx.createRadialGradient(node.x, node.y, 0, node.x, node.y, r * 5);
        halo.addColorStop(0, `rgba(${nr},${ng},${nb},${alpha * 0.4})`);
        halo.addColorStop(1, 'transparent');
        ctx.fillStyle = halo;
        ctx.beginPath();
        ctx.arc(node.x, node.y, r * 5, 0, Math.PI * 2);
        ctx.fill();
      }

      // Node circle
      ctx.fillStyle = `rgba(${nr},${ng},${nb},${alpha})`;
      ctx.beginPath();
      ctx.arc(node.x, node.y, Math.max(0.5, r), 0, Math.PI * 2);
      ctx.fill();
    });

    // --- Central AIDA Core ---
    const coreR = (this.isMobile ? 18 : 26) * bs;
    const coreGrad = ctx.createRadialGradient(W / 2, H / 2, 0, W / 2, H / 2, coreR * 3.5);
    const corePulse = 0.5 + 0.5 * Math.sin(t * 1.1 + this.breathPhase);
    coreGrad.addColorStop(0, `rgba(93,232,255,${0.28 * corePulse + 0.05})`);
    coreGrad.addColorStop(0.45, `rgba(76,125,255,${0.12 * corePulse})`);
    coreGrad.addColorStop(1, 'transparent');
    ctx.fillStyle = coreGrad;
    ctx.beginPath();
    ctx.arc(W / 2, H / 2, coreR * 3.5, 0, Math.PI * 2);
    ctx.fill();

    // Core ring
    ctx.beginPath();
    ctx.arc(W / 2, H / 2, coreR, 0, Math.PI * 2);
    ctx.strokeStyle = `rgba(93,232,255,${0.55 + 0.3 * corePulse})`;
    ctx.lineWidth = 1.2;
    ctx.stroke();
    ctx.fillStyle = 'rgba(3,5,10,0.88)';
    ctx.fill();

    // Outer orbit rings
    ctx.save();
    ctx.translate(W / 2, H / 2);
    ctx.rotate(t * 0.09);
    ctx.beginPath();
    ctx.ellipse(0, 0, coreR * 2.6, coreR * 1.1, 0, 0, Math.PI * 2);
    ctx.strokeStyle = `rgba(93,232,255,${0.07 + 0.04 * Math.sin(t)})`;
    ctx.lineWidth = 0.8;
    ctx.stroke();
    ctx.rotate(-t * 0.18);
    ctx.beginPath();
    ctx.ellipse(0, 0, coreR * 2.1, coreR * 1.6, Math.PI / 4, 0, Math.PI * 2);
    ctx.strokeStyle = `rgba(124,92,255,${0.06 + 0.03 * Math.cos(t * 0.7)})`;
    ctx.stroke();
    ctx.restore();

    // Core label
    const fontSize = this.isMobile ? 9 : 11;
    ctx.fillStyle = `rgba(93,232,255,${0.85 + 0.15 * corePulse})`;
    ctx.font = `600 ${fontSize}px 'Space Grotesk', sans-serif`;
    ctx.textAlign = 'center';
    ctx.textBaseline = 'middle';
    ctx.fillText('AIDA', W / 2, H / 2);

    // --- Cluster region labels ---
    CLUSTERS.forEach(cluster => {
      const cc = this.clusterCenters[cluster.id];
      if (!cc) return;

      const isActive = active === cluster.id;
      const alpha = isActive ? 0.85 : 0.28;
      const [r, g, b] = hexToRgb(cluster.color);

      const labelFontSize = this.isMobile ? 7.5 : 9.5;
      ctx.font = `500 ${labelFontSize}px 'JetBrains Mono', 'Space Mono', monospace`;
      ctx.textAlign = 'center';
      ctx.textBaseline = 'top';

      // Label anchor: push label away from center
      const dx = cc.x - W / 2;
      const dy = cc.y - H / 2;
      const len = Math.sqrt(dx * dx + dy * dy) || 1;
      const labelOffset = (this.isMobile ? 32 : 42);
      const lx = cc.x + (dx / len) * labelOffset;
      const ly = cc.y + (dy / len) * labelOffset - 6;

      // Label background for readability
      const textW = ctx.measureText(cluster.label).width;
      ctx.fillStyle = `rgba(3,5,10,${isActive ? 0.75 : 0.4})`;
      ctx.beginPath();
      if (typeof (ctx as any).roundRect === 'function') {
        (ctx as any).roundRect(lx - textW / 2 - 5, ly - 2, textW + 10, labelFontSize + 6, 3);
      } else {
        ctx.rect(lx - textW / 2 - 5, ly - 2, textW + 10, labelFontSize + 6);
      }
      ctx.fill();

      ctx.fillStyle = `rgba(${r},${g},${b},${alpha})`;
      ctx.fillText(cluster.label, lx, ly);

      // Active region dot indicator
      if (isActive) {
        ctx.fillStyle = `rgba(${r},${g},${b},0.9)`;
        ctx.beginPath();
        ctx.arc(cc.x, cc.y, 3, 0, Math.PI * 2);
        ctx.fill();
      }
    });
  }

  destroy() {
    this.nodes = [];
    this.connections = [];
    this.signalPool.forEach(s => { s.active = false; });
  }
}

// ─── React Component ────────────────────────────────────────────────────────

export default function AIBrain({ activeRegion = 'idle', autoCycle = true, className = '' }: AIBrainProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const engineRef = useRef<BrainEngine | null>(null);
  const animRef = useRef<number>(0);
  const lastTimeRef = useRef<number>(0);
  const cycleTimerRef = useRef<number>(0);
  const cycleIdxRef = useRef<number>(0);
  const externalRegionRef = useRef<BrainRegion>(activeRegion);

  // Sync external region prop
  useEffect(() => {
    externalRegionRef.current = activeRegion;
    if (!autoCycle && engineRef.current) {
      engineRef.current.setActiveRegion(activeRegion);
    }
  }, [activeRegion, autoCycle]);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    const engine = new BrainEngine();
    engineRef.current = engine;

    const resize = () => {
      const parent = canvas.parentElement;
      const W = parent ? parent.clientWidth : window.innerWidth;
      const H = parent ? parent.clientHeight : window.innerHeight;
      canvas.width = W * Math.min(window.devicePixelRatio, 2);
      canvas.height = H * Math.min(window.devicePixelRatio, 2);
      canvas.style.width = `${W}px`;
      canvas.style.height = `${H}px`;
      ctx.scale(Math.min(window.devicePixelRatio, 2), Math.min(window.devicePixelRatio, 2));
      engine.resize(W, H);
    };
    resize();
    window.addEventListener('resize', resize);

    const loop = (ts: number) => {
      const dt = Math.min((ts - lastTimeRef.current) / 1000, 0.05);
      lastTimeRef.current = ts;

      // Auto-cycle logic
      if (autoCycle) {
        cycleTimerRef.current += dt * 1000;
        if (cycleTimerRef.current >= CYCLE_DURATION) {
          cycleTimerRef.current = 0;
          cycleIdxRef.current = (cycleIdxRef.current + 1) % CYCLE_ORDER.length;
          engine.setActiveRegion(CYCLE_ORDER[cycleIdxRef.current]);
        }
      }

      engine.update(dt);
      engine.draw(ctx);
      animRef.current = requestAnimationFrame(loop);
    };

    // Start first cycle
    if (autoCycle) {
      engine.setActiveRegion(CYCLE_ORDER[0]);
    }

    animRef.current = requestAnimationFrame(loop);

    return () => {
      cancelAnimationFrame(animRef.current);
      window.removeEventListener('resize', resize);
      engine.destroy();
    };
  }, [autoCycle]);

  return (
    <canvas
      ref={canvasRef}
      className={`absolute inset-0 w-full h-full block ${className}`}
    />
  );
}

import * as THREE from 'three';

export type DepthLayer = 'fg' | 'mg' | 'bg';

export interface ParticleData {
  pos: THREE.Vector3;
  targetPos: THREE.Vector3;
  floatPos: THREE.Vector3;
  logoPos: THREE.Vector3;
  corePos: THREE.Vector3;
  velocity: THREE.Vector3;
  color: THREE.Color;
  size: number;
  speed: number;
  layer: DepthLayer;
}

// ─── High-Precision Parametric 3D Particle Constellations (A I D A) ─────────
function getLogoPosition(index: number, count: number, layer: DepthLayer): THREE.Vector3 {
  const group = index % 4; // Split particles equally between A, I, D, A
  const t = Math.random();
  
  let z = -1.8 + (Math.random() - 0.5) * 0.4;
  if (layer === 'fg') z += 1.2;
  if (layer === 'bg') z -= 1.8;

  let x = 0;
  let y = 0;

  if (group === 0) {
    // ─── First Letter 'A' (Centered at X = -6.5) ───────────────────────────
    const sub = index % 3;
    if (sub === 0) {
      // Left diagonal leg
      x = -8.0 + t * 1.5;
      y = -2.8 + t * 5.6;
    } else if (sub === 1) {
      // Right diagonal leg
      x = -6.5 + t * 1.5;
      y = 2.8 - t * 5.6;
    } else {
      // Horizontal crossbar
      x = -7.25 + t * 1.5;
      y = 0.0;
    }
  } else if (group === 1) {
    // ─── Letter 'I' (Centered at X = -2.2) ──────────────────────────────────
    const sub = index % 3;
    if (sub === 0) {
      // Main vertical spine
      x = -2.2;
      y = -2.8 + t * 5.6;
    } else if (sub === 1) {
      // Top cap crossbar
      x = -2.9 + t * 1.4;
      y = 2.8;
    } else {
      // Bottom cap crossbar
      x = -2.9 + t * 1.4;
      y = -2.8;
    }
  } else if (group === 2) {
    // ─── Letter 'D' (Centered at X = +2.2, Geometrically Perfect) ───────────
    const sub = index % 3;
    if (sub === 0) {
      // Main vertical spine
      x = 1.3;
      y = -2.8 + t * 5.6;
    } else if (sub === 1) {
      // Top/bottom horizontal caps
      const isTop = (index % 2) === 0;
      x = 1.3 + t * 0.9;
      y = isTop ? 2.8 : -2.8;
    } else {
      // Smooth 180° semi-elliptical outer curve (rX: 1.8, rY: 2.8)
      const theta = -Math.PI / 2 + t * Math.PI;
      x = 1.3 + Math.cos(theta) * 1.8;
      y = Math.sin(theta) * 2.8;
    }
  } else {
    // ─── Second Letter 'A' (Centered at X = +6.5) ──────────────────────────
    const sub = index % 3;
    if (sub === 0) {
      // Left diagonal leg
      x = 5.0 + t * 1.5;
      y = -2.8 + t * 5.6;
    } else if (sub === 1) {
      // Right diagonal leg
      x = 6.5 + t * 1.5;
      y = 2.8 - t * 5.6;
    } else {
      // Horizontal crossbar
      x = 5.75 + t * 1.5;
      y = 0.0;
    }
  }

  // Micro-jitter for organic constellation distribution
  x += (Math.random() - 0.5) * 0.10;
  y += (Math.random() - 0.5) * 0.10;

  return new THREE.Vector3(x, y, z);
}

// Spherical Archimedes distribution for AI Core
function getCorePosition(index: number, count: number, layer: DepthLayer): THREE.Vector3 {
  const isInner = index % 4 === 0;
  let radius = isInner ? 1.2 + Math.random() * 0.6 : 3.4 + (Math.random() - 0.5) * 0.5;
  
  if (layer === 'fg') radius += 1.8;
  if (layer === 'bg') radius -= 0.8;

  const goldenRatio = (1 + Math.sqrt(5)) / 2;
  const theta = 2 * Math.PI * index / goldenRatio;
  const phi = Math.acos(1 - 2 * (index + 0.5) / count);

  const x = radius * Math.sin(phi) * Math.cos(theta);
  const y = radius * Math.sin(phi) * Math.sin(theta);
  const z = radius * Math.cos(phi);

  return new THREE.Vector3(x, y, z);
}

export function createParticles(count: number): ParticleData[] {
  const particles: ParticleData[] = [];

  for (let i = 0; i < count; i++) {
    // Synced Color Palette Ratio (Matching bg-video.mp4): 40% Ultraviolet, 30% Neon Magenta, 20% Electric Cyan, 10% White
    let color: THREE.Color;
    const cRand = Math.random();
    if (cRand < 0.40) color = new THREE.Color('#8B5CF6');      // Ultraviolet
    else if (cRand < 0.70) color = new THREE.Color('#EC4899'); // Neon Magenta
    else if (cRand < 0.90) color = new THREE.Color('#5DE8FF'); // Electric Cyan
    else color = new THREE.Color('#FFFFFF');                  // White Highlights

    // Assign Depth Layer: 15% Foreground, 60% Midground, 25% Background
    let layer: DepthLayer = 'mg';
    const rand = Math.random();
    if (rand < 0.15) layer = 'fg';
    else if (rand > 0.75) layer = 'bg';

    // Set Z boundary by layer
    let zDepth = (Math.random() - 0.5) * 10;
    let size = Math.random() * 0.06 + 0.03;
    let baseSpeed = 0.025 + Math.random() * 0.02;

    if (layer === 'fg') {
      zDepth = 5 + Math.random() * 7;
      size = Math.random() * 0.12 + 0.08;
      baseSpeed = 0.04 + Math.random() * 0.03;
    } else if (layer === 'bg') {
      zDepth = -16 + Math.random() * 8;
      size = Math.random() * 0.03 + 0.015;
      baseSpeed = 0.015 + Math.random() * 0.015;
    }

    const floatPos = new THREE.Vector3(
      (Math.random() - 0.5) * 38,
      (Math.random() - 0.5) * 22,
      zDepth
    );

    const initialPos = new THREE.Vector3(
      (Math.random() - 0.5) * 0.15,
      (Math.random() - 0.5) * 0.15,
      (Math.random() - 0.5) * 0.15
    );

    particles.push({
      pos: initialPos,
      targetPos: floatPos.clone(),
      floatPos,
      logoPos: getLogoPosition(i, count, layer),
      corePos: getCorePosition(i, count, layer),
      velocity: new THREE.Vector3(
        (Math.random() - 0.5) * 0.02,
        (Math.random() - 0.5) * 0.02,
        (Math.random() - 0.5) * 0.02
      ),
      color,
      size,
      speed: baseSpeed,
      layer
    });
  }

  return particles;
}

export function updateParticles(
  particles: ParticleData[],
  phase: number,
  time: number,
  mouseX: number,
  mouseY: number,
  isReducedMotion: boolean
) {
  const isMobile = window.innerWidth < 768;

  particles.forEach((p, idx) => {
    // Determine Target Position based on Intro Phase
    if (phase === 0) {
      // Opening: Slow drift from origin
      const driftX = Math.sin(time * 0.4 + idx) * 0.4;
      const driftY = Math.cos(time * 0.3 + idx) * 0.4;
      p.targetPos.set(
        p.floatPos.x * 0.08 + driftX,
        p.floatPos.y * 0.08 + driftY,
        p.floatPos.z * 0.08
      );
    } 
    else if (phase === 1) {
      // Phase 1: High-Precision 3D Particle Constellations (A I D A)
      p.targetPos.copy(p.logoPos);
      p.targetPos.x += Math.sin(time * 1.5 + idx) * 0.04;
      p.targetPos.y += Math.cos(time * 1.2 + idx) * 0.04;
    } 
    else if (phase === 2) {
      // Phase 2: Shift left to balance story text
      p.targetPos.set(
        p.logoPos.x * 0.6 - 4.5,
        p.logoPos.y * 0.6,
        p.logoPos.z
      );
    } 
    else if (phase === 3) {
      // Phase 3: Transition towards AI Core formation
      const morphFactor = (Math.sin(time * 0.8) + 1) * 0.5;
      p.targetPos.lerpVectors(p.logoPos, p.corePos, morphFactor);
    } 
    else if (phase === 10) {
      // Phase 10: Global Neural Convergence — Wave-like pull toward center
      const layerDelay = p.layer === 'bg' ? 0.3 : (p.layer === 'mg' ? 0.6 : 1.0);
      const pull = Math.min(1.0, Math.max(0.1, (time % 4.0) * 0.4 * layerDelay));
      p.targetPos.set(
        p.corePos.x * (1.2 - pull * 0.8),
        p.corePos.y * (1.2 - pull * 0.8),
        p.corePos.z * (1.2 - pull * 0.8)
      );
    }
    else if (phase === 11) {
      // Phase 11: Core Power-Up & Implosion -> Silence Pause
      const implosionProgress = Math.min(1.0, (time % 5.0) / 4.0);
      const radiusScale = 1.0 - Math.pow(implosionProgress, 2) * 0.75;
      
      p.targetPos.set(
        p.corePos.x * radiusScale,
        p.corePos.y * radiusScale,
        p.corePos.z * radiusScale
      );
    }
    else if (phase === 12) {
      // Phase 12: MASSIVE AIDA BRAND REVEAL — Safe Zone Ambient Halo
      const angle = (idx / particles.length) * Math.PI * 2 + time * 0.15;
      const haloRadius = 4.2 + (idx % 7) * 0.3;
      
      p.targetPos.set(
        Math.cos(angle) * haloRadius + (Math.sin(time * 1.5 + idx) * 0.2),
        Math.sin(angle) * haloRadius * 0.6 + (Math.cos(time * 1.2 + idx) * 0.2),
        (Math.sin(idx) * 2.5) - 2.0 // Positioned in background aura behind text
      );
    }
    else if (phase === 13) {
      // Phase 13: Final Transition — Thrust outward as camera passes through
      p.targetPos.set(
        p.floatPos.x * 2.5,
        p.floatPos.y * 2.5,
        p.floatPos.z * 2.5
      );
    }
    else if (phase >= 4 && phase <= 9) {
      // Phase 4–9: AI Brain Core Spherical Cloud
      const floatFactor = 0.55;
      p.targetPos.set(
        p.corePos.x * floatFactor + p.floatPos.x * 0.45,
        p.corePos.y * floatFactor + p.floatPos.y * 0.45,
        p.corePos.z * floatFactor + p.floatPos.z * 0.45
      );
    }

    // Fluid energy wave undulation (Matching bg-video.mp4 energy streams)
    if (!isReducedMotion && phase !== 13) {
      const waveY = Math.sin(time * 1.8 + idx * 0.15) * 0.12;
      const waveZ = Math.cos(time * 1.4 + idx * 0.10) * 0.12;
      p.targetPos.y += waveY;
      p.targetPos.z += waveZ;
    }

    // Interactive mouse parallax drift (disabled if reduced motion)
    if (!isReducedMotion) {
      const depthMultiplier = p.layer === 'fg' ? 1.8 : (p.layer === 'bg' ? 0.3 : 1.0);
      p.targetPos.x += mouseX * 1.2 * depthMultiplier;
      p.targetPos.y += mouseY * 1.2 * depthMultiplier;
    }

    // Smooth position interpolation (LERP)
    const lerpSpeed = isReducedMotion ? 0.03 : p.speed;
    p.pos.x += (p.targetPos.x - p.pos.x) * lerpSpeed;
    p.pos.y += (p.targetPos.y - p.pos.y) * lerpSpeed;
    p.pos.z += (p.targetPos.z - p.pos.z) * lerpSpeed;
  });
}

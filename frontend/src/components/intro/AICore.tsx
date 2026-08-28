import * as THREE from 'three';

// ─── Programmatic Circular Texture Generator (Eliminates WebGL Square Points) ─
function createCircleTexture(): THREE.Texture {
  const canvas = document.createElement('canvas');
  canvas.width = 32;
  canvas.height = 32;
  const ctx = canvas.getContext('2d')!;
  const grad = ctx.createRadialGradient(16, 16, 0, 16, 16, 16);
  grad.addColorStop(0, 'rgba(255, 255, 255, 1)');
  grad.addColorStop(0.3, 'rgba(255, 255, 255, 0.8)');
  grad.addColorStop(0.7, 'rgba(255, 255, 255, 0.2)');
  grad.addColorStop(1, 'rgba(255, 255, 255, 0)');
  ctx.fillStyle = grad;
  ctx.fillRect(0, 0, 32, 32);
  const texture = new THREE.CanvasTexture(canvas);
  return texture;
}

// Shared circle texture instance
const circleTexture = typeof document !== 'undefined' ? createCircleTexture() : null;

// ─── 3D Cluster Coordinates for AIDA Brain Structure ────────────────────────
const CLUSTER_CENTERS: Record<string, THREE.Vector3> = {
  INPUT: new THREE.Vector3(-2.2, 1.6, 1.2),
  CONTEXT: new THREE.Vector3(-1.2, 0.4, 1.8),
  WORKING_MEMORY: new THREE.Vector3(-0.6, 1.8, -1.6),
  LONG_TERM_MEMORY: new THREE.Vector3(-2.0, 0.4, -2.2),
  KNOWLEDGE: new THREE.Vector3(2.2, 1.4, -1.5),
  REASONING: new THREE.Vector3(0.6, 2.0, 1.0),
  TOOLS: new THREE.Vector3(2.2, -0.6, 1.6),
  USER_CONTEXT: new THREE.Vector3(-1.8, -1.0, -1.5),
  VERIFICATION: new THREE.Vector3(1.5, -1.6, 1.0),
  RESPONSE: new THREE.Vector3(0.0, -2.0, 0.0),
};

const CLUSTER_COLORS: Record<string, number> = {
  INPUT: 0x5DE8FF,            // Electric Cyan
  CONTEXT: 0x8B5CF6,          // Ultraviolet
  WORKING_MEMORY: 0xEC4899,   // Neon Magenta
  LONG_TERM_MEMORY: 0x8B5CF6, // Ultraviolet
  KNOWLEDGE: 0x5DE8FF,        // Electric Cyan
  REASONING: 0xEC4899,        // Neon Magenta
  TOOLS: 0x8B5CF6,            // Ultraviolet
  USER_CONTEXT: 0xEC4899,     // Neon Magenta
  VERIFICATION: 0x5DE8FF,     // Electric Cyan
  RESPONSE: 0xFFFFFF,         // White
};

interface BrainNode3D {
  position: THREE.Vector3;
  localOffset: THREE.Vector3;
  cluster: string;
  color: THREE.Color;
  tier: 'micro' | 'processing' | 'core';
  size: number;
  baseBrightness: number;
  currentBrightness: number;
}

interface Signal3D {
  position: THREE.Vector3;
  path: THREE.Vector3[];
  pathProgress: number;
  speed: number;
  color: THREE.Color;
  active: boolean;
}

export class AICoreScene {
  group: THREE.Group;
  brainGroup: THREE.Group; // Independent 3D rotation group
  
  // Three.js meshes and particle systems
  microNodesGeometry: THREE.BufferGeometry;
  microNodesPoints: THREE.Points;

  processingNodesGeometry: THREE.BufferGeometry;
  processingNodesPoints: THREE.Points;

  coreNodesGeometry: THREE.BufferGeometry;
  coreNodesPoints: THREE.Points;

  curvedArcsGeometry: THREE.BufferGeometry;
  curvedArcsSegments: THREE.LineSegments;
  
  signalsGeometry: THREE.BufferGeometry;
  signalsPoints: THREE.Points;

  vectorGeometry: THREE.BufferGeometry;
  vectorPoints: THREE.Points;

  // Central Core Mesh Sphere
  coreSphere: THREE.Mesh;
  innerCore: THREE.Mesh;
  glowMesh: THREE.Mesh;
  shockwaveRing: THREE.Mesh;
  coreRings: THREE.LineLoop[] = [];

  // Internal State
  nodes: BrainNode3D[] = [];
  arcPoints: { p0: THREE.Vector3; p1: THREE.Vector3; p2: THREE.Vector3; colorA: THREE.Color; colorB: THREE.Color; tier: 'primary' | 'secondary' | 'background' }[] = [];
  signals: Signal3D[] = [];
  vectorNodes: { pos: THREE.Vector3; brightness: number }[] = [];
  
  currentMemoryScale = 1.0;
  pulseTime = 0;
  ultraIntensity = 0.0;
  isMobile = false;

  constructor() {
    this.group = new THREE.Group();
    this.brainGroup = new THREE.Group();
    this.group.add(this.brainGroup);
    this.group.visible = false;

    this.isMobile = typeof window !== 'undefined' && window.innerWidth < 768;

    // ─── 1. Tier 1: Micro Nodes (Dense ambient matrix, small circular points)
    const microCount = this.isMobile ? 400 : 1200;
    this.microNodesGeometry = new THREE.BufferGeometry();
    const microPositions = new Float32Array(microCount * 3);
    const microColors = new Float32Array(microCount * 3);

    for (let i = 0; i < microCount; i++) {
      const r = Math.pow(Math.random(), 0.6) * 3.2;
      const theta = Math.random() * Math.PI * 2;
      const phi = Math.acos(Math.random() * 2 - 1);

      const x = r * Math.sin(phi) * Math.cos(theta);
      const y = r * Math.sin(phi) * Math.sin(theta);
      const z = r * Math.cos(phi);

      microPositions[i * 3] = x;
      microPositions[i * 3 + 1] = y;
      microPositions[i * 3 + 2] = z;

      const color = new THREE.Color();
      const randType = Math.random();
      if (randType < 0.50) color.setHex(0x4C7DFF);      // Blue
      else if (randType < 0.80) color.setHex(0x5DE8FF); // Cyan
      else if (randType < 0.95) color.setHex(0x7C5CFF); // Violet
      else color.setHex(0xFFFFFF);                      // White highlight (5%)

      const baseB = 0.18 + Math.random() * 0.15;
      microColors[i * 3] = color.r * baseB;
      microColors[i * 3 + 1] = color.g * baseB;
      microColors[i * 3 + 2] = color.b * baseB;

      this.nodes.push({
        position: new THREE.Vector3(x, y, z),
        localOffset: new THREE.Vector3(x, y, z),
        cluster: 'ambient',
        color,
        tier: 'micro',
        size: 0.10 + Math.random() * 0.08,
        baseBrightness: baseB,
        currentBrightness: baseB,
      });
    }

    this.microNodesGeometry.setAttribute('position', new THREE.BufferAttribute(microPositions, 3));
    this.microNodesGeometry.setAttribute('color', new THREE.BufferAttribute(microColors, 3));

    const microMaterial = new THREE.PointsMaterial({
      size: this.isMobile ? 0.18 : 0.24,
      vertexColors: true,
      map: circleTexture,
      transparent: true,
      opacity: 0.60,
      blending: THREE.AdditiveBlending,
      depthWrite: false,
    });
    this.microNodesPoints = new THREE.Points(this.microNodesGeometry, microMaterial);
    this.brainGroup.add(this.microNodesPoints);

    // ─── 2. Tier 2: Processing Nodes (Cluster nodes, circular soft glow) ──────
    const nodesPerCluster = 25;
    const clusterKeys = Object.keys(CLUSTER_CENTERS);

    clusterKeys.forEach((clusterName) => {
      const center = CLUSTER_CENTERS[clusterName];
      const baseColor = new THREE.Color(CLUSTER_COLORS[clusterName]);

      for (let i = 0; i < nodesPerCluster; i++) {
        const r = 0.12 + Math.random() * 0.38;
        const theta = Math.random() * Math.PI * 2;
        const phi = Math.acos(Math.random() * 2 - 1);

        const localOffset = new THREE.Vector3(
          r * Math.sin(phi) * Math.cos(theta),
          r * Math.sin(phi) * Math.sin(theta),
          r * Math.cos(phi)
        );

        const baseB = 0.5 + Math.random() * 0.2;
        this.nodes.push({
          position: center.clone().add(localOffset),
          localOffset,
          cluster: clusterName,
          color: baseColor.clone(),
          tier: 'processing',
          size: 0.24 + Math.random() * 0.12,
          baseBrightness: baseB,
          currentBrightness: baseB,
        });
      }
    });

    const procCount = clusterKeys.length * nodesPerCluster;
    this.processingNodesGeometry = new THREE.BufferGeometry();
    const procPositions = new Float32Array(procCount * 3);
    const procColors = new Float32Array(procCount * 3);

    this.nodes.filter(n => n.tier === 'processing').forEach((n, idx) => {
      procPositions[idx * 3] = n.position.x;
      procPositions[idx * 3 + 1] = n.position.y;
      procPositions[idx * 3 + 2] = n.position.z;

      procColors[idx * 3] = n.color.r * n.baseBrightness;
      procColors[idx * 3 + 1] = n.color.g * n.baseBrightness;
      procColors[idx * 3 + 2] = n.color.b * n.baseBrightness;
    });

    this.processingNodesGeometry.setAttribute('position', new THREE.BufferAttribute(procPositions, 3));
    this.processingNodesGeometry.setAttribute('color', new THREE.BufferAttribute(procColors, 3));

    const procMaterial = new THREE.PointsMaterial({
      size: 0.38,
      vertexColors: true,
      map: circleTexture,
      transparent: true,
      opacity: 0.85,
      blending: THREE.AdditiveBlending,
      depthWrite: false,
    });
    this.processingNodesPoints = new THREE.Points(this.processingNodesGeometry, procMaterial);
    this.brainGroup.add(this.processingNodesPoints);

    // ─── 3. Tier 3: Core Nodes (12 Major High-Glow Hubs) ────────────────────
    const coreCount = 12;
    this.coreNodesGeometry = new THREE.BufferGeometry();
    const corePositions = new Float32Array(coreCount * 3);
    const coreColors = new Float32Array(coreCount * 3);

    for (let i = 0; i < coreCount; i++) {
      const angle = (i / coreCount) * Math.PI * 2;
      const radius = 1.1 + (i % 3) * 0.35;
      const height = ((i % 4) - 1.5) * 0.5;

      const pos = new THREE.Vector3(
        Math.cos(angle) * radius,
        height,
        Math.sin(angle) * radius
      );

      this.nodes.push({
        position: pos,
        localOffset: pos.clone(),
        cluster: 'core_hub',
        color: new THREE.Color(0x5DE8FF),
        tier: 'core',
        size: 0.55,
        baseBrightness: 0.9,
        currentBrightness: 0.9,
      });

      corePositions[i * 3] = pos.x;
      corePositions[i * 3 + 1] = pos.y;
      corePositions[i * 3 + 2] = pos.z;

      coreColors[i * 3] = 0.9;
      coreColors[i * 3 + 1] = 0.9;
      coreColors[i * 3 + 2] = 0.9;
    }

    this.coreNodesGeometry.setAttribute('position', new THREE.BufferAttribute(corePositions, 3));
    this.coreNodesGeometry.setAttribute('color', new THREE.BufferAttribute(coreColors, 3));

    const coreNodesMaterial = new THREE.PointsMaterial({
      size: 0.58,
      vertexColors: true,
      map: circleTexture,
      transparent: true,
      opacity: 0.95,
      blending: THREE.AdditiveBlending,
      depthWrite: false,
    });
    this.coreNodesPoints = new THREE.Points(this.coreNodesGeometry, coreNodesMaterial);
    this.brainGroup.add(this.coreNodesPoints);

    // ─── 4. Connection Opacity Tiers & Curved Pathways ──────────────────────
    const arcCount = this.isMobile ? 50 : 120;
    const samplesPerArc = 10;
    const lineVerticesCount = arcCount * (samplesPerArc - 1) * 2;

    const linePositions = new Float32Array(lineVerticesCount * 3);
    const lineColors = new Float32Array(lineVerticesCount * 3);

    const clusterNames = Object.keys(CLUSTER_CENTERS);
    for (let i = 0; i < arcCount; i++) {
      const nameA = clusterNames[i % clusterNames.length];
      const nameB = clusterNames[(i + 2 + (i % 3)) % clusterNames.length];

      const p0 = CLUSTER_CENTERS[nameA].clone().add(new THREE.Vector3((Math.random() - 0.5) * 0.6, (Math.random() - 0.5) * 0.6, (Math.random() - 0.5) * 0.6));
      const p2 = CLUSTER_CENTERS[nameB].clone().add(new THREE.Vector3((Math.random() - 0.5) * 0.6, (Math.random() - 0.5) * 0.6, (Math.random() - 0.5) * 0.6));

      const mid = new THREE.Vector3().addVectors(p0, p2).multiplyScalar(0.5);
      const outwardDir = mid.clone().normalize();
      const curveHeight = 0.8 + Math.random() * 1.8;
      const p1 = mid.add(outwardDir.multiplyScalar(curveHeight));

      const colorA = new THREE.Color(CLUSTER_COLORS[nameA]);
      const colorB = new THREE.Color(CLUSTER_COLORS[nameB]);

      let tier: 'primary' | 'secondary' | 'background' = 'secondary';
      const randTier = Math.random();
      if (randTier < 0.20) tier = 'primary';
      else if (randTier > 0.65) tier = 'background';

      this.arcPoints.push({ p0, p1, p2, colorA, colorB, tier });
    }

    let vertexIdx = 0;
    this.arcPoints.forEach((arc) => {
      const curve = new THREE.QuadraticBezierCurve3(arc.p0, arc.p1, arc.p2);
      const points = curve.getPoints(samplesPerArc - 1);

      const baseOpacity = arc.tier === 'primary' ? 0.65 : (arc.tier === 'secondary' ? 0.30 : 0.12);

      for (let j = 0; j < points.length - 1; j++) {
        const ptA = points[j];
        const ptB = points[j + 1];
        const t = j / (points.length - 1);

        linePositions[vertexIdx * 3] = ptA.x;
        linePositions[vertexIdx * 3 + 1] = ptA.y;
        linePositions[vertexIdx * 3 + 2] = ptA.z;

        linePositions[(vertexIdx + 1) * 3] = ptB.x;
        linePositions[(vertexIdx + 1) * 3 + 1] = ptB.y;
        linePositions[(vertexIdx + 1) * 3 + 2] = ptB.z;

        const cSegment = new THREE.Color().lerpColors(arc.colorA, arc.colorB, t);

        lineColors[vertexIdx * 3] = cSegment.r * baseOpacity;
        lineColors[vertexIdx * 3 + 1] = cSegment.g * baseOpacity;
        lineColors[vertexIdx * 3 + 2] = cSegment.b * baseOpacity;

        lineColors[(vertexIdx + 1) * 3] = cSegment.r * baseOpacity;
        lineColors[(vertexIdx + 1) * 3 + 1] = cSegment.g * baseOpacity;
        lineColors[(vertexIdx + 1) * 3 + 2] = cSegment.b * baseOpacity;

        vertexIdx += 2;
      }
    });

    this.curvedArcsGeometry = new THREE.BufferGeometry();
    this.curvedArcsGeometry.setAttribute('position', new THREE.BufferAttribute(linePositions, 3));
    this.curvedArcsGeometry.setAttribute('color', new THREE.BufferAttribute(lineColors, 3));

    const curvedArcsMaterial = new THREE.LineBasicMaterial({
      vertexColors: true,
      transparent: true,
      opacity: 0.6,
      blending: THREE.AdditiveBlending,
      depthWrite: false,
    });
    this.curvedArcsSegments = new THREE.LineSegments(this.curvedArcsGeometry, curvedArcsMaterial);
    this.brainGroup.add(this.curvedArcsSegments);

    // ─── 5. Vector Index Field (Knowledge cluster) ──────────────────────────
    const knowledgeCenter = CLUSTER_CENTERS['KNOWLEDGE'];
    const vectorCount = 80;
    this.vectorGeometry = new THREE.BufferGeometry();
    const vectorPositions = new Float32Array(vectorCount * 3);
    const vectorColors = new Float32Array(vectorCount * 3);

    for (let i = 0; i < vectorCount; i++) {
      const r = 0.2 + Math.random() * 0.75;
      const theta = Math.random() * Math.PI * 2;
      const phi = Math.acos(Math.random() * 2 - 1);

      const pos = new THREE.Vector3(
        knowledgeCenter.x + r * Math.sin(phi) * Math.cos(theta),
        knowledgeCenter.y + r * Math.sin(phi) * Math.sin(theta),
        knowledgeCenter.z + r * Math.cos(phi)
      );

      this.vectorNodes.push({ pos, brightness: 0.15 });

      vectorPositions[i * 3] = pos.x;
      vectorPositions[i * 3 + 1] = pos.y;
      vectorPositions[i * 3 + 2] = pos.z;

      vectorColors[i * 3] = 0.2;
      vectorColors[i * 3 + 1] = 0.5;
      vectorColors[i * 3 + 2] = 0.8;
    }

    this.vectorGeometry.setAttribute('position', new THREE.BufferAttribute(vectorPositions, 3));
    this.vectorGeometry.setAttribute('color', new THREE.BufferAttribute(vectorColors, 3));

    const vectorMaterial = new THREE.PointsMaterial({
      size: 0.18,
      vertexColors: true,
      map: circleTexture,
      transparent: true,
      opacity: 0.65,
      blending: THREE.AdditiveBlending,
    });
    this.vectorPoints = new THREE.Points(this.vectorGeometry, vectorMaterial);
    this.brainGroup.add(this.vectorPoints);

    // ─── 6. Luminous Signal Particles Pool ──────────────────────────────────
    this.signalsGeometry = new THREE.BufferGeometry();
    const maxSignals = 30;
    const signalPositions = new Float32Array(maxSignals * 3);
    const signalColors = new Float32Array(maxSignals * 3);
    this.signalsGeometry.setAttribute('position', new THREE.BufferAttribute(signalPositions, 3));
    this.signalsGeometry.setAttribute('color', new THREE.BufferAttribute(signalColors, 3));

    const signalMaterial = new THREE.PointsMaterial({
      size: 0.42,
      vertexColors: true,
      map: circleTexture,
      transparent: true,
      opacity: 0.9,
      blending: THREE.AdditiveBlending,
    });
    this.signalsPoints = new THREE.Points(this.signalsGeometry, signalMaterial);
    this.brainGroup.add(this.signalsPoints);

    for (let i = 0; i < maxSignals; i++) {
      this.signals.push({
        position: new THREE.Vector3(),
        path: [],
        pathProgress: 0,
        speed: 0.018 + Math.random() * 0.02,
        color: new THREE.Color(0x5DE8FF),
        active: false,
      });
    }

    // ─── 7. Central Intelligence Core (Controlled Bloom, Clamp Overexposure) 
    const sphereGeo = new THREE.SphereGeometry(0.85, 20, 20);
    const sphereMat = new THREE.MeshBasicMaterial({
      color: 0x5DE8FF,
      transparent: true,
      opacity: 0.20,
      wireframe: true,
      blending: THREE.AdditiveBlending,
    });
    this.coreSphere = new THREE.Mesh(sphereGeo, sphereMat);
    this.brainGroup.add(this.coreSphere);

    // Inner Core (soft white, non-overexposed)
    const innerGeo = new THREE.SphereGeometry(0.30, 18, 18);
    const innerMat = new THREE.MeshBasicMaterial({
      color: 0xFFFFFF,
      transparent: true,
      opacity: 0.70,
      blending: THREE.AdditiveBlending,
    });
    this.innerCore = new THREE.Mesh(innerGeo, innerMat);
    this.brainGroup.add(this.innerCore);

    // Volumetric Glow (Violet/Cyan backdrop)
    const glowGeo = new THREE.SphereGeometry(1.5, 18, 18);
    const glowMat = new THREE.MeshBasicMaterial({
      color: 0x7C5CFF,
      transparent: true,
      opacity: 0.08,
      blending: THREE.AdditiveBlending,
    });
    this.glowMesh = new THREE.Mesh(glowGeo, glowMat);
    this.brainGroup.add(this.glowMesh);

    // Shockwave Energy Ring
    const shockGeo = new THREE.RingGeometry(0.4, 1.0, 32);
    const shockMat = new THREE.MeshBasicMaterial({
      color: 0x5DE8FF,
      transparent: true,
      opacity: 0.0,
      side: THREE.DoubleSide,
      blending: THREE.AdditiveBlending,
    });
    this.shockwaveRing = new THREE.Mesh(shockGeo, shockMat);
    this.shockwaveRing.rotation.x = Math.PI / 2;
    this.brainGroup.add(this.shockwaveRing);

    // Orbiting rings
    const createRing = (radius: number, color: number, angleX = 0, angleY = 0) => {
      const points = [];
      for (let i = 0; i <= 64; i++) {
        const theta = (i / 64) * Math.PI * 2;
        points.push(new THREE.Vector3(Math.cos(theta) * radius, Math.sin(theta) * radius, 0));
      }
      const geo = new THREE.BufferGeometry().setFromPoints(points);
      const mat = new THREE.LineBasicMaterial({
        color,
        transparent: true,
        opacity: 0.22,
        blending: THREE.AdditiveBlending,
      });
      const ring = new THREE.LineLoop(geo, mat);
      ring.rotation.x = angleX;
      ring.rotation.y = angleY;
      return ring;
    };

    this.coreRings.push(createRing(1.7, 0x5DE8FF, Math.PI / 3, 0));
    this.coreRings.push(createRing(2.1, 0x4C7DFF, -Math.PI / 4, Math.PI / 6));
    this.coreRings.push(createRing(1.5, 0x7C5CFF, Math.PI / 2.5, -Math.PI / 4));

    this.coreRings.forEach(r => this.brainGroup.add(r));
  }

  // Trigger signal along curved Bezier path
  triggerSignal(fromCluster: string, toCluster: string, colorHex: number) {
    const inactiveSig = this.signals.find(s => !s.active);
    if (inactiveSig) {
      const centerA = CLUSTER_CENTERS[fromCluster];
      const centerB = CLUSTER_CENTERS[toCluster];
      const mid = new THREE.Vector3().addVectors(centerA, centerB).multiplyScalar(0.5);
      const outward = mid.clone().normalize().multiplyScalar(1.0);

      inactiveSig.path = [centerA, mid.add(outward), centerB];
      inactiveSig.pathProgress = 0;
      inactiveSig.color.setHex(colorHex);
      inactiveSig.active = true;
    }
  }

  update(time: number, phase: number) {
    this.group.visible = phase >= 4 && phase <= 13;
    if (!this.group.visible) return;

    this.pulseTime += 0.02;

    // ─── 1. Independent 3D Brain Core Rotation ──────────────────────────────
    const rotationSpeed = 0.035 + Math.sin(time * 0.12) * 0.015;
    this.brainGroup.rotation.y = time * rotationSpeed;
    this.brainGroup.rotation.x = Math.sin(time * 0.05) * 0.10;

    // ─── 2. ULTRA INTELLIGENCE Mode Trigger ───
    const isUltraMode = phase === 10 || phase === 11;
    this.ultraIntensity = THREE.MathUtils.lerp(this.ultraIntensity, isUltraMode ? 1.0 : 0.0, 0.04);

    if (isUltraMode) {
      const wave = (time * 1.2) % 1;
      this.shockwaveRing.scale.setScalar(1.0 + wave * 3.5);
      (this.shockwaveRing.material as THREE.MeshBasicMaterial).opacity = (1.0 - wave) * 0.45;
    } else {
      (this.shockwaveRing.material as THREE.MeshBasicMaterial).opacity = 0.0;
    }

    // ─── 3. Memory Expansion Scaling ───
    let targetMemScale = 1.0;
    if (phase === 5) {
      targetMemScale = 2.0;
    }
    this.currentMemoryScale = THREE.MathUtils.lerp(this.currentMemoryScale, targetMemScale, 0.05);

    // Update Processing Node Positions & Colors
    const procPosAttr = this.processingNodesGeometry.getAttribute('position') as THREE.BufferAttribute;
    const procColAttr = this.processingNodesGeometry.getAttribute('color') as THREE.BufferAttribute;
    const procPosArr = procPosAttr.array as Float32Array;
    const procColArr = procColAttr.array as Float32Array;

    const procNodes = this.nodes.filter(n => n.tier === 'processing');
    procNodes.forEach((node, idx) => {
      const center = CLUSTER_CENTERS[node.cluster];
      let scale = 1.0;

      if (node.cluster.includes('MEMORY') || node.cluster === 'USER_CONTEXT' || node.cluster === 'KNOWLEDGE') {
        scale = this.currentMemoryScale;
      }

      node.position.copy(center).addScaledVector(node.localOffset, scale);
      procPosArr[idx * 3] = node.position.x;
      procPosArr[idx * 3 + 1] = node.position.y;
      procPosArr[idx * 3 + 2] = node.position.z;

      let targetB = node.baseBrightness;
      if (phase === 5 && (node.cluster.includes('MEMORY') || node.cluster === 'USER_CONTEXT')) targetB = 0.90;
      if (phase === 6 && (node.cluster === 'KNOWLEDGE' || node.cluster === 'INPUT')) targetB = 0.90;
      if (phase === 7 && node.cluster === 'REASONING') targetB = 0.90;
      if (phase === 8 && node.cluster === 'TOOLS') targetB = 0.90;
      if (phase === 9 && node.cluster === 'VERIFICATION') targetB = 0.90;
      if (phase >= 10 && (node.cluster === 'RESPONSE' || node.cluster === 'core')) targetB = 0.95;

      node.currentBrightness = THREE.MathUtils.lerp(node.currentBrightness, targetB, 0.05);

      const pulse = 0.88 + 0.12 * Math.sin(this.pulseTime * 3.5 + idx);
      procColArr[idx * 3] = node.color.r * node.currentBrightness * pulse;
      procColArr[idx * 3 + 1] = node.color.g * node.currentBrightness * pulse;
      procColArr[idx * 3 + 2] = node.color.b * node.currentBrightness * pulse;
    });
    procPosAttr.needsUpdate = true;
    procColAttr.needsUpdate = true;

    // ─── 4. Update Micro Nodes ───
    const microColAttr = this.microNodesGeometry.getAttribute('color') as THREE.BufferAttribute;
    const microColArr = microColAttr.array as Float32Array;

    const microNodes = this.nodes.filter(n => n.tier === 'micro');
    microNodes.forEach((node, idx) => {
      const pulse = 0.75 + 0.25 * Math.sin(this.pulseTime * 2.0 + idx * 0.1);
      const b = node.baseBrightness + this.ultraIntensity * 0.25;

      microColArr[idx * 3] = node.color.r * b * pulse;
      microColArr[idx * 3 + 1] = node.color.g * b * pulse;
      microColArr[idx * 3 + 2] = node.color.b * b * pulse;
    });
    microColAttr.needsUpdate = true;

    // ─── 5. Update Curved Arc Pathways Opacities ───
    const arcColAttr = this.curvedArcsGeometry.getAttribute('color') as THREE.BufferAttribute;
    const arcColArr = arcColAttr.array as Float32Array;
    let vIdx = 0;

    this.arcPoints.forEach((arc) => {
      const samples = 10;
      const baseOpacity = arc.tier === 'primary' ? 0.65 : (arc.tier === 'secondary' ? 0.30 : 0.12);

      for (let j = 0; j < samples - 1; j++) {
        const t = j / (samples - 1);
        const cSegment = new THREE.Color().lerpColors(arc.colorA, arc.colorB, t);
        const brightness = baseOpacity + this.ultraIntensity * 0.25 + Math.sin(time * 2.5 + j * 0.4) * 0.08;

        arcColArr[vIdx * 3] = cSegment.r * brightness;
        arcColArr[vIdx * 3 + 1] = cSegment.g * brightness;
        arcColArr[vIdx * 3 + 2] = cSegment.b * brightness;

        arcColArr[(vIdx + 1) * 3] = cSegment.r * brightness;
        arcColArr[(vIdx + 1) * 3 + 1] = cSegment.g * brightness;
        arcColArr[(vIdx + 1) * 3 + 2] = cSegment.b * brightness;

        vIdx += 2;
      }
    });
    arcColAttr.needsUpdate = true;

    // ─── 6. Vector Index Search Field ───
    const vecColAttr = this.vectorGeometry.getAttribute('color') as THREE.BufferAttribute;
    const vecColArr = vecColAttr.array as Float32Array;

    this.vectorNodes.forEach((node, i) => {
      let targetB = 0.12;
      if (phase === 6) {
        targetB = 0.25 + 0.65 * Math.sin(time * 3.5 + i * 0.15);
      }
      node.brightness = THREE.MathUtils.lerp(node.brightness, Math.max(0.12, targetB), 0.05);

      vecColArr[i * 3] = (phase === 6 ? 0.36 : 0.15) * node.brightness;
      vecColArr[i * 3 + 1] = (phase === 6 ? 0.91 : 0.45) * node.brightness;
      vecColArr[i * 3 + 2] = (phase === 6 ? 1.0 : 0.8) * node.brightness;
    });
    vecColAttr.needsUpdate = true;

    // ─── 7. Sequential Signal Cascades ───
    const signalChance = isUltraMode ? 0.35 : 0.15;
    if (Math.random() < signalChance) {
      if (phase === 5) {
        this.triggerSignal('WORKING_MEMORY', 'LONG_TERM_MEMORY', 0x7C5CFF);
        this.triggerSignal('USER_CONTEXT', 'WORKING_MEMORY', 0xA78BFA);
      } else if (phase === 6) {
        this.triggerSignal('INPUT', 'CONTEXT', 0x5DE8FF);
        this.triggerSignal('CONTEXT', 'KNOWLEDGE', 0x4C7DFF);
      } else if (phase === 7) {
        this.triggerSignal('WORKING_MEMORY', 'REASONING', 0x7C5CFF);
        this.triggerSignal('REASONING', 'VERIFICATION', 0xA78BFA);
      } else if (phase === 8) {
        this.triggerSignal('REASONING', 'TOOLS', 0xA78BFA);
        this.triggerSignal('TOOLS', 'WORKING_MEMORY', 0x7C5CFF);
      } else if (phase === 9) {
        this.triggerSignal('VERIFICATION', 'RESPONSE', 0x5DE8FF);
        this.triggerSignal('RESPONSE', 'VERIFICATION', 0xFFFFFF);
      } else if (phase >= 10) {
        const clusters = Object.keys(CLUSTER_CENTERS);
        const randCluster = clusters[Math.floor(Math.random() * clusters.length)];
        this.triggerSignal(randCluster, 'RESPONSE', 0xFFFFFF);
      }
    }

    const sigPosAttr = this.signalsGeometry.getAttribute('position') as THREE.BufferAttribute;
    const sigColAttr = this.signalsGeometry.getAttribute('color') as THREE.BufferAttribute;
    const sigPosArr = sigPosAttr.array as Float32Array;
    const sigColArr = sigColAttr.array as Float32Array;

    this.signals.forEach((sig, idx) => {
      if (!sig.active) {
        sigPosArr[idx * 3] = 9999;
        sigPosArr[idx * 3 + 1] = 9999;
        sigPosArr[idx * 3 + 2] = 9999;
        return;
      }

      sig.pathProgress += sig.speed * (isUltraMode ? 1.5 : 1.0);
      if (sig.pathProgress >= 1) {
        sig.active = false;
        return;
      }

      const p = sig.pathProgress;
      const p0 = sig.path[0];
      const p1 = sig.path[1];
      const p2 = sig.path[2];

      const x = (1 - p) * (1 - p) * p0.x + 2 * (1 - p) * p * p1.x + p * p * p2.x;
      const y = (1 - p) * (1 - p) * p0.y + 2 * (1 - p) * p * p1.y + p * p * p2.y;
      const z = (1 - p) * (1 - p) * p0.z + 2 * (1 - p) * p * p1.z + p * p * p2.z;

      sig.position.set(x, y, z);

      sigPosArr[idx * 3] = sig.position.x;
      sigPosArr[idx * 3 + 1] = sig.position.y;
      sigPosArr[idx * 3 + 2] = sig.position.z;

      sigColArr[idx * 3] = sig.color.r * 0.9;
      sigColArr[idx * 3 + 1] = sig.color.g * 0.9;
      sigColArr[idx * 3 + 2] = sig.color.b * 0.9;
    });
    sigPosAttr.needsUpdate = true;
    sigColAttr.needsUpdate = true;

    // ─── 8. Central Core Controlled Energy & Rotation ───
    const energyFactor = 1.0 + Math.sin(time * 3.5) * (isUltraMode ? 0.18 : 0.06);
    this.coreSphere.rotation.y = time * 0.35;
    this.coreSphere.rotation.x = time * 0.18;
    this.innerCore.scale.setScalar(energyFactor * (isUltraMode ? 1.4 : 1.0));

    this.coreRings.forEach((ring, idx) => {
      const dir = idx % 2 === 0 ? 1 : -1;
      ring.rotation.z = time * 0.5 * dir;
    });

    const scale = 1.0 + Math.cos(time * 2.0) * 0.08;
    this.glowMesh.scale.set(scale, scale, scale);

    if (phase >= 11) {
      const approachScale = 1.0 + (phase - 11) * 0.45;
      this.brainGroup.scale.setScalar(approachScale);
    } else {
      this.brainGroup.scale.setScalar(1.0);
    }
  }

  destroy() {
    this.microNodesGeometry.dispose();
    (this.microNodesPoints.material as THREE.Material).dispose();

    this.processingNodesGeometry.dispose();
    (this.processingNodesPoints.material as THREE.Material).dispose();

    this.coreNodesGeometry.dispose();
    (this.coreNodesPoints.material as THREE.Material).dispose();

    this.curvedArcsGeometry.dispose();
    (this.curvedArcsSegments.material as THREE.Material).dispose();

    this.vectorGeometry.dispose();
    (this.vectorPoints.material as THREE.Material).dispose();

    this.signalsGeometry.dispose();
    (this.signalsPoints.material as THREE.Material).dispose();

    this.coreSphere.geometry.dispose();
    (this.coreSphere.material as THREE.Material).dispose();

    this.innerCore.geometry.dispose();
    (this.innerCore.material as THREE.Material).dispose();

    this.glowMesh.geometry.dispose();
    (this.glowMesh.material as THREE.Material).dispose();

    this.shockwaveRing.geometry.dispose();
    (this.shockwaveRing.material as THREE.MeshBasicMaterial).dispose();

    this.coreRings.forEach((ring) => {
      ring.geometry.dispose();
      (ring.material as THREE.Material).dispose();
    });
  }
}

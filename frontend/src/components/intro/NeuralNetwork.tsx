import * as THREE from 'three';
import { ParticleData } from './IntroParticles';

export class NeuralNetworkLines {
  geometry: THREE.BufferGeometry;
  material: THREE.LineBasicMaterial;
  lineMesh: THREE.LineSegments;
  maxConnections: number;

  constructor(maxConnections = 450) {
    this.maxConnections = maxConnections;
    this.geometry = new THREE.BufferGeometry();

    const positions = new Float32Array(maxConnections * 2 * 3);
    const colors = new Float32Array(maxConnections * 2 * 3);

    this.geometry.setAttribute('position', new THREE.BufferAttribute(positions, 3));
    this.geometry.setAttribute('color', new THREE.BufferAttribute(colors, 3));

    this.material = new THREE.LineBasicMaterial({
      vertexColors: true,
      transparent: true,
      blending: THREE.AdditiveBlending,
      linewidth: 1,
      depthWrite: false
    });

    this.lineMesh = new THREE.LineSegments(this.geometry, this.material);
  }

  update(particles: ParticleData[], phase: number, time: number) {
    const posAttr = this.geometry.getAttribute('position') as THREE.BufferAttribute;
    const colAttr = this.geometry.getAttribute('color') as THREE.BufferAttribute;
    const positions = posAttr.array as Float32Array;
    const colors = colAttr.array as Float32Array;

    let lineCount = 0;
    const limit = Math.min(particles.length, 320);
    
    let maxDist = 2.4;
    let baseOpacity = 0.45;

    if (phase === 0) {
      maxDist = 2.0;
    } else if (phase === 1) {
      maxDist = 1.05; // sharp 3D constellation connections for A I D A
      baseOpacity = 0.35;
    } else if (phase === 2) {
      maxDist = 2.2;
    } else if (phase === 3) {
      maxDist = 2.8; // expanded active neural system
      baseOpacity = 0.6;
    } else if (phase === 4) {
      maxDist = 1.15; // sphere mesh connections
      baseOpacity = 0.5;
    } else if (phase >= 5 && phase <= 11) {
      // Brain phases: subtle ambient connections
      maxDist = 1.6;
      baseOpacity = 0.35;
    } else if (phase === 12) {
      maxDist = 1.0;
      baseOpacity = 0.4;
    } else if (phase === 13) {
      maxDist = 0.0; // disappear during final transition
    }

    if (maxDist > 0) {
      for (let i = 0; i < limit; i++) {
        const p1 = particles[i];
        if (p1.layer === 'bg') continue; // only connect midground/foreground nodes

        for (let j = i + 1; j < limit; j++) {
          if (lineCount >= this.maxConnections) break;

          const p2 = particles[j];
          if (p2.layer === 'bg') continue;

          const dx = p1.pos.x - p2.pos.x;
          const dy = p1.pos.y - p2.pos.y;
          const dz = p1.pos.z - p2.pos.z;
          const distSq = dx * dx + dy * dy + dz * dz;

          if (distSq < maxDist * maxDist) {
            const dist = Math.sqrt(distSq);
            
            // Dynamic data stream pulse effect travelling down lines
            const dataPulse = Math.sin(time * 5.0 + i * 0.3) * 0.3 + 0.7;
            const alpha = (1 - dist / maxDist) * baseOpacity * dataPulse;

            const idx = lineCount * 6;

            // Vertex 1
            positions[idx] = p1.pos.x;
            positions[idx + 1] = p1.pos.y;
            positions[idx + 2] = p1.pos.z;

            colors[idx] = p1.color.r * alpha;
            colors[idx + 1] = p1.color.g * alpha;
            colors[idx + 2] = p1.color.b * alpha;

            // Vertex 2
            positions[idx + 3] = p2.pos.x;
            positions[idx + 4] = p2.pos.y;
            positions[idx + 5] = p2.pos.z;

            colors[idx + 3] = p2.color.r * alpha;
            colors[idx + 4] = p2.color.g * alpha;
            colors[idx + 5] = p2.color.b * alpha;

            lineCount++;
          }
        }
      }
    }

    this.geometry.setDrawRange(0, lineCount * 2);
    posAttr.needsUpdate = true;
    colAttr.needsUpdate = true;
  }

  destroy() {
    this.geometry.dispose();
    this.material.dispose();
  }
}

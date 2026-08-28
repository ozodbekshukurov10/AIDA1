import React, { useEffect, useRef } from 'react';
import * as THREE from 'three';
import { createParticles, updateParticles } from './IntroParticles';
import { NeuralNetworkLines } from './NeuralNetwork';
import { AICoreScene } from './AICore';
import { CinematicCameraController } from './CameraController';

interface IntroSceneProps {
  phase: number;
  time: number;
  isReducedMotion: boolean;
}

// Generate circular glow texture programmatically with soft halo for Depth of Field
function createCircleTexture(): THREE.Texture {
  const canvas = document.createElement('canvas');
  canvas.width = 32;
  canvas.height = 32;
  const ctx = canvas.getContext('2d')!;
  const grad = ctx.createRadialGradient(16, 16, 0, 16, 16, 16);
  grad.addColorStop(0, 'rgba(255, 255, 255, 1)');
  grad.addColorStop(0.25, 'rgba(255, 255, 255, 0.85)');
  grad.addColorStop(0.65, 'rgba(255, 255, 255, 0.25)');
  grad.addColorStop(1, 'rgba(255, 255, 255, 0)');
  ctx.fillStyle = grad;
  ctx.fillRect(0, 0, 32, 32);
  const texture = new THREE.CanvasTexture(canvas);
  return texture;
}

export default function IntroScene({ phase, time, isReducedMotion }: IntroSceneProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);

  const phaseRef = useRef(phase);
  const timeRef = useRef(time);
  const mouseRef = useRef({ x: 0, y: 0 });

  useEffect(() => {
    phaseRef.current = phase;
  }, [phase]);

  useEffect(() => {
    timeRef.current = time;
  }, [time]);

  useEffect(() => {
    const container = containerRef.current;
    const canvas = canvasRef.current;
    if (!container || !canvas) return;

    // 1. Scene Setup with Deep Fog
    const scene = new THREE.Scene();
    scene.fog = new THREE.FogExp2(0x03050a, 0.042);

    // 2. Camera Setup
    const camera = new THREE.PerspectiveCamera(
      45,
      container.clientWidth / container.clientHeight,
      0.1,
      100
    );
    const cameraController = new CinematicCameraController();

    // 3. Renderer Setup
    const renderer = new THREE.WebGLRenderer({
      canvas,
      antialias: true,
      alpha: true,
      powerPreference: "high-performance"
    });
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    renderer.setSize(container.clientWidth, container.clientHeight);

    // 4. Lighting System 2.0 (Dynamic 4-Light Rig — Synced to bg-video.mp4)
    const ambientLight = new THREE.AmbientLight(0xffffff, 0.20);
    scene.add(ambientLight);

    // Neon Magenta Core Point Light
    const magentaPointLight = new THREE.PointLight(0xEC4899, 1.8, 38);
    magentaPointLight.position.set(0, 0, 2);
    scene.add(magentaPointLight);

    // Electric Cyan Fill Light
    const cyanFillLight = new THREE.DirectionalLight(0x5DE8FF, 1.3);
    cyanFillLight.position.set(6, 8, -5);
    scene.add(cyanFillLight);

    // Ultraviolet Rim Light
    const violetRimLight = new THREE.DirectionalLight(0x8B5CF6, 1.1);
    violetRimLight.position.set(-6, -6, 5);
    scene.add(violetRimLight);

    // 5. Particle System 2.0 Setup (FG, MG, BG depth layers)
    const isMobile = window.innerWidth < 768;
    const particleCount = isMobile ? 300 : 1000;
    const particles = createParticles(particleCount);

    const particleGeometry = new THREE.BufferGeometry();
    const positions = new Float32Array(particleCount * 3);
    const colors = new Float32Array(particleCount * 3);

    particles.forEach((p, idx) => {
      positions[idx * 3] = p.pos.x;
      positions[idx * 3 + 1] = p.pos.y;
      positions[idx * 3 + 2] = p.pos.z;

      colors[idx * 3] = p.color.r;
      colors[idx * 3 + 1] = p.color.g;
      colors[idx * 3 + 2] = p.color.b;
    });

    particleGeometry.setAttribute('position', new THREE.BufferAttribute(positions, 3));
    particleGeometry.setAttribute('color', new THREE.BufferAttribute(colors, 3));

    const particleMaterial = new THREE.PointsMaterial({
      size: isMobile ? 0.3 : 0.48,
      vertexColors: true,
      map: createCircleTexture(),
      transparent: true,
      blending: THREE.AdditiveBlending,
      depthWrite: false
    });

    const particlePoints = new THREE.Points(particleGeometry, particleMaterial);
    scene.add(particlePoints);

    // 6. Neural Network Plexus
    const neuralNetwork = new NeuralNetworkLines(isMobile ? 180 : 450);
    scene.add(neuralNetwork.lineMesh);

    // 7. AI Core Scene
    const aiCore = new AICoreScene();
    scene.add(aiCore.group);

    // 8. Micro Details (Micro-grid coordinate plane)
    const gridHelper = new THREE.GridHelper(30, 20, 0x62E8FF, 0x07111F);
    gridHelper.position.y = -8;
    (gridHelper.material as THREE.Material).opacity = 0.06;
    (gridHelper.material as THREE.Material).transparent = true;
    scene.add(gridHelper);

    // 9. Event Listeners
    const handleResize = () => {
      if (!container) return;
      camera.aspect = container.clientWidth / container.clientHeight;
      camera.updateProjectionMatrix();
      renderer.setSize(container.clientWidth, container.clientHeight);
    };
    window.addEventListener('resize', handleResize);

    const handleMouseMove = (e: MouseEvent) => {
      mouseRef.current.x = (e.clientX / window.innerWidth) - 0.5;
      mouseRef.current.y = -(e.clientY / window.innerHeight) + 0.5;
    };
    window.addEventListener('mousemove', handleMouseMove);

    // 10. Animation Loop
    let animId: number;
    const clock = new THREE.Clock();

    const animate = () => {
      const delta = clock.getDelta();
      const elapsedTime = timeRef.current;
      const curPhase = phaseRef.current;

      // Dynamically interpolate light and fog colors based on the current phase
      let targetFogColor = 0x03050a;
      let targetCyanLight = 0x5de8ff;
      let targetRimLight = 0x4c7dff;
      let targetFillLight = 0x7c5cff;

      if (curPhase === 0) {
        // Scene 1: Black + Deep Navy
        targetFogColor = 0x03050a;
        targetCyanLight = 0x07101a; // very dim
        targetRimLight = 0x0b1830;
        targetFillLight = 0x03050a;
      } else if (curPhase === 1) {
        // Scene 2: Blue + Cyan
        targetFogColor = 0x03050a;
        targetCyanLight = 0x5de8ff;
        targetRimLight = 0x4c7dff;
        targetFillLight = 0x0b1830;
      } else if (curPhase === 2 || curPhase === 3) {
        // Scene 3: Cyan + Violet
        targetFogColor = 0x03050a;
        targetCyanLight = 0x5de8ff;
        targetRimLight = 0x7c5cff;
        targetFillLight = 0x7c5cff;
      } else if (curPhase === 4) {
        // Scene 4: Electric Blue + Purple + Cyan
        targetFogColor = 0x03050a;
        targetCyanLight = 0x5de8ff;
        targetRimLight = 0x4c7dff;
        targetFillLight = 0xa78bfa; // soft purple
      } else if (curPhase === 5) {
        // Phase 3 — Brain Emerge: Deep Cyan backdrop
        targetFogColor = 0x020609;
        targetCyanLight = 0x5de8ff;
        targetRimLight = 0x4c7dff;
        targetFillLight = 0x07101a;
      } else if (curPhase === 6) {
        // Phase 3 — Input/Context: Blue + Cyan
        targetFogColor = 0x03050a;
        targetCyanLight = 0x4c7dff;
        targetRimLight = 0x5de8ff;
        targetFillLight = 0x0b1830;
      } else if (curPhase === 7) {
        // Phase 3 — Reasoning: Violet dominant
        targetFogColor = 0x050310;
        targetCyanLight = 0x7c5cff;
        targetRimLight = 0xa78bfa;
        targetFillLight = 0x4c7dff;
      } else if (curPhase === 8) {
        // Phase 3 — Tools & Memory: Purple + Soft Violet
        targetFogColor = 0x060310;
        targetCyanLight = 0xa78bfa;
        targetRimLight = 0x7c5cff;
        targetFillLight = 0x4c7dff;
      } else if (curPhase === 9) {
        // Phase 3 — Verification: Cyan purification
        targetFogColor = 0x02080d;
        targetCyanLight = 0x5de8ff;
        targetRimLight = 0x4c7dff;
        targetFillLight = 0xa78bfa;
      } else if (curPhase === 10) {
        // Phase 3 — Brain Map overview: Full spectrum
        targetFogColor = 0x03050a;
        targetCyanLight = 0x5de8ff;
        targetRimLight = 0x7c5cff;
        targetFillLight = 0x4c7dff;
      } else if (curPhase === 11) {
        // Phase 3 — Final / Intelligence Loop: Deep Navy + Cyan
        targetFogColor = 0x02040a;
        targetCyanLight = 0x5de8ff;
        targetRimLight = 0x4c7dff;
        targetFillLight = 0x7c5cff;
      } else if (curPhase === 12) {
        // Product Reveal: Deep Navy + Violet + Blue
        targetFogColor = 0x07101a;
        targetCyanLight = 0x7c5cff; // violet
        targetRimLight = 0x4c7dff;
        targetFillLight = 0x0b1830;
      } else if (curPhase === 13) {
        // Final Hero Transition: Cyan -> Blue -> Violet
        targetFogColor = 0x03050a;
        targetCyanLight = 0x5de8ff;
        targetRimLight = 0x4c7dff;
        targetFillLight = 0x7c5cff;
      }

      // Smooth color transitions
      if (scene.fog) {
        (scene.fog as THREE.FogExp2).color.lerp(new THREE.Color(targetFogColor), 0.05);
      }
      magentaPointLight.color.lerp(new THREE.Color(targetCyanLight), 0.05);
      cyanFillLight.color.lerp(new THREE.Color(targetRimLight), 0.05);
      violetRimLight.color.lerp(new THREE.Color(targetFillLight), 0.05);

      // Animate Light Rig Intensity based on Phase
      if (curPhase >= 4 && curPhase <= 11) {
        magentaPointLight.intensity = THREE.MathUtils.lerp(magentaPointLight.intensity, 3.2, 0.05); // Ramp up core light
      } else {
        magentaPointLight.intensity = THREE.MathUtils.lerp(magentaPointLight.intensity, 1.8, 0.05);
      }
      magentaPointLight.position.x = Math.sin(elapsedTime * 0.4) * 2.0;

      // Update particle physics
      updateParticles(
        particles,
        curPhase,
        elapsedTime,
        mouseRef.current.x,
        mouseRef.current.y,
        isReducedMotion
      );

      // Write positions to buffer
      const posAttr = particleGeometry.getAttribute('position') as THREE.BufferAttribute;
      const posArr = posAttr.array as Float32Array;

      particles.forEach((p, idx) => {
        posArr[idx * 3] = p.pos.x;
        posArr[idx * 3 + 1] = p.pos.y;
        posArr[idx * 3 + 2] = p.pos.z;
      });
      posAttr.needsUpdate = true;

      // Update Plexus lines with active data streams
      neuralNetwork.update(particles, curPhase, elapsedTime);

      // Update AI Core 2.0
      aiCore.update(elapsedTime, curPhase);

      // Update Camera 2.0
      cameraController.update(
        camera,
        curPhase,
        elapsedTime,
        mouseRef.current.x,
        mouseRef.current.y,
        isReducedMotion
      );

      renderer.render(scene, camera);
      animId = requestAnimationFrame(animate);
    };

    animate();

    // 11. Memory Cleanup
    return () => {
      cancelAnimationFrame(animId);
      window.removeEventListener('resize', handleResize);
      window.removeEventListener('mousemove', handleMouseMove);

      particleGeometry.dispose();
      particleMaterial.dispose();
      neuralNetwork.destroy();
      aiCore.destroy();
      gridHelper.geometry.dispose();
      (gridHelper.material as THREE.Material).dispose();
      renderer.dispose();
    };
  }, [isReducedMotion]);

  return (
    <div ref={containerRef} className="absolute inset-0 w-full h-full bg-[#03050A]">
      <canvas ref={canvasRef} className="w-full h-full block" />
    </div>
  );
}

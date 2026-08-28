import React, { useEffect, useRef } from 'react';
import AIDALogo, { AIDALogoCore } from '../ui/AIDALogo';

export type CoreState = 'idle' | 'hover' | 'thinking' | 'processing' | 'response';

interface AICoreProps {
  state?: CoreState;
  className?: string;
}

interface SphereParticle {
  x: number; // 3D local coords
  y: number;
  z: number;
  radius: number;
  color: string;
  speedMultiplier: number;
}

export default function AICore({ state = 'idle', className = '' }: AICoreProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const hoverRef = useRef(false);
  const phaseRef = useRef(0);
  const particlesRef = useRef<SphereParticle[]>([]);
  const stateRef = useRef<CoreState>('idle');
  const shockwaveRef = useRef(0); // For response state explosion

  useEffect(() => {
    stateRef.current = state;
    if (state === 'response') {
      shockwaveRef.current = 1.0; // Start shockwave explosion trigger
    }
  }, [state]);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    let animId: number;

    const resize = () => {
      canvas.width = canvas.parentElement?.offsetWidth || 360;
      canvas.height = canvas.parentElement?.offsetHeight || 360;
    };
    resize();
    window.addEventListener('resize', resize);

    // Initialize 3D Sphere Particles
    const particleCount = 220;
    const initParticles = () => {
      const arr: SphereParticle[] = [];
      const sphereRadius = 75;
      
      for (let i = 0; i < particleCount; i++) {
        // Uniform distribution over 3D sphere surface (Archimedes' theorem)
        const theta = Math.random() * Math.PI * 2;
        const phi = Math.acos(Math.random() * 2 - 1);
        
        const x = sphereRadius * Math.sin(phi) * Math.cos(theta);
        const y = sphereRadius * Math.sin(phi) * Math.sin(theta);
        const z = sphereRadius * Math.cos(phi);

        // Core dynamic color layers
        let color = '#5DE8FF'; // Middle Cyan
        const rand = Math.random();
        if (rand < 0.35) {
          color = '#4C7DFF'; // 35% Electric Blue (outer)
        } else if (rand < 0.70) {
          color = '#5DE8FF'; // 35% Cyan (middle)
        } else if (rand < 0.92) {
          color = '#7C5CFF'; // 22% Violet (inner)
        } else {
          color = '#F5F7FF'; // 8% White highlight
        }

        arr.push({
          x,
          y,
          z,
          radius: 1.0 + Math.random() * 1.5,
          color,
          speedMultiplier: 0.8 + Math.random() * 0.5
        });
      }
      particlesRef.current = arr;
    };
    initParticles();

    const handleMouseEnter = () => { hoverRef.current = true; };
    const handleMouseLeave = () => { hoverRef.current = false; };
    canvas.addEventListener('mouseenter', handleMouseEnter);
    canvas.addEventListener('mouseleave', handleMouseLeave);

    // Camera perspective settings
    const focalLength = 300;
    const cx = canvas.width / 2;
    const cy = canvas.height / 2;

    const draw = () => {
      ctx.clearRect(0, 0, canvas.width, canvas.height);
      const curState = stateRef.current;
      const isHovered = hoverRef.current || curState === 'hover';
      
      // Determine speeds based on state
      let speed = 0.008;
      if (curState === 'thinking') speed = 0.045;
      if (curState === 'processing') speed = 0.03;
      if (isHovered && curState === 'idle') speed = 0.015;

      // 3D rotation angles
      const rotY = speed;
      const rotX = speed * 0.5;

      const cosY = Math.cos(rotY);
      const sinY = Math.sin(rotY);
      const cosX = Math.cos(rotX);
      const sinX = Math.sin(rotX);

      // Pulse scaling
      phaseRef.current += curState === 'thinking' ? 0.15 : 0.035;
      const pulse = 1.0 + Math.sin(phaseRef.current) * (curState === 'thinking' ? 0.08 : 0.04);

      // Slow and elegant color cycling in idle state: Cyan -> Blue -> Violet -> Blue -> Cyan
      const time = phaseRef.current * 0.05;
      const cycle = (Math.sin(time) + 1) / 2; // value between 0 and 1
      
      let cycleAuraColor = 'rgba(93, 232, 255, 0.15)'; // default Cyan
      let waveColor = '#5DE8FF';
      if (curState === 'idle') {
        if (cycle < 0.33) {
          cycleAuraColor = 'rgba(93, 232, 255, 0.15)'; // Cyan
          waveColor = '#5DE8FF';
        } else if (cycle < 0.66) {
          cycleAuraColor = 'rgba(76, 125, 255, 0.15)'; // Electric Blue
          waveColor = '#4C7DFF';
        } else {
          cycleAuraColor = 'rgba(124, 92, 255, 0.15)'; // Violet
          waveColor = '#7C5CFF';
        }
      }

      // Handle response explosion fade out
      if (shockwaveRef.current > 0) {
        shockwaveRef.current += 0.06;
        if (shockwaveRef.current > 3.0) shockwaveRef.current = 0;
      }

      // Draw Aura Glow behind Core
      const auraRadius = 110 * pulse;
      const radialGrad = ctx.createRadialGradient(cx, cy, 10, cx, cy, auraRadius);
      if (curState === 'thinking') {
        radialGrad.addColorStop(0, 'rgba(124, 92, 255, 0.25)'); // Violet thinking
        radialGrad.addColorStop(1, 'transparent');
      } else if (curState === 'processing') {
        radialGrad.addColorStop(0, 'rgba(93, 232, 255, 0.28)'); // Cyan processing
        radialGrad.addColorStop(1, 'transparent');
      } else if (isHovered) {
        radialGrad.addColorStop(0, 'rgba(93, 232, 255, 0.35)');
        radialGrad.addColorStop(1, 'transparent');
      } else {
        radialGrad.addColorStop(0, cycleAuraColor);
        radialGrad.addColorStop(1, 'transparent');
      }
      ctx.fillStyle = radialGrad;
      ctx.beginPath();
      ctx.arc(cx, cy, auraRadius, 0, Math.PI * 2);
      ctx.fill();

      // Render 3D Projected Particles
      const particles = particlesRef.current;
      
      // Sort by depth (z) to render back-to-front (depth buffering)
      particles.sort((a, b) => b.z - a.z);

      particles.forEach(p => {
        // Rotate local coordinates
        // Y-axis rotation
        let x1 = p.x * cosY - p.z * sinY;
        let z1 = p.x * sinY + p.z * cosY;
        
        // X-axis rotation
        let y1 = p.y * cosX - z1 * sinX;
        let z2 = p.y * sinX + z1 * cosX;

        p.x = x1;
        p.y = y1;
        p.z = z2;

        // Apply scale/pulse and explosion factor if shockwave is active
        let px = p.x * pulse;
        let py = p.y * pulse;
        let pz = p.z * pulse;

        if (shockwaveRef.current > 0) {
          const pushForce = Math.max(0.5, 3.0 - shockwaveRef.current);
          px *= shockwaveRef.current * pushForce;
          py *= shockwaveRef.current * pushForce;
        }

        // Perspective Projection calculation
        const scale = focalLength / (focalLength + pz + 180);
        const screenX = cx + px * scale;
        const screenY = cy + py * scale;

        // Depth alpha scaling
        const depthAlpha = (pz + 100) / 200;
        
        ctx.fillStyle = p.color;
        // Make it glow brighter in thinking / response states
        const stateAlpha = curState === 'thinking' ? 0.95 : (isHovered ? 0.85 : 0.6);
        ctx.globalAlpha = Math.max(0.15, depthAlpha * stateAlpha);
        
        ctx.beginPath();
        ctx.arc(screenX, screenY, p.radius * scale * 1.5, 0, Math.PI * 2);
        ctx.fill();
        ctx.globalAlpha = 1.0; // reset
      });

      // Connecting neural mesh lines inside sphere
      ctx.lineWidth = 0.45;
      for (let i = 0; i < particles.length; i += 6) {
        const p1 = particles[i];
        const scale1 = focalLength / (focalLength + p1.z * pulse + 180);
        const sX1 = cx + p1.x * pulse * scale1;
        const sY1 = cy + p1.y * pulse * scale1;

        for (let j = i + 1; j < i + 4; j++) {
          if (j >= particles.length) break;
          const p2 = particles[j];
          const scale2 = focalLength / (focalLength + p2.z * pulse + 180);
          const sX2 = cx + p2.x * pulse * scale2;
          const sY2 = cy + p2.y * pulse * scale2;

          const dx = sX1 - sX2;
          const dy = sY1 - sY2;
          const d = Math.sqrt(dx * dx + dy * dy);

          if (d < 54) {
            ctx.strokeStyle = curState === 'thinking' 
              ? `rgba(124, 92, 255, ${(1 - d / 54) * 0.28})` 
              : `rgba(93, 232, 255, ${(1 - d / 54) * 0.18})`;
            ctx.beginPath();
            ctx.moveTo(sX1, sY1);
            ctx.lineTo(sX2, sY2);
            ctx.stroke();
          }
        }
      }

      // Draw SVG/Math Data Waves during PROCESSING state
      if (curState === 'processing') {
        ctx.strokeStyle = '#5DE8FF';
        ctx.lineWidth = 1.2;
        ctx.beginPath();
        for (let x = cx - 75; x < cx + 75; x++) {
          const relativeX = (x - cx) / 75;
          // Sine wave wrapped in a gaussian envelope to keep it within the sphere boundary
          const y = cy + Math.sin(relativeX * 12 + phaseRef.current * 2) * 20 * Math.exp(-relativeX * relativeX * 2);
          if (x === cx - 75) ctx.moveTo(x, y);
          else ctx.lineTo(x, y);
        }
        ctx.stroke();
      }

      // Outer Energy Orbits (vector rings spinning)
      ctx.lineWidth = 0.8;
      ctx.strokeStyle = isHovered ? 'rgba(93, 232, 255, 0.3)' : 'rgba(93, 232, 255, 0.12)';
      
      ctx.beginPath();
      ctx.ellipse(cx, cy, 110, 110, 0.25, phaseRef.current * 0.1, phaseRef.current * 0.1 + Math.PI * 2);
      ctx.stroke();

      ctx.strokeStyle = curState === 'thinking' ? 'rgba(124, 92, 255, 0.25)' : 'rgba(76, 125, 255, 0.1)';
      ctx.beginPath();
      ctx.ellipse(cx, cy, 130, 45, -0.4, -phaseRef.current * 0.15, -phaseRef.current * 0.15 + Math.PI * 2);
      ctx.stroke();

      animId = requestAnimationFrame(draw);
    };

    draw();

    return () => {
      window.removeEventListener('resize', resize);
      canvas.removeEventListener('mouseenter', handleMouseEnter);
      canvas.removeEventListener('mouseleave', handleMouseLeave);
      cancelAnimationFrame(animId);
    };
  }, []);

  return (
    <div className={`relative flex items-center justify-center ${className}`}>
      <canvas ref={canvasRef} className="w-[300px] h-[300px] md:w-[360px] md:h-[360px] block cursor-pointer" />
      {/* Central AIDA Logo Symbol */}
      <div className="absolute inset-0 flex items-center justify-center pointer-events-none z-20">
        <AIDALogoCore size={56} />
      </div>
    </div>
  );
}

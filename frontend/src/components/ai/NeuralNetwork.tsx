import React, { useEffect, useRef } from 'react';

interface NeuralNetworkProps {
  mode?: 'ambient' | 'attract';
  className?: string;
  intensity?: number;
}

interface Particle {
  x: number;
  y: number;
  baseX: number;
  baseY: number;
  vx: number;
  vy: number;
  z: number; // 3D depth approximation
  radius: number;
  color: string;
  angle: number;
  orbitRadius: number;
}

export default function NeuralNetwork({ mode = 'ambient', className = '', intensity = 1 }: NeuralNetworkProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const mouseRef = useRef({ x: -9999, y: -9999, active: false });

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    let animationFrameId: number;

    const resizeCanvas = () => {
      canvas.width = canvas.parentElement?.offsetWidth || window.innerWidth;
      canvas.height = canvas.parentElement?.offsetHeight || window.innerHeight;
    };
    resizeCanvas();
    window.addEventListener('resize', resizeCanvas);

    // Particle count: reduce on mobile devices for smooth CPU performance
    const isMobile = window.innerWidth < 768;
    const particleCount = isMobile ? 45 : (mode === 'attract' ? 140 : 90);
    const maxDistance = isMobile ? 90 : 120;
    const particles: Particle[] = [];

    // Color palette based on weights:
    // 70% Soft Blue (#4C7DFF), 20% Cyan (#5DE8FF), 10% Violet (#7C5CFF)
    const selectColor = () => {
      const rand = Math.random();
      if (rand < 0.70) return '#4C7DFF';
      if (rand < 0.90) return '#5DE8FF';
      return '#7C5CFF';
    };

    // Initialize particles
    for (let i = 0; i < particleCount; i++) {
      const x = Math.random() * canvas.width;
      const y = Math.random() * canvas.height;
      const z = Math.random() * 2 - 1; // z coordinate between -1 and 1
      particles.push({
        x,
        y,
        baseX: x,
        baseY: y,
        vx: (Math.random() - 0.5) * 0.35,
        vy: (Math.random() - 0.5) * 0.35,
        z,
        radius: (z + 1.2) * 1.4 + 0.6, // depth scaling radius
        color: selectColor(),
        angle: Math.random() * Math.PI * 2,
        orbitRadius: 20 + Math.random() * 60
      });
    }

    const handleMouseMove = (e: MouseEvent) => {
      const rect = canvas.getBoundingClientRect();
      mouseRef.current.x = e.clientX - rect.left;
      mouseRef.current.y = e.clientY - rect.top;
      mouseRef.current.active = true;
    };

    const handleMouseLeave = () => {
      mouseRef.current.x = -9999;
      mouseRef.current.y = -9999;
      mouseRef.current.active = false;
    };

    canvas.addEventListener('mousemove', handleMouseMove);
    canvas.addEventListener('mouseleave', handleMouseLeave);

    // Dynamic animation loop
    const animate = () => {
      // Very slight opacity fill to allow trails in "attract" mode, clean clear in "ambient"
      if (mode === 'attract') {
        ctx.fillStyle = 'rgba(5, 7, 13, 0.12)';
        ctx.fillRect(0, 0, canvas.width, canvas.height);
      } else {
        ctx.clearRect(0, 0, canvas.width, canvas.height);
      }

      // Draw AIDA Intelligence Core Glow in the center (Hero section)
      if (mode === 'ambient') {
        const cx = canvas.width / 2;
        const cy = canvas.height / 2;
        const radialGrad = ctx.createRadialGradient(cx, cy, 10, cx, cy, 280);
        radialGrad.addColorStop(0, 'rgba(93, 232, 255, 0.04)');
        radialGrad.addColorStop(0.5, 'rgba(76, 125, 255, 0.02)');
        radialGrad.addColorStop(1, 'transparent');
        ctx.fillStyle = radialGrad;
        ctx.beginPath();
        ctx.arc(cx, cy, 280, 0, Math.PI * 2);
        ctx.fill();
      }

      // Rotate network view slowly in ambient mode
      const rotationSpeed = 0.0008;
      const cosVal = Math.cos(rotationSpeed);
      const sinVal = Math.sin(rotationSpeed);
      const cx = canvas.width / 2;
      const cy = canvas.height / 2;

      particles.forEach(p => {
        // Apply 3D-like slow rotation
        if (mode === 'ambient') {
          const dx = p.x - cx;
          const dy = p.y - cy;
          p.x = cx + (dx * cosVal - dy * sinVal);
          p.y = cy + (dx * sinVal + dy * cosVal);
        }

        // Standard floating drift
        p.x += p.vx;
        p.y += p.vy;

        // Bouncing constraints
        if (p.x < 0 || p.x > canvas.width) p.vx *= -1;
        if (p.y < 0 || p.y > canvas.height) p.vy *= -1;

        // Mouse Interactivity
        if (mouseRef.current.active) {
          const dx = p.x - mouseRef.current.x;
          const dy = p.y - mouseRef.current.y;
          const dist = Math.sqrt(dx * dx + dy * dy);

          if (mode === 'attract') {
            // Pull particles towards the cursor
            if (dist < 320) {
              const force = (320 - dist) / 3200;
              p.vx -= (dx / dist) * force;
              p.vy -= (dy / dist) * force;
              
              // Orbit close to cursor
              if (dist < 100) {
                p.angle += 0.02;
                p.x = mouseRef.current.x + Math.cos(p.angle) * p.orbitRadius;
                p.y = mouseRef.current.y + Math.sin(p.angle) * p.orbitRadius;
              }
            }
          } else {
            // Ambient: Pushes particles away slightly (avoidance)
            if (dist < 140) {
              const force = (140 - dist) / 140;
              p.vx += (dx / dist) * force * 0.12;
              p.vy += (dy / dist) * force * 0.12;
            }
          }
        }

        // Apply friction to keep velocities stable
        p.vx *= 0.98;
        p.vy *= 0.98;

        // Draw particle dot with depth-based opacity
        const depthAlpha = (p.z + 1.2) / 2.2;
        ctx.fillStyle = p.color;
        ctx.globalAlpha = depthAlpha * intensity;
        
        ctx.beginPath();
        ctx.arc(p.x, p.y, p.radius, 0, Math.PI * 2);
        ctx.fill();
        ctx.globalAlpha = 1.0; // reset
      });

      // Connections Plexus
      for (let i = 0; i < particles.length; i++) {
        const p1 = particles[i];
        for (let j = i + 1; j < particles.length; j++) {
          const p2 = particles[j];
          const dx = p1.x - p2.x;
          const dy = p1.y - p2.y;
          const dist = Math.sqrt(dx * dx + dy * dy);

          if (dist < maxDistance) {
            const opacity = (1 - dist / maxDistance) * 0.22 * intensity;
            
            // Blend colors of connecting lines based on node colors
            let strokeColor = 'rgba(76, 125, 255, '; // Electric Blue default
            if (p1.color === '#5DE8FF' || p2.color === '#5DE8FF') {
              strokeColor = 'rgba(93, 232, 255, '; // Cyan active
            } else if (p1.color === '#7C5CFF' || p2.color === '#7C5CFF') {
              strokeColor = 'rgba(124, 92, 255, '; // Violet high active
            }
            
            ctx.strokeStyle = `${strokeColor}${opacity})`;
            ctx.lineWidth = 0.5 + (p1.z + p2.z + 2) * 0.2;
            ctx.beginPath();
            ctx.moveTo(p1.x, p1.y);
            ctx.lineTo(p2.x, p2.y);
            ctx.stroke();

            // Low poly filled triangulation (creates the 3D plexus volume)
            for (let k = j + 1; k < particles.length; k++) {
              const p3 = particles[k];
              const dist2 = Math.sqrt((p2.x - p3.x) ** 2 + (p2.y - p3.y) ** 2);
              const dist3 = Math.sqrt((p1.x - p3.x) ** 2 + (p1.y - p3.y) ** 2);

              if (dist2 < maxDistance - 20 && dist3 < maxDistance - 20) {
                const triOpacity = (1 - (dist + dist2 + dist3) / (maxDistance * 3)) * 0.05 * intensity;
                ctx.fillStyle = `rgba(76, 125, 255, ${triOpacity})`;
                ctx.beginPath();
                ctx.moveTo(p1.x, p1.y);
                ctx.lineTo(p2.x, p2.y);
                ctx.lineTo(p3.x, p3.y);
                ctx.closePath();
                ctx.fill();
              }
            }
          }
        }

        // Draw connections to cursor
        if (mouseRef.current.active) {
          const dx = p1.x - mouseRef.current.x;
          const dy = p1.y - mouseRef.current.y;
          const dist = Math.sqrt(dx * dx + dy * dy);

          if (dist < (mode === 'attract' ? 240 : 160)) {
            const baseDist = mode === 'attract' ? 240 : 160;
            const opacity = (1 - dist / baseDist) * (mode === 'attract' ? 0.45 : 0.22) * intensity;
            ctx.strokeStyle = mode === 'attract' 
              ? `rgba(95, 232, 255, ${opacity})`
              : `rgba(139, 92, 246, ${opacity})`;
            ctx.lineWidth = 0.8;
            ctx.beginPath();
            ctx.moveTo(p1.x, p1.y);
            ctx.lineTo(mouseRef.current.x, mouseRef.current.y);
            ctx.stroke();
          }
        }
      }

      // Draw cursor attraction core glow in attract mode
      if (mode === 'attract' && mouseRef.current.active) {
        ctx.shadowBlur = 20;
        ctx.shadowColor = '#5FE8FF';
        ctx.fillStyle = '#ffffff';
        ctx.beginPath();
        ctx.arc(mouseRef.current.x, mouseRef.current.y, 4, 0, Math.PI * 2);
        ctx.fill();
        ctx.shadowBlur = 0; // reset
      }

      animationFrameId = requestAnimationFrame(animate);
    };

    animate();

    return () => {
      window.removeEventListener('resize', resizeCanvas);
      canvas.removeEventListener('mousemove', handleMouseMove);
      canvas.removeEventListener('mouseleave', handleMouseLeave);
      cancelAnimationFrame(animationFrameId);
    };
  }, [mode, intensity]);

  return (
    <canvas 
      ref={canvasRef} 
      className={`absolute inset-0 w-full h-full block pointer-events-auto z-0 ${className}`} 
    />
  );
}

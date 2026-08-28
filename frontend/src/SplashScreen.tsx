import React, { useState, useEffect, useRef } from 'react';
import { motion, AnimatePresence } from 'motion/react';

interface SplashScreenProps {
  onComplete: () => void;
}

interface Particle {
  x: number;
  y: number;
  vx: number;
  vy: number;
  radius: number;
  color: string;
}

export default function SplashScreen({ onComplete }: SplashScreenProps) {
  const [phase, setPhase] = useState(0);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  
  // Hexadecimal message from the image: "The easiest way to save money is to waste less energy."
  const initialHexLines = [
    "54 68 65 20 65 61 73 69 65 73 74 20 77 61",
    "79 20 74 6f 20 73 61 76 65 20 6d 6f 6e 65 79",
    "20 69 73 20 74 6f 20 77 61 73 74 65 20 6c",
    "65 73 73 20 65 6e 65 72 67 79 2e"
  ];

  const [hexLines, setHexLines] = useState<string[]>(initialHexLines);

  useEffect(() => {
    const timers = [
      setTimeout(() => setPhase(1), 600),
      setTimeout(() => setPhase(2), 1500),
      setTimeout(() => setPhase(3), 2500),
      setTimeout(() => onComplete(), 5800), // Gives ample time to view the custom animations
    ];
    return () => timers.forEach(t => clearTimeout(t));
  }, [onComplete]);

  // Animate/glitch the hex codes slightly for a high-tech loading feel
  useEffect(() => {
    const glitchInterval = setInterval(() => {
      setHexLines(prev => {
        return prev.map((line, idx) => {
          const parts = line.split(" ");
          // Randomly change 1-2 bytes to random hex values for 80ms, then revert
          if (Math.random() > 0.4) {
            const glitchIdx = Math.floor(Math.random() * parts.length);
            const originalVal = parts[glitchIdx];
            const randomHex = Math.floor(Math.random() * 256).toString(16).padStart(2, '0');
            parts[glitchIdx] = randomHex;
            
            // Revert after 100ms
            setTimeout(() => {
              setHexLines(current => {
                const currentParts = current[idx].split(" ");
                currentParts[glitchIdx] = originalVal;
                return current.map((l, i) => i === idx ? currentParts.join(" ") : l);
              });
            }, 100);
          }
          return parts.join(" ");
        });
      });
    }, 400);

    return () => clearInterval(glitchInterval);
  }, []);

  // Plexus / Constellation Neural Net Canvas Animation (on the right half)
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    let animationId: number;

    const resizeCanvas = () => {
      canvas.width = window.innerWidth;
      canvas.height = window.innerHeight;
    };
    resizeCanvas();
    window.addEventListener('resize', resizeCanvas);

    // Initialize particles on the right side of the screen
    const particles: Particle[] = [];
    const particleCount = 75;
    const connectionDist = 110;
    const triangleDist = 95;

    for (let i = 0; i < particleCount; i++) {
      // Confine particle spawning mostly to the right 60% of the screen
      const minX = canvas.width * 0.38;
      const maxX = canvas.width + 30;
      particles.push({
        x: minX + Math.random() * (maxX - minX),
        y: Math.random() * canvas.height,
        vx: (Math.random() - 0.5) * 0.45,
        vy: (Math.random() - 0.5) * 0.45,
        radius: 1.5 + Math.random() * 2,
        color: Math.random() > 0.35 ? '#00f2ff' : '#ff00c8'
      });
    }

    const draw = () => {
      ctx.fillStyle = '#030405'; // Var --ae-bg
      ctx.fillRect(0, 0, canvas.width, canvas.height);

      // Draw faint nebula background under plexus
      const gradient = ctx.createRadialGradient(
        canvas.width * 0.75, canvas.height * 0.5, 10,
        canvas.width * 0.75, canvas.height * 0.5, canvas.width * 0.4
      );
      gradient.addColorStop(0, 'rgba(112, 0, 255, 0.08)');
      gradient.addColorStop(0.5, 'rgba(0, 242, 255, 0.03)');
      gradient.addColorStop(1, 'transparent');
      ctx.fillStyle = gradient;
      ctx.fillRect(0, 0, canvas.width, canvas.height);

      // Update positions
      particles.forEach(p => {
        p.x += p.vx;
        p.y += p.vy;

        // Keep them bounded to the right side
        const minX = canvas.width * 0.35;
        const maxX = canvas.width + 40;

        if (p.x < minX) {
          p.x = minX;
          p.vx *= -1;
        } else if (p.x > maxX) {
          p.x = maxX;
          p.vx *= -1;
        }

        if (p.y < -20) {
          p.y = canvas.height + 20;
        } else if (p.y > canvas.height + 20) {
          p.y = -20;
        }
      });

      // Plexus Line connection and Triangulation
      for (let i = 0; i < particles.length; i++) {
        const p1 = particles[i];

        // Draw particle dot
        ctx.fillStyle = p1.color;
        ctx.shadowBlur = 8;
        ctx.shadowColor = p1.color;
        ctx.beginPath();
        ctx.arc(p1.x, p1.y, p1.radius, 0, Math.PI * 2);
        ctx.fill();
        ctx.shadowBlur = 0; // reset

        for (let j = i + 1; j < particles.length; j++) {
          const p2 = particles[j];
          const dx = p1.x - p2.x;
          const dy = p1.y - p2.y;
          const dist = Math.sqrt(dx * dx + dy * dy);

          if (dist < connectionDist) {
            // Draw connection line
            const lineOpacity = (1 - dist / connectionDist) * 0.28;
            ctx.strokeStyle = `rgba(0, 242, 255, ${lineOpacity})`;
            ctx.lineWidth = 0.8;
            ctx.beginPath();
            ctx.moveTo(p1.x, p1.y);
            ctx.lineTo(p2.x, p2.y);
            ctx.stroke();

            // Draw filled triangles for 3-way proximity
            for (let k = j + 1; k < particles.length; k++) {
              const p3 = particles[k];
              const dx2 = p2.x - p3.x;
              const dy2 = p2.y - p3.y;
              const dist2 = Math.sqrt(dx2 * dx2 + dy2 * dy2);

              const dx3 = p1.x - p3.x;
              const dy3 = p1.y - p3.y;
              const dist3 = Math.sqrt(dx3 * dx3 + dy3 * dy3);

              if (dist2 < triangleDist && dist3 < triangleDist) {
                const totalDist = dist + dist2 + dist3;
                const triOpacity = (1 - totalDist / (connectionDist * 3)) * 0.085;
                ctx.fillStyle = `rgba(0, 242, 255, ${triOpacity})`;
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
      }

      animationId = requestAnimationFrame(draw);
    };

    draw();

    return () => {
      window.removeEventListener('resize', resizeCanvas);
      cancelAnimationFrame(animationId);
    };
  }, []);

  return (
    <motion.div
      className="ae-splash cs-layout"
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0, scale: 1.05, filter: "brightness(1.5) blur(10px)" }}
      transition={{ duration: 0.8 }}
    >
      {/* Dynamic Animated Plexus Background */}
      <canvas ref={canvasRef} className="cs-plexus-canvas" />
      
      {/* Cyber/Red Gradient Nebulas */}
      <div className="ae-bg">
        <div className="ae-nebula ae-nebula-red" />
        <div className="ae-nebula ae-nebula-1" />
        <div className="ae-nebula ae-nebula-2" />
      </div>

      {/* Grid Layout Container */}
      <div className="cs-grid">
        
        {/* Left Cyber/Branding Column */}
        <div className="cs-left-panel">
          
          {/* Hashtag Header */}
          <motion.div 
            className="cs-hashtag"
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.8 }}
          >
            #JOINTHEREVOLUTION
          </motion.div>

          {/* Hexadecimal Grid block */}
          <div className="cs-hex-container">
            {hexLines.map((line, idx) => (
              <motion.div 
                key={idx}
                className="cs-hex-line"
                initial={{ opacity: 0 }}
                animate={{ opacity: 0.85 }}
                transition={{ delay: 0.2 + idx * 0.15, duration: 0.5 }}
              >
                {line}
              </motion.div>
            ))}
          </div>

          {/* Brand Logo & Tagline at bottom-left */}
          <div className="cs-brand-container">
            <motion.div 
              className="cs-logo-wrapper"
              initial={{ opacity: 0, y: 15 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.8, delay: 0.8 }}
            >
              <h1 className="cs-logo">
                AIDA
              </h1>
            </motion.div>

            <motion.div 
              className="cs-loading-bar-wrapper"
              initial={{ width: 0 }}
              animate={{ width: "260px" }}
              transition={{ duration: 1.5, delay: 1, ease: "easeInOut" }}
            >
              <div className="cs-loading-bar-inner" />
            </motion.div>
          </div>

          {/* Bottom Actions */}
          <AnimatePresence>
            {phase >= 3 && (
              <motion.div 
                className="cs-action-panel"
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0 }}
                transition={{ duration: 0.4 }}
              >
                <button className="ae-btn" type="button" onClick={onComplete}>
                  <div className="ae-btn-content">
                    <span className="ae-btn-text">TIZIMGA KIRISH</span>
                    <div className="ae-btn-corner ae-tl" />
                    <div className="ae-btn-corner ae-tr" />
                    <div className="ae-btn-corner ae-bl" />
                    <div className="ae-btn-corner ae-br" />
                  </div>
                  <div className="ae-btn-glow" />
                </button>
                <button className="ae-skip" type="button" onClick={onComplete}>
                  O'tkazib yuborish
                </button>
              </motion.div>
            )}
          </AnimatePresence>
        </div>

        {/* Right side is intentionally left for the canvas constellation plexus view */}
        <div className="cs-right-panel" />
      </div>

      {/* Brand logo at top right corner */}
      <div className="cs-corner-logo">
        <svg viewBox="0 0 100 100" className="cs-icon-logo">
          <path 
            d="M20,20 C40,20 50,30 50,50 C50,70 60,80 80,80" 
            fill="none" 
            stroke="#fff" 
            strokeWidth="8" 
            strokeLinecap="round" 
          />
          <path 
            d="M80,20 C60,20 50,30 50,50 C50,70 40,80 20,80" 
            fill="none" 
            stroke="var(--ae-primary)" 
            strokeWidth="8" 
            strokeLinecap="round" 
          />
        </svg>
      </div>
    </motion.div>
  );
}

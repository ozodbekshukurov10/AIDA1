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
      setTimeout(() => onComplete(), 5800),
    ];
    return () => timers.forEach(t => clearTimeout(t));
  }, [onComplete]);

  // Animate/glitch the hex codes slightly for a high-tech loading feel
  useEffect(() => {
    const glitchInterval = setInterval(() => {
      setHexLines(prev => {
        return prev.map((line, idx) => {
          const parts = line.split(" ");
          if (Math.random() > 0.4) {
            const glitchIdx = Math.floor(Math.random() * parts.length);
            const originalVal = parts[glitchIdx];
            const randomHex = Math.floor(Math.random() * 256).toString(16).padStart(2, '0');
            parts[glitchIdx] = randomHex;
            
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

  // Plexus / Constellation Neural Net Canvas Animation
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

    const particles: Particle[] = [];
    const particleCount = 75;
    const connectionDist = 110;
    const triangleDist = 95;

    for (let i = 0; i < particleCount; i++) {
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
      ctx.fillStyle = '#030405';
      ctx.fillRect(0, 0, canvas.width, canvas.height);

      const gradient = ctx.createRadialGradient(
        canvas.width * 0.75, canvas.height * 0.5, 10,
        canvas.width * 0.75, canvas.height * 0.5, canvas.width * 0.4
      );
      gradient.addColorStop(0, 'rgba(112, 0, 255, 0.08)');
      gradient.addColorStop(0.5, 'rgba(0, 242, 255, 0.03)');
      gradient.addColorStop(1, 'transparent');
      ctx.fillStyle = gradient;
      ctx.fillRect(0, 0, canvas.width, canvas.height);

      particles.forEach(p => {
        p.x += p.vx;
        p.y += p.vy;

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

      for (let i = 0; i < particles.length; i++) {
        const p1 = particles[i];

        ctx.fillStyle = p1.color;
        ctx.shadowBlur = 8;
        ctx.shadowColor = p1.color;
        ctx.beginPath();
        ctx.arc(p1.x, p1.y, p1.radius, 0, Math.PI * 2);
        ctx.fill();
        ctx.shadowBlur = 0;

        for (let j = i + 1; j < particles.length; j++) {
          const p2 = particles[j];
          const dx = p1.x - p2.x;
          const dy = p1.y - p2.y;
          const dist = Math.sqrt(dx * dx + dy * dy);

          if (dist < connectionDist) {
            const lineOpacity = (1 - dist / connectionDist) * 0.28;
            ctx.strokeStyle = `rgba(0, 242, 255, ${lineOpacity})`;
            ctx.lineWidth = 0.8;
            ctx.beginPath();
            ctx.moveTo(p1.x, p1.y);
            ctx.lineTo(p2.x, p2.y);
            ctx.stroke();

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
      className="fixed inset-0 z-[9999] bg-[#03050A] text-[#F5F7FF] overflow-hidden select-none font-sans flex"
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0, scale: 1.05, filter: "brightness(1.5) blur(10px)" }}
      transition={{ duration: 0.8 }}
    >
      {/* Dynamic Animated Plexus Background */}
      <canvas ref={canvasRef} className="absolute inset-0 w-full h-full pointer-events-none z-0" />
      
      {/* Cyber Nebulas */}
      <div className="absolute inset-0 pointer-events-none z-0">
        <div className="absolute top-1/4 left-1/4 w-[400px] h-[400px] bg-[#5DE8FF]/5 blur-[140px] rounded-full" />
        <div className="absolute bottom-1/4 right-1/4 w-[450px] h-[450px] bg-[#7C5CFF]/5 blur-[150px] rounded-full animate-pulse" />
      </div>

      {/* Main Grid Layout */}
      <div className="relative z-10 w-full max-w-7xl mx-auto px-8 md:px-16 flex flex-col justify-between py-12 min-h-screen">
        
        {/* Top Header Hashtag */}
        <motion.div 
          className="font-['JetBrains_Mono',monospace] text-xs md:text-sm tracking-[0.35em] text-[#5DE8FF] uppercase font-bold"
          initial={{ opacity: 0, x: -20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ duration: 0.8 }}
        >
          #JOINTHEREVOLUTION
        </motion.div>

        {/* Middle Body Content: Hex Grid + AIDA Title + Sleek Smooth Buttons */}
        <div className="flex flex-col gap-8 max-w-xl my-auto">
          
          {/* Hexadecimal Grid block */}
          <div className="font-['JetBrains_Mono',monospace] text-xs md:text-sm tracking-wider text-[#9CA9BC]/70 flex flex-col gap-1.5">
            {hexLines.map((line, idx) => (
              <motion.div 
                key={idx}
                initial={{ opacity: 0 }}
                animate={{ opacity: 0.85 }}
                transition={{ delay: 0.2 + idx * 0.15, duration: 0.5 }}
              >
                {line}
              </motion.div>
            ))}
          </div>

          {/* Brand Title AIDA with Smooth Glowing Underline */}
          <div className="flex flex-col gap-2">
            <motion.h1 
              className="font-['Space_Grotesk',sans-serif] font-black text-5xl md:text-7xl text-[#F5F7FF] tracking-wider uppercase leading-none drop-shadow-[0_0_25px_rgba(93,232,255,0.4)]"
              initial={{ opacity: 0, y: 15 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.8, delay: 0.8 }}
            >
              A I D A
            </motion.h1>

            <motion.div 
              className="h-[3px] rounded-full bg-gradient-to-r from-[#5DE8FF] via-[#4C7DFF] to-[#7C5CFF] shadow-[0_0_15px_#5DE8FF]"
              initial={{ width: 0 }}
              animate={{ width: "240px" }}
              transition={{ duration: 1.5, delay: 1, ease: "easeInOut" }}
            />
          </div>

          {/* Sleek Smooth Rounded Buttons Panel */}
          <AnimatePresence>
            {phase >= 3 && (
              <motion.div 
                className="flex items-center gap-5 mt-4"
                initial={{ opacity: 0, y: 15, filter: 'blur(8px)' }}
                animate={{ opacity: 1, y: 0, filter: 'blur(0px)' }}
                exit={{ opacity: 0 }}
                transition={{ duration: 0.5, ease: [0.16, 1, 0.3, 1] }}
              >
                {/* Primary Smooth Glowing Button: TIZIMGA KIRISH */}
                <motion.button 
                  type="button" 
                  onClick={onComplete}
                  whileHover={{ scale: 1.05, boxShadow: '0 0 30px rgba(93,232,255,0.6)' }}
                  whileTap={{ scale: 0.95 }}
                  className="px-8 py-3.5 rounded-full border border-[#5DE8FF]/50 bg-gradient-to-r from-[#4C7DFF] via-[#5DE8FF]/20 to-[#7C5CFF] text-[#F5F7FF] font-['JetBrains_Mono',monospace] text-xs font-bold tracking-[0.25em] uppercase cursor-pointer backdrop-blur-md transition-all duration-300 shadow-[0_0_20px_rgba(76,125,255,0.3)] hover:text-[#5DE8FF]"
                >
                  TIZIMGA KIRISH â†’
                </motion.button>

                {/* Secondary Smooth Glass Button: O'tkazib yuborish */}
                <motion.button 
                  type="button" 
                  onClick={onComplete}
                  whileHover={{ scale: 1.05, backgroundColor: 'rgba(93,232,255,0.15)' }}
                  whileTap={{ scale: 0.95 }}
                  className="px-6 py-3.5 rounded-full border border-white/20 bg-white/5 text-[#9CA9BC] hover:text-[#F5F7FF] font-['JetBrains_Mono',monospace] text-xs font-medium tracking-wider cursor-pointer backdrop-blur-md transition-all duration-300"
                >
                  O'tkazib yuborish
                </motion.button>
              </motion.div>
            )}
          </AnimatePresence>

        </div>

        {/* Bottom Status Tag */}
        <div className="font-['JetBrains_Mono',monospace] text-[10px] text-[#5DE8FF]/50 tracking-[0.3em] uppercase">
          SYSTEM STATUS: ONLINE // OPERATIONAL
        </div>

      </div>

    </motion.div>
  );
}

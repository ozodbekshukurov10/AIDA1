import React, { useRef, useState } from 'react';
import { motion, useSpring, useMotionValue } from 'motion/react';

interface CardProps {
  children: React.ReactNode;
  className?: string;
  onClick?: () => void;
  maxTilt?: number;
  accentColor?: 'cyan' | 'electric-blue' | 'violet' | 'purple' | 'magenta' | 'blue' | 'default';
}

export default function Card({ 
  children, 
  className = '', 
  onClick, 
  maxTilt = 8,
  accentColor = 'default'
}: CardProps) {
  const cardRef = useRef<HTMLDivElement>(null);

  // Motion values for spring-smoothed rotations
  const rotateX = useMotionValue(0);
  const rotateY = useMotionValue(0);

  // Spot light background position
  const [spotlight, setSpotlight] = useState({ x: 0, y: 0, opacity: 0 });

  const springConfig = { damping: 25, stiffness: 240, mass: 0.5 };
  const springX = useSpring(rotateX, springConfig);
  const springY = useSpring(rotateY, springConfig);

  const handleMouseMove = (e: React.MouseEvent) => {
    const card = cardRef.current;
    if (!card) return;
    const rect = card.getBoundingClientRect();
    
    // Relative coordinates [0, 1]
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;
    
    // Tilt calculations
    const percentX = x / rect.width;
    const percentY = y / rect.height;
    
    // Rotate values
    const rotX = (0.5 - percentY) * maxTilt;
    const rotY = (percentX - 0.5) * maxTilt;
    
    rotateX.set(rotX);
    rotateY.set(rotY);

    setSpotlight({ x, y, opacity: 1 });
  };

  const handleMouseLeave = () => {
    rotateX.set(0);
    rotateY.set(0);
    setSpotlight(prev => ({ ...prev, opacity: 0 }));
  };

  // Accent color mapping for borders & glow overlays
  const hoverBorders = {
    'cyan': 'hover:border-[#5DE8FF]/30',
    'electric-blue': 'hover:border-[#4C7DFF]/30',
    'violet': 'hover:border-[#7C5CFF]/30',
    'purple': 'hover:border-[#A78BFA]/30',
    'magenta': 'hover:border-[#D56BFF]/30',
    'blue': 'hover:border-[#4C7DFF]/25',
    'default': 'hover:border-white/15'
  };

  const spotlightGlows = {
    'cyan': 'rgba(93, 232, 255, 0.08)',
    'electric-blue': 'rgba(76, 125, 255, 0.08)',
    'violet': 'rgba(124, 92, 255, 0.08)',
    'purple': 'rgba(167, 139, 250, 0.08)',
    'magenta': 'rgba(213, 107, 255, 0.08)',
    'blue': 'rgba(76, 125, 255, 0.06)',
    'default': 'rgba(255, 255, 255, 0.04)'
  };

  const glowColor = spotlightGlows[accentColor];

  return (
    <motion.div
      ref={cardRef}
      onMouseMove={handleMouseMove}
      onMouseLeave={handleMouseLeave}
      onClick={onClick}
      style={{
        rotateX: springX,
        rotateY: springY,
        transformStyle: 'preserve-3d',
      }}
      className={`relative p-8 rounded-2xl border border-white/8 bg-white/[0.03] backdrop-blur-xl transition-all duration-300 shadow-[0_10px_35px_rgba(0,0,0,0.4)] overflow-hidden cursor-pointer select-none ${hoverBorders[accentColor]} ${className}`}
    >
      
      {/* Spotlight Radial Glow Overlay */}
      <div 
        className="absolute inset-0 pointer-events-none transition-opacity duration-300"
        style={{
          opacity: spotlight.opacity,
          background: `radial-gradient(circle 140px at ${spotlight.x}px ${spotlight.y}px, ${glowColor}, transparent 80%)`
        }}
      />

      {/* Card Content wrapper to support 3D translateZ */}
      <div style={{ transform: 'translateZ(30px)' }} className="relative z-10 flex flex-col gap-4">
        {children}
      </div>

    </motion.div>
  );
}

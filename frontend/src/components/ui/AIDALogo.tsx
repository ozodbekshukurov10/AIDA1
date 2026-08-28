import React from 'react';
import { motion } from 'motion/react';

interface AIDALogoProps {
  className?: string;
  size?: number | string;
  strokeWidth?: number;
  color?: string;
}

// 1. Base SVG Logo Component (Clean connection lines)
export default function AIDALogo({ 
  className = '', 
  size = '100%', 
  strokeWidth = 8,
  color = 'currentColor' 
}: AIDALogoProps) {
  return (
    <svg 
      viewBox="0 0 100 100" 
      fill="none" 
      xmlns="http://www.w3.org/2000/svg"
      className={className}
      style={{ width: size, height: size }}
    >
      <path 
        d="M20,20 C40,20 50,30 50,50 C50,70 60,80 80,80" 
        stroke={color} 
        strokeWidth={strokeWidth} 
        strokeLinecap="round" 
      />
      <path 
        d="M80,20 C60,20 50,30 50,50 C50,70 40,80 20,80" 
        stroke={color} 
        strokeWidth={strokeWidth} 
        strokeLinecap="round" 
      />
    </svg>
  );
}

// 2. Animated Reveal variant (SVG stroke drawing-in + horizontal light sheen sweep)
export function AIDALogoReveal({ size = 110, className = '' }) {
  return (
    <div className={`relative flex items-center justify-center ${className}`}>
      <svg 
        viewBox="0 0 100 100" 
        fill="none" 
        xmlns="http://www.w3.org/2000/svg"
        style={{ width: size, height: size }}
        className="filter drop-shadow-[0_0_15px_rgba(93,232,255,0.2)]"
      >
        <motion.path 
          d="M20,20 C40,20 50,30 50,50 C50,70 60,80 80,80" 
          stroke="#5DE8FF" 
          strokeWidth="7.5" 
          strokeLinecap="round" 
          initial={{ pathLength: 0 }}
          animate={{ pathLength: 1 }}
          transition={{ duration: 1.6, ease: "easeInOut" }}
        />
        <motion.path 
          d="M80,20 C60,20 50,30 50,50 C50,70 40,80 20,80" 
          stroke="#7C5CFF" 
          strokeWidth="7.5" 
          strokeLinecap="round" 
          initial={{ pathLength: 0 }}
          animate={{ pathLength: 1 }}
          transition={{ duration: 1.6, delay: 0.3, ease: "easeInOut" }}
        />
      </svg>
      {/* Light sheen sweep shimmer */}
      <motion.div
        initial={{ x: '-100%', opacity: 0 }}
        animate={{ x: '200%', opacity: [0, 0.75, 0] }}
        transition={{ duration: 1.6, delay: 1.6, ease: "easeInOut" }}
        className="absolute inset-0 w-full h-full bg-gradient-to-r from-transparent via-[#5DE8FF]/30 to-transparent skew-x-12 mix-blend-overlay pointer-events-none"
      />
    </div>
  );
}

// 3. Glowing Atmospheric variant
export function AIDALogoGlow({ size = 60, className = '' }) {
  return (
    <div className={`relative flex items-center justify-center ${className}`}>
      <div className="absolute w-[180%] h-[180%] rounded-full bg-gradient-to-tr from-[#5DE8FF]/12 via-[#4C7DFF]/8 to-[#7C5CFF]/12 blur-2xl pointer-events-none" />
      <AIDALogo size={size} color="#F5F7FF" className="filter drop-shadow-[0_0_10px_rgba(255,255,255,0.15)]" />
    </div>
  );
}

// 4. HUD Preloader pulsing variant
export function AIDALogoLoader({ size = 70, progress = 0, className = '' }) {
  return (
    <div className={`flex flex-col items-center justify-center gap-6 ${className}`}>
      <motion.div
        animate={{ 
          scale: [0.97, 1.03, 0.97],
          opacity: [0.75, 1.0, 0.75]
        }}
        transition={{ duration: 1.8, repeat: Infinity, ease: "easeInOut" }}
        className="relative"
      >
        <div className="absolute inset-0 blur-md opacity-25 bg-[#5DE8FF] rounded-full scale-90" />
        <AIDALogo size={size} color="#5DE8FF" />
      </motion.div>
      <div className="flex flex-col items-center gap-2">
        <span className="text-[10px] font-mono tracking-[0.25em] text-[#62E8FF] uppercase">
          Initializing Intelligence
        </span>
        <span className="text-xs font-mono text-[#9CA9BC]">{progress}%</span>
      </div>
    </div>
  );
}

// 5. Central AI Core variant
export function AIDALogoCore({ size = 44, className = '' }) {
  return (
    <div className={`relative flex items-center justify-center ${className}`}>
      <div className="absolute w-[200%] h-[200%] rounded-full bg-radial-gradient from-[#5DE8FF]/15 via-transparent to-transparent blur-xl pointer-events-none" />
      <AIDALogo size={size} strokeWidth={8.5} color="#5DE8FF" className="filter drop-shadow-[0_0_12px_rgba(93,232,255,0.5)]" />
    </div>
  );
}

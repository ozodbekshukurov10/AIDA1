import React from 'react';
import { motion } from 'motion/react';
import { AIDALogoReveal as OfficialLogoReveal } from '../ui/AIDALogo';

interface AIDALogoRevealProps {
  active: boolean;
  phase?: number; // 1: Initial Reveal, 12: Massive Final Brand Reveal, 13: Fly-Through Transition
  onStartClick?: () => void;
}

export default function AIDALogoReveal({ active, phase = 1, onStartClick }: AIDALogoRevealProps) {
  if (!active) return null;

  const isFinalReveal = phase === 12 || phase === 13;
  const isFlyThrough = phase === 13;

  return (
    <div className="absolute inset-0 flex flex-col items-center justify-center bg-transparent z-30 pointer-events-none select-none overflow-hidden">
      
      {/* ─── 1. Orbital Precision Energy Rings & Micro-Pulse ─── */}
      <motion.div
        initial={{ opacity: 0, scale: isFinalReveal ? 0.6 : 0.7 }}
        animate={
          isFlyThrough
            ? { scale: [1, 5, 18], opacity: [1, 0.7, 0], filter: "blur(12px)" }
            : { opacity: 1, scale: isFinalReveal ? 1.05 : 1, filter: "blur(0px)" }
        }
        exit={{ opacity: 0, scale: 1.25, filter: "blur(8px)" }}
        transition={{ 
          duration: isFlyThrough ? 1.3 : 1.4, 
          ease: isFlyThrough ? [0.22, 1, 0.36, 1] : [0.16, 1, 0.3, 1] 
        }}
        className="absolute flex items-center justify-center pointer-events-none"
      >
        <svg 
          className={isFinalReveal ? "w-[360px] h-[360px] md:w-[520px] md:h-[520px]" : "w-[300px] h-[300px] md:w-[400px] md:h-[400px]"} 
          viewBox="0 0 100 100"
        >
          <defs>
            <linearGradient id="finalLogoRingGrad" x1="0%" y1="0%" x2="100%" y2="100%">
              <stop offset="0%" stopColor="#5DE8FF" stopOpacity="0.85" />
              <stop offset="45%" stopColor="#4C7DFF" stopOpacity="0.20" />
              <stop offset="80%" stopColor="#7C5CFF" stopOpacity="0.65" />
              <stop offset="100%" stopColor="#5DE8FF" stopOpacity="0" />
            </linearGradient>
            <filter id="finalSubtleGlow">
              <feGaussianBlur stdDeviation="1.5" result="blur" />
              <feMerge>
                <feMergeNode in="blur" />
                <feMergeNode in="SourceGraphic" />
              </feMerge>
            </filter>
          </defs>
          
          {/* Primary Orbital Ring */}
          <circle
            cx="50"
            cy="50"
            r="44"
            fill="none"
            stroke="url(#finalLogoRingGrad)"
            strokeWidth={isFinalReveal ? "0.6" : "0.5"}
            strokeDasharray="160 120"
            className="origin-center animate-[spin_10s_linear_infinite]"
            filter="url(#finalSubtleGlow)"
          />
          
          {/* Counter Ring */}
          <circle
            cx="50"
            cy="50"
            r="41"
            fill="none"
            stroke="rgba(93, 232, 255, 0.15)"
            strokeWidth="0.25"
            strokeDasharray="30 140"
            className="origin-center animate-[spin_15s_linear_infinite_reverse]"
          />
        </svg>

        {/* Final Micro-Pulse Ring (radiates outward when final reveal triggers) */}
        {isFinalReveal && !isFlyThrough && (
          <motion.div
            initial={{ opacity: 0.8, scale: 0.4 }}
            animate={{ opacity: 0, scale: 2.2 }}
            transition={{ duration: 2.2, ease: "easeOut", delay: 0.6 }}
            className="absolute w-72 h-72 rounded-full border border-[#5DE8FF]/40 shadow-[0_0_50px_rgba(93,232,255,0.3)] pointer-events-none"
          />
        )}
      </motion.div>

      {/* ─── 2. Main Brand Container — 60FPS GPU Fly-Through Motion Wrapper ─── */}
      <motion.div
        style={{ willChange: 'transform, opacity', transform: 'translateZ(0)' }}
        animate={
          isFlyThrough
            ? { 
                scale: [1, 5, 15], 
                opacity: [1, 0.8, 0],
              }
            : { 
                scale: 1, 
                opacity: 1, 
              }
        }
        transition={{ 
          duration: isFlyThrough ? 1.2 : 1.4, 
          ease: isFlyThrough ? [0.16, 1, 0.3, 1] : [0.16, 1, 0.3, 1] 
        }}
        className="flex flex-col items-center justify-center z-10 relative px-6 py-4 text-center transform-gpu"
      >
        
        {/* Tier 1: Official Logo Symbol Reveal */}
        <motion.div
          initial={{ opacity: 0, scale: 0.8, y: -10 }}
          animate={{ opacity: 1, scale: 1, y: 0 }}
          transition={{ duration: 1.2, ease: [0.16, 1, 0.3, 1] }}
        >
          <OfficialLogoReveal size={isFinalReveal ? 135 : 110} className="mb-4 md:mb-6" />
        </motion.div>

        {/* Tier 2: MASSIVE "AIDA" Wordmark (Space Grotesk, 100% Crisp, Blur -> Sharp, Light Sweep) */}
        <motion.div className="relative overflow-hidden px-4 py-2">
          
          {/* Main Typography */}
          <motion.h1
            initial={{ opacity: 0, y: isFinalReveal ? 22 : 14, filter: "blur(18px)", scale: 0.94 }}
            animate={{ opacity: 1, y: 0, filter: "blur(0px)", scale: 1 }}
            exit={{ opacity: 0, y: -10, filter: "blur(8px)" }}
            transition={{ duration: isFinalReveal ? 1.6 : 1.4, delay: 0.35, ease: [0.16, 1, 0.3, 1] }}
            className={
              isFinalReveal 
                ? "font-['Space_Grotesk'] font-extrabold text-6xl sm:text-7xl md:text-8xl lg:text-9xl tracking-[0.20em] text-[#FFFFFF] pl-[0.20em] filter drop-shadow-[0_0_35px_rgba(93,232,255,0.35)] select-none leading-none"
                : "font-['Space_Grotesk'] font-bold text-4xl md:text-6xl tracking-[0.18em] text-[#FFFFFF] pl-[0.18em] filter drop-shadow-[0_0_20px_rgba(93,232,255,0.25)] select-none"
            }
          >
            AIDA
          </motion.h1>

          {/* Precision Light Sheen Sweep (Left -> Right across AIDA) */}
          {isFinalReveal && !isFlyThrough && (
            <motion.div
              initial={{ x: '-100%', opacity: 0 }}
              animate={{ x: '200%', opacity: [0, 0.7, 0] }}
              transition={{ duration: 1.6, delay: 1.1, ease: "easeInOut" }}
              className="absolute inset-0 w-1/2 bg-gradient-to-r from-transparent via-white/40 to-transparent skew-x-12 pointer-events-none"
            />
          )}

        </motion.div>

        {/* Tier 3: Subtitles — "ARTIFICIAL INTELLIGENCE" & "YOUR INTELLIGENT DIGITAL MIND" */}
        <motion.div
          initial={{ opacity: 0, y: 10, filter: "blur(8px)" }}
          animate={{ opacity: 0.9, y: 0, filter: "blur(0px)" }}
          exit={{ opacity: 0 }}
          transition={{ duration: 1.4, delay: 0.8, ease: "easeOut" }}
          className="flex flex-col items-center gap-1.5 mt-4"
        >
          <div className="text-[10px] sm:text-xs md:text-sm font-sans tracking-[0.40em] text-[#5DE8FF] uppercase font-semibold pl-[0.40em]">
            ARTIFICIAL INTELLIGENCE
          </div>
          
          {isFinalReveal && (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 0.6 }}
              transition={{ delay: 1.3, duration: 1.0 }}
              className="text-[9px] sm:text-[10px] font-mono tracking-[0.30em] text-[#9CA9BC] uppercase mt-1 pl-[0.30em] border-t border-white/10 pt-2"
            >
              YOUR INTELLIGENT DIGITAL MIND
            </motion.div>
          )}
        </motion.div>

        {/* Tier 4: Interactive START Button (Phase 12 interactive hold) */}
        {isFinalReveal && !isFlyThrough && onStartClick && (
          <motion.button
            type="button"
            onClick={onStartClick}
            initial={{ opacity: 0, y: 20, scale: 0.9 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            whileHover={{ scale: 1.08, boxShadow: "0 0 40px rgba(93,232,255,0.5)" }}
            whileTap={{ scale: 0.95 }}
            transition={{ duration: 0.6, delay: 1.0 }}
            className="mt-8 px-8 py-3.5 rounded-full bg-[#5DE8FF]/10 border border-[#5DE8FF]/40 text-[#5DE8FF] font-['Space_Grotesk'] font-bold text-xs md:text-sm tracking-[0.3em] uppercase cursor-pointer backdrop-blur-xl shadow-[0_0_30px_rgba(93,232,255,0.25)] flex items-center gap-2.5 pointer-events-auto hover:bg-[#5DE8FF] hover:text-[#03050A] transition-colors duration-300"
          >
            <span className="w-2 h-2 rounded-full bg-[#5DE8FF] animate-ping" />
            START &rarr;
          </motion.button>
        )}

      </motion.div>

    </div>
  );
}

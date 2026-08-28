import React from 'react';
import { motion } from 'motion/react';

export default function AIOrb() {
  return (
    <div className="relative w-[340px] h-[340px] md:w-[420px] md:h-[420px] flex items-center justify-center select-none">
      
      {/* Outer Holographic Glow Aura */}
      <motion.div 
        className="absolute inset-0 bg-gradient-to-r from-[#5FE8FF]/10 via-[#4D7CFF]/10 to-[#8B5CF6]/10 rounded-full blur-[80px]"
        animate={{ 
          scale: [1, 1.15, 1],
          opacity: [0.6, 0.9, 0.6] 
        }}
        transition={{ 
          duration: 4, 
          repeat: Infinity, 
          ease: "easeInOut" 
        }}
      />

      {/* Sphere Central Core */}
      <motion.div 
        className="absolute w-48 h-48 md:w-60 md:h-60 rounded-full bg-gradient-to-tr from-[#5FE8FF]/20 via-[#4D7CFF]/10 to-[#8B5CF6]/30 border border-[#5FE8FF]/20 flex flex-col items-center justify-center backdrop-blur-md shadow-[0_0_60px_rgba(95,232,255,0.15),inset_0_0_30px_rgba(255,255,255,0.05)]"
        animate={{ 
          scale: [1, 1.05, 1],
          boxShadow: [
            "0 0 60px rgba(95,232,255,0.15), inset 0 0 30px rgba(255,255,255,0.05)",
            "0 0 100px rgba(139,92,246,0.3), inset 0 0 40px rgba(255,255,255,0.08)",
            "0 0 60px rgba(95,232,255,0.15), inset 0 0 30px rgba(255,255,255,0.05)"
          ]
        }}
        transition={{ 
          duration: 3, 
          repeat: Infinity, 
          ease: "easeInOut" 
        }}
      >
        {/* Core Center White Core */}
        <div className="absolute w-12 h-12 rounded-full bg-[#F5F7FA] blur-md opacity-30 animate-ping" />
        
        {/* Texts */}
        <span className="font-['Space_Grotesk'] text-3xl md:text-4xl font-extrabold tracking-[0.25em] text-[#F5F7FA] filter drop-shadow-[0_0_10px_rgba(255,255,255,0.4)]">
          AIDA
        </span>
        <span className="text-[9px] md:text-[10px] uppercase tracking-[0.3em] text-[#5FE8FF] font-medium text-center mt-2 px-4 max-w-[180px] leading-relaxed">
          Intelligence Core
        </span>
      </motion.div>

      {/* Animated Orbits */}
      {/* Orbit 1: Fast Clockwise */}
      <motion.div 
        className="absolute w-64 h-64 md:w-80 md:h-80 border border-dashed border-[#5FE8FF]/20 rounded-full"
        animate={{ rotate: 360 }}
        transition={{ duration: 18, repeat: Infinity, ease: "linear" }}
      >
        <div className="absolute top-0 left-1/2 -translate-x-1/2 w-2 h-2 bg-[#5FE8FF] rounded-full shadow-[0_0_8px_#5FE8FF]" />
      </motion.div>

      {/* Orbit 2: Slow Counter-Clockwise */}
      <motion.div 
        className="absolute w-80 h-80 md:w-[380px] md:h-[380px] border border-[#8B5CF6]/20 rounded-full"
        animate={{ rotate: -360 }}
        transition={{ duration: 25, repeat: Infinity, ease: "linear" }}
      >
        <div className="absolute bottom-4 right-1/4 w-1.5 h-1.5 bg-[#8B5CF6] rounded-full shadow-[0_0_8px_#8B5CF6]" />
      </motion.div>

      {/* Orbit 3: Wide Angle Ring */}
      <motion.div 
        className="absolute w-[320px] h-[100px] md:w-[400px] md:h-[120px] border border-double border-[#4D7CFF]/15 rounded-full"
        style={{ transform: "rotateX(70deg) rotateY(15deg)" }}
        animate={{ rotate: 360 }}
        transition={{ duration: 12, repeat: Infinity, ease: "linear" }}
      >
        <div className="absolute left-0 top-1/2 -translate-y-1/2 w-2 h-2 bg-[#4D7CFF] rounded-full shadow-[0_0_8px_#4D7CFF]" />
      </motion.div>

      {/* Holographic Subtle Rays & Floating Data Dots */}
      <div className="absolute inset-0 pointer-events-none overflow-hidden rounded-full">
        {/* Left Ray */}
        <div className="absolute top-1/4 left-10 w-[2px] h-32 bg-gradient-to-b from-transparent via-[#5FE8FF]/20 to-transparent rotate-[15deg] blur-[1px]" />
        {/* Right Ray */}
        <div className="absolute bottom-1/4 right-10 w-[2px] h-32 bg-gradient-to-b from-transparent via-[#8B5CF6]/20 to-transparent rotate-[-15deg] blur-[1px]" />
      </div>

    </div>
  );
}

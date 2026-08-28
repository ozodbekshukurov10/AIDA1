import React from 'react';
import { motion } from 'motion/react';
import NeuralNetwork from '../components/ai/NeuralNetwork';

export default function Intelligence() {
  return (
    <section className="relative min-h-screen bg-[#05070D] flex flex-col items-center justify-center overflow-hidden px-6 text-center z-10 select-none">
      
      {/* Fullscreen Interactive Attract-mode Neural Network */}
      <div className="absolute inset-0 z-0">
        <NeuralNetwork mode="attract" className="w-full h-full" />
      </div>

      {/* Cybernetic HUD layout overlays */}
      <div className="absolute top-10 left-10 text-[9px] font-mono text-[#F5F7FA]/20 tracking-[0.2em] pointer-events-none uppercase">
        System Status: EVOLVING // Matrix Core: 0x9F82
      </div>
      <div className="absolute bottom-10 right-10 text-[9px] font-mono text-[#F5F7FA]/20 tracking-[0.2em] pointer-events-none uppercase">
        Synaptic Density: 94.6% // Mode: Dynamic Attractor
      </div>

      {/* Center Copy Overlays */}
      <div className="max-w-2xl mx-auto flex flex-col items-center gap-6 relative z-10 pointer-events-none">
        
        <motion.div 
          initial={{ opacity: 0, scale: 0.9 }}
          whileInView={{ opacity: 1, scale: 1 }}
          viewport={{ once: true }}
          transition={{ duration: 0.8 }}
          className="flex items-center justify-center w-24 h-24 border border-[#5FE8FF]/10 bg-[#08111F]/30 backdrop-blur-md rounded-full shadow-[0_0_40px_rgba(95,232,255,0.05)]"
        >
          <div className="w-10 h-10">
            <svg viewBox="0 0 100 100" className="w-full h-full text-[#5FE8FF] filter drop-shadow-[0_0_8px_#5FE8FF] animate-pulse">
              <polygon points="50,15 85,35 85,75 50,95 15,75 15,35" fill="none" stroke="currentColor" strokeWidth="6" />
              <line x1="50" y1="15" x2="50" y2="95" stroke="currentColor" strokeWidth="6" strokeDasharray="6 6" />
            </svg>
          </div>
        </motion.div>

        <motion.h2 
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.8, delay: 0.1 }}
          className="font-['Space_Grotesk'] text-5xl sm:text-6xl md:text-7xl font-extrabold text-[#F5F7FA] tracking-[0.1em] uppercase filter drop-shadow-[0_0_20px_rgba(95,232,255,0.2)]"
        >
          AIDA
        </motion.h2>

        <motion.p 
          initial={{ opacity: 0, y: 15 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.8, delay: 0.2 }}
          className="font-['Space_Grotesk'] text-base sm:text-lg md:text-xl text-[#F5F7FA]/60 font-light tracking-wide max-w-md leading-relaxed"
        >
          Intelligence that evolves with you.
        </motion.p>
        
        <span className="text-[10px] font-mono text-[#5FE8FF]/40 tracking-[0.3em] uppercase mt-2 animate-pulse">
          Move cursor to interact with the neural net
        </span>

      </div>

      {/* Decorative HUD Corner Bracket elements */}
      <div className="absolute top-12 right-12 w-8 h-8 border-t border-r border-[#F5F7FA]/10 pointer-events-none" />
      <div className="absolute bottom-12 left-12 w-8 h-8 border-b border-l border-[#F5F7FA]/10 pointer-events-none" />

    </section>
  );
}

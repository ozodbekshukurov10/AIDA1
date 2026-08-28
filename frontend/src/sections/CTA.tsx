import React from 'react';
import { motion } from 'motion/react';
import NeuralNetwork from '../components/ai/NeuralNetwork';
import Button from '../components/ui/Button';
import AIDALogo from '../components/ui/AIDALogo';

interface CTAProps {
  onStart: () => void;
}

export default function CTA({ onStart }: CTAProps) {
  return (
    <section className="relative min-h-[90vh] bg-[#03050A] flex flex-col items-center justify-center overflow-hidden px-6 text-center z-10 select-none">
      
      {/* Fullscreen Interactive Attractor network */}
      <div className="absolute inset-0 z-0 opacity-25">
        <NeuralNetwork mode="attract" className="w-full h-full" />
      </div>

      {/* Radial lights overlaying the canvas */}
      <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[450px] h-[450px] bg-[#4C7DFF]/5 blur-[120px] rounded-full pointer-events-none" />
      <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[550px] h-[550px] bg-[#7C5CFF]/3 blur-[140px] rounded-full pointer-events-none animate-pulse" />

      <div className="max-w-3xl mx-auto flex flex-col items-center gap-6 relative z-10">
        
        {/* Core SVG abstract geometric AI symbol */}
        <div className="w-16 h-16 flex items-center justify-center rounded-2xl bg-white/[0.03] border border-white/8 mb-4 shadow-[0_0_20px_rgba(93,232,255,0.05)]">
          <AIDALogo size={30} strokeWidth={9} className="text-[#5DE8FF] filter drop-shadow-[0_0_8px_rgba(93,232,255,0.45)]" />
        </div>

        <motion.h2 
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.8 }}
          style={{ fontSize: 'clamp(2.2rem, 5.5vw, 3.8rem)' }}
          className="font-['Space_Grotesk'] font-extrabold text-[#F5F7FF] tracking-tight leading-tight max-w-2xl"
        >
          The future of intelligence starts here.
        </motion.h2>

        <motion.p 
          initial={{ opacity: 0, y: 15 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.8, delay: 0.15 }}
          className="text-base text-[#9CA9BC] font-light"
        >
          Meet <span className="text-[#5DE8FF] font-semibold">AIDA</span>.
        </motion.p>

        <motion.div 
          initial={{ opacity: 0, scale: 0.95 }}
          whileInView={{ opacity: 1, scale: 1 }}
          viewport={{ once: true }}
          transition={{ duration: 0.8, delay: 0.25 }}
          className="mt-6"
        >
          <Button variant="primary" onClick={onStart} className="px-10 py-5">
            Start with AIDA →
          </Button>
        </motion.div>

      </div>

      {/* HUD Corner borders */}
      <div className="absolute top-12 left-12 w-6 h-6 border-t border-l border-white/8 pointer-events-none" />
      <div className="absolute bottom-12 right-12 w-6 h-6 border-b border-r border-white/8 pointer-events-none" />

    </section>
  );
}

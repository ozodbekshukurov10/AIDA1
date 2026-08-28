import React from 'react';
import { motion } from 'motion/react';
import NeuralNetwork from '../components/ai/NeuralNetwork';
import AIDALogo from '../components/ui/AIDALogo';
import { Sparkles, ArrowRight, Zap, ShieldCheck } from 'lucide-react';

interface CTAProps {
  onStart: () => void;
}

export default function CTA({ onStart }: CTAProps) {
  return (
    <section className="relative min-h-[90vh] bg-[#03050A] flex flex-col items-center justify-center overflow-hidden px-6 py-20 text-center z-10 select-none">
      
      {/* â”€â”€ 1. Interactive Attractor Neural Mesh Canvas â”€â”€ */}
      <div className="absolute inset-0 z-0 opacity-30 pointer-events-none">
        <NeuralNetwork mode="attract" className="w-full h-full" />
      </div>

      {/* â”€â”€ 2. Ambient Radial Glow Aura Blobs â”€â”€ */}
      <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[600px] bg-[#5DE8FF]/10 blur-[160px] rounded-full pointer-events-none animate-pulse" />
      <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[700px] h-[700px] bg-[#7C5CFF]/10 blur-[180px] rounded-full pointer-events-none" />

      {/* â”€â”€ 3. Central Glassmorphism Card â”€â”€ */}
      <div className="max-w-4xl mx-auto flex flex-col items-center gap-8 relative z-10 p-10 md:p-16 rounded-3xl border border-white/10 bg-[#03050A]/80 backdrop-blur-2xl shadow-[0_0_60px_rgba(93,232,255,0.15)]">
        
        {/* Core AIDA Branding Logo Badge */}
        <motion.div
          initial={{ scale: 0.8, opacity: 0 }}
          whileInView={{ scale: 1, opacity: 1 }}
          viewport={{ once: true }}
          transition={{ duration: 0.8 }}
          className="relative w-20 h-20 flex items-center justify-center rounded-3xl bg-gradient-to-b from-[#5DE8FF]/20 to-[#7C5CFF]/20 border border-[#5DE8FF]/40 shadow-[0_0_30px_rgba(93,232,255,0.3)]"
        >
          <div className="absolute inset-0 rounded-3xl bg-[#5DE8FF]/20 animate-ping opacity-30" />
          <AIDALogo size={40} strokeWidth={9} className="text-[#5DE8FF] filter drop-shadow-[0_0_12px_rgba(93,232,255,0.6)]" />
        </motion.div>

        {/* Micro Status Badges */}
        <motion.div
          initial={{ opacity: 0, y: 15 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.8, delay: 0.1 }}
          className="flex flex-wrap items-center justify-center gap-3"
        >
          <span className="px-3.5 py-1 rounded-full bg-[#5DE8FF]/15 border border-[#5DE8FF]/30 text-[#5DE8FF] font-['JetBrains_Mono',monospace] text-xs font-bold uppercase tracking-widest flex items-center gap-1.5">
            <Sparkles className="w-3.5 h-3.5 animate-spin" /> AIDA 2.0 ONLINE
          </span>
          <span className="px-3.5 py-1 rounded-full bg-[#7C5CFF]/15 border border-[#7C5CFF]/30 text-[#7C5CFF] font-['JetBrains_Mono',monospace] text-xs font-bold uppercase tracking-widest flex items-center gap-1.5">
            <Zap className="w-3.5 h-3.5" /> 2M+ CONTEXT TOKENS
          </span>
          <span className="px-3.5 py-1 rounded-full bg-white/10 border border-white/20 text-white font-['JetBrains_Mono',monospace] text-xs font-bold uppercase tracking-widest flex items-center gap-1.5">
            <ShieldCheck className="w-3.5 h-3.5" /> 1.2ms SWARM SPEED
          </span>
        </motion.div>

        {/* Bold Headline */}
        <motion.h2 
          initial={{ opacity: 0, y: 20, filter: 'blur(10px)' }}
          whileInView={{ opacity: 1, y: 0, filter: 'blur(0px)' }}
          viewport={{ once: true }}
          transition={{ duration: 0.8, delay: 0.2 }}
          className="font-['Space_Grotesk'] font-black text-4xl sm:text-6xl md:text-7xl text-[#F5F7FF] tracking-tight leading-none uppercase max-w-3xl"
        >
          The future of intelligence starts here.
        </motion.h2>

        {/* Subtitle */}
        <motion.p 
          initial={{ opacity: 0, y: 15, filter: 'blur(8px)' }}
          whileInView={{ opacity: 1, y: 0, filter: 'blur(0px)' }}
          viewport={{ once: true }}
          transition={{ duration: 0.8, delay: 0.3 }}
          className="text-base sm:text-xl text-[#C4CEDF] font-light max-w-xl leading-relaxed"
        >
          AIDA 2.0 bilan kelajak loyihalaringizni 1,024 ta avtonom neyron agentlar va 2M+ kontekst sig'imi bilan boshlang.
        </motion.p>

        {/* Action Button */}
        <motion.div 
          initial={{ opacity: 0, scale: 0.9 }}
          whileInView={{ opacity: 1, scale: 1 }}
          viewport={{ once: true }}
          transition={{ duration: 0.8, delay: 0.4 }}
          className="mt-4"
        >
          <button
            type="button"
            onClick={onStart}
            className="group relative inline-flex items-center gap-3 px-10 py-4 rounded-full bg-gradient-to-r from-[#5DE8FF] via-[#4C7DFF] to-[#7C5CFF] text-[#03050A] font-['Space_Grotesk'] text-base font-bold tracking-wider hover:scale-105 shadow-[0_0_35px_rgba(93,232,255,0.4)] transition-all duration-300 cursor-pointer uppercase"
          >
            <span>Start with AIDA</span>
            <ArrowRight className="w-5 h-5 group-hover:translate-x-1 transition-transform" />
          </button>
        </motion.div>

      </div>

      {/* Futuristic Frame Corners */}
      <div className="absolute top-12 left-12 w-8 h-8 border-t-2 border-l-2 border-[#5DE8FF]/30 pointer-events-none" />
      <div className="absolute bottom-12 right-12 w-8 h-8 border-b-2 border-r-2 border-[#7C5CFF]/30 pointer-events-none" />

    </section>
  );
}

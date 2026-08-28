import React from 'react';
import { motion } from 'motion/react';
import AnimatedHeaderCanvas from '../components/intro/AnimatedHeaderCanvas';
import Button from '../components/ui/Button';

interface HeroProps {
  onStart: () => void;
  onExplore: () => void;
  morphFromIntro?: boolean;
}

export default function Hero({ onStart, onExplore, morphFromIntro = false }: HeroProps) {
  return (
    <section
      id="hero"
      className="relative min-h-screen bg-[#03050A] flex flex-col items-center justify-center overflow-hidden pt-28 pb-16 px-6 md:px-12 z-10 select-none"
    >
      {/* â”€â”€ 1. Animated Header Canvas Background (from AnimatedHeaderBackgrounds) â”€â”€ */}
      <AnimatedHeaderCanvas />

      {/* â”€â”€ 2. Ambient background video & gradient overlay â”€â”€ */}
      <div className="absolute inset-0 pointer-events-none z-0 overflow-hidden opacity-25">
        <video
          autoPlay
          muted
          loop
          playsInline
          className="w-full h-full object-cover"
          style={{ filter: 'blur(2px) saturate(0.8) brightness(0.4)' }}
        >
          <source src="/bg-video.mp4" type="video/mp4" />
        </video>
        <div className="absolute inset-0 bg-gradient-to-b from-[#03050A] via-transparent to-[#03050A]" />
      </div>

      {/* â”€â”€ 3. Main Central Hero Title & AIDA Branding â”€â”€ */}
      <div className="max-w-4xl mx-auto flex flex-col items-center text-center gap-8 relative z-10">
        
        {/* Micro Status Badge */}
        <motion.div
          initial={{ opacity: 0, y: -15 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8, ease: "easeOut" }}
          className="flex items-center gap-2.5 px-4 py-1.5 bg-[#5DE8FF]/10 border border-[#5DE8FF]/25 rounded-full shadow-[0_0_15px_rgba(93,232,255,0.2)]"
        >
          <span className="w-2 h-2 bg-[#5DE8FF] rounded-full animate-ping" />
          <span className="font-['JetBrains_Mono',monospace] text-xs tracking-[0.3em] text-[#5DE8FF] uppercase font-bold">
            AIDA 2.0 // NEURAL ENGINE ONLINE
          </span>
        </motion.div>

        {/* BOLD AIDA HEADLINE */}
        <motion.h1
          initial={{ opacity: 0, scale: 0.88, filter: 'blur(10px)' }}
          animate={{ opacity: 1, scale: 1, filter: 'blur(0px)' }}
          transition={{ duration: 1.0, delay: 0.15, ease: [0.16, 1, 0.3, 1] }}
          className="font-['Space_Grotesk',sans-serif] font-black text-6xl sm:text-8xl md:text-9xl text-[#F5F7FF] tracking-widest uppercase leading-none drop-shadow-[0_0_35px_rgba(93,232,255,0.35)]"
        >
          A I D A
        </motion.h1>

        {/* Subtitle */}
        <motion.p
          initial={{ opacity: 0, y: 15 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8, delay: 0.35 }}
          className="text-base sm:text-xl md:text-2xl font-light text-[#C4CEDF] max-w-2xl leading-relaxed font-sans"
        >
          Autonomous Cognitive Intelligence & Multi-Model Swarm Collaboration
        </motion.p>

        {/* Feature Tags */}
        <motion.div
          initial={{ opacity: 0, y: 15 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8, delay: 0.45 }}
          className="flex flex-wrap justify-center gap-3 font-['JetBrains_Mono',monospace] text-xs text-[#5DE8FF]/80"
        >
          {['Context-First Reasoning', 'Self-Healing Shield', 'Web Search RAG', 'Infinite Vector Memory'].map((tag) => (
            <span key={tag} className="px-3.5 py-1.5 rounded-full border border-[#5DE8FF]/20 bg-[#5DE8FF]/5 backdrop-blur-md">
              {tag}
            </span>
          ))}
        </motion.div>

        {/* CTA Actions */}
        <motion.div
          initial={{ opacity: 0, y: 15 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8, delay: 0.55 }}
          className="flex flex-row items-center gap-4 mt-2"
        >
          <Button variant="primary" onClick={onStart}>
            Start with AIDA â†’
          </Button>
          <Button variant="secondary" onClick={onExplore}>
            Explore AI HUD
          </Button>
        </motion.div>

      </div>

      {/* Downward Scroll Indicator */}
      <motion.div
        animate={{ y: [0, 8, 0] }}
        transition={{ duration: 2, repeat: Infinity, ease: 'easeInOut' }}
        className="absolute bottom-6 left-1/2 -translate-x-1/2 flex flex-col items-center gap-2 text-[#9CA9BC]/40 pointer-events-none select-none"
      >
        <span className="font-['JetBrains_Mono',monospace] text-[10px] tracking-[0.3em] uppercase">
          Scroll for 3D Morphing Showcase
        </span>
        <div className="w-1.5 h-4 bg-[#5DE8FF]/30 rounded-full" />
      </motion.div>

    </section>
  );
}

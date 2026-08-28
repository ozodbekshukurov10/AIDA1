import React from 'react';
import { motion } from 'motion/react';
import AnimatedHeaderCanvas from '../components/intro/AnimatedHeaderCanvas';
import Button from '../components/ui/Button';

interface HeroProps {
  onStart: () => void;
  onExplore: () => void;
  onOpenContext?: () => void;
  morphFromIntro?: boolean;
}

export default function Hero({ onStart, onExplore, onOpenContext, morphFromIntro = false }: HeroProps) {
  return (
    <section
      id="hero"
      className="relative min-h-screen bg-[#03050A] flex flex-col items-center justify-center overflow-hidden pt-28 pb-16 px-6 md:px-12 z-10 select-none"
    >
      {/* ÃƒÂ¢â‚¬-â€šÂ¬ÃƒÂ¢â‚¬-â€šÂ¬ 1. Ambient Pulsing Radial Blur Glow Blobs ÃƒÂ¢â‚¬-â€šÂ¬ÃƒÂ¢â‚¬-â€šÂ¬ */}
      <div className="absolute w-[650px] h-[650px] bg-[#5DE8FF]/8 blur-[180px] rounded-full pointer-events-none animate-pulse" />
      <div className="absolute w-[500px] h-[500px] bg-[#7C5CFF]/8 blur-[150px] rounded-full pointer-events-none" />

      {/* ÃƒÂ¢â‚¬-â€šÂ¬ÃƒÂ¢â‚¬-â€šÂ¬ 2. Animated Header Canvas Background (from AnimatedHeaderBackgrounds) ÃƒÂ¢â‚¬-â€šÂ¬ÃƒÂ¢â‚¬-â€šÂ¬ */}
      <AnimatedHeaderCanvas />

      {/* ÃƒÂ¢â‚¬-â€šÂ¬ÃƒÂ¢â‚¬-â€šÂ¬ 3. Ambient background video & gradient overlay ÃƒÂ¢â‚¬-â€šÂ¬ÃƒÂ¢â‚¬-â€šÂ¬ */}
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

      {/* ÃƒÂ¢â‚¬-â€šÂ¬ÃƒÂ¢â‚¬-â€šÂ¬ 4. Main Central Hero Title & AIDA Branding (Pure Minimalist + Blur Animation) ÃƒÂ¢â‚¬-â€šÂ¬ÃƒÂ¢â‚¬-â€šÂ¬ */}
      <div className="max-w-4xl mx-auto flex flex-col items-center text-center gap-8 relative z-10">
        
        {/* Micro Status Badge */}
        <motion.div
          initial={{ opacity: 0, y: -15, filter: 'blur(10px)' }}
          animate={{ opacity: 1, y: 0, filter: 'blur(0px)' }}
          transition={{ duration: 0.8, ease: "easeOut" }}
          className="flex items-center gap-2.5 px-4 py-1.5 bg-[#5DE8FF]/10 border border-[#5DE8FF]/25 rounded-full shadow-[0_0_20px_rgba(93,232,255,0.25)]"
        >
          <span className="w-2 h-2 bg-[#5DE8FF] rounded-full animate-ping" />
          <span className="font-['JetBrains_Mono',monospace] text-xs tracking-[0.3em] text-[#5DE8FF] uppercase font-bold">
            AIDA 2.0 // NEURAL ENGINE ONLINE
          </span>
        </motion.div>

        {/* BOLD AIDA HEADLINE (WITH SMOOTH BLUR REVEAL ANIMATION) */}
        <motion.h1
          initial={{ opacity: 0, scale: 0.8, filter: 'blur(30px)' }}
          animate={{ opacity: 1, scale: 1, filter: 'blur(0px)' }}
          transition={{ duration: 1.4, delay: 0.15, ease: [0.16, 1, 0.3, 1] }}
          className="font-['Space_Grotesk',sans-serif] font-black text-7xl sm:text-9xl md:text-[10rem] text-[#F5F7FF] tracking-widest uppercase leading-none filter drop-shadow-[0_0_45px_rgba(93,232,255,0.45)]"
        >
          A I D A
        </motion.h1>

        {/* Minimalist Subtitle */}
        <motion.p
          initial={{ opacity: 0, y: 15, filter: 'blur(12px)' }}
          animate={{ opacity: 1, y: 0, filter: 'blur(0px)' }}
          transition={{ duration: 1.0, delay: 0.35, ease: [0.16, 1, 0.3, 1] }}
          className="text-lg sm:text-2xl md:text-3xl font-light text-[#C4CEDF] max-w-xl leading-relaxed font-sans"
        >
          Sun'iy Ong va Avtonom Intellekt Tizimi
        </motion.p>

        {/* Sleek CTA Actions (Matching media_1787942471001.png 100% exactly) */}
        <motion.div
          initial={{ opacity: 0, y: 15, filter: 'blur(10px)' }}
          animate={{ opacity: 1, y: 0, filter: 'blur(0px)' }}
          transition={{ duration: 0.8, delay: 0.5, ease: [0.16, 1, 0.3, 1] }}
          className="flex flex-wrap items-center justify-center gap-4 mt-2"
        >
          <Button variant="primary" onClick={onStart}>
            Start with AIDA â€ â€™
          </Button>
          {onOpenContext && (
            <Button variant="secondary" onClick={onOpenContext}>
              <span>Å¸Â§Â </span> AIDA Context
            </Button>
          )}
          <Button variant="ghost" onClick={onExplore}>
            Explore 3D World
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
          Scroll for 3D Kinetic Showcase
        </span>
        <div className="w-1.5 h-4 bg-[#5DE8FF]/30 rounded-full" />
      </motion.div>

    </section>
  );
}

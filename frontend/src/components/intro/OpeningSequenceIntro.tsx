import React, { useEffect, useState } from 'react';
import { motion, AnimatePresence } from 'motion/react';

interface OpeningSequenceIntroProps {
  onComplete: () => void;
}

const PHRASES = [
  { text: "KELAJAK CHEGARASIDA", subtitle: "At the Frontier of Consciousness", duration: 4200, isMain: false },
  { text: "SUN'IY INTELLEKT TAFAKKURI", subtitle: "Cognition & Neural Synthesis", duration: 4200, isMain: false },
  { text: "CHEKSIZ IMKONIYATLAR UYG'UNLIGI", subtitle: "Harmony of Infinite Potential", duration: 4200, isMain: false },
  { text: "O'Z-O'ZINI ANGLOVCHI TIZIM", subtitle: "Autonomous Self-Architecting Intelligence", duration: 4200, isMain: false },
  { 
    text: "A I D A   2 . 0", 
    subtitle: "Inson ongi va sun'iy intellektning mukammal uyg'unligi",
    duration: 8500, // Extended duration for a breathtaking emotional feel
    isMain: true 
  },
  { text: "SUN'IY ONG DUNYOSIGA XUSH KELIBSIZ", subtitle: "Welcome to the World of Artificial Intelligence", duration: 4500, isMain: false },
];

export default function OpeningSequenceIntro({ onComplete }: OpeningSequenceIntroProps) {
  const [currentPhraseIndex, setCurrentPhraseIndex] = useState(0);

  useEffect(() => {
    // Lock body scroll when intro is active
    document.body.style.overflow = 'hidden';

    const currentPhrase = PHRASES[currentPhraseIndex];
    
    let timer: NodeJS.Timeout;

    if (currentPhraseIndex < PHRASES.length - 1) {
      timer = setTimeout(() => {
        setCurrentPhraseIndex((prev) => prev + 1);
      }, currentPhrase.duration);
    } else {
      timer = setTimeout(() => {
        document.body.style.overflow = '';
        onComplete();
      }, currentPhrase.duration);
    }

    return () => {
      clearTimeout(timer);
    };
  }, [currentPhraseIndex, onComplete]);

  const activePhrase = PHRASES[currentPhraseIndex];

  const handleSkipClick = () => {
    document.body.style.overflow = '';
    onComplete();
  };

  return (
    <div className="fixed inset-0 w-screen h-screen z-[99999] bg-[#020409] flex items-center justify-center overflow-hidden select-none font-sans">
      
      {/* â”€â”€ 1. Ambient Pulsing Radial Glow Nebula â”€â”€ */}
      <div className="absolute w-[800px] h-[800px] bg-[#5DE8FF]/10 blur-[200px] rounded-full pointer-events-none animate-pulse" />
      <div className="absolute w-[600px] h-[600px] bg-[#7C5CFF]/10 blur-[170px] rounded-full pointer-events-none" />

      {/* â”€â”€ 2. Fullscreen Ambient Video Backdrop â”€â”€ */}
      <div className="absolute inset-0 w-full h-full pointer-events-none z-0 overflow-hidden opacity-45">
        <video
          autoPlay
          muted
          loop
          playsInline
          className="w-full h-full object-cover"
          style={{ filter: 'blur(2px) saturate(0.85) brightness(0.45)' }}
        >
          <source src="/bg-video.mp4" type="video/mp4" />
        </video>
        <div className="absolute inset-0 bg-gradient-to-b from-[#020409]/90 via-[#020409]/50 to-[#020409]/95" />
      </div>

      {/* â”€â”€ 3. Top Bar Controls â”€â”€ */}
      <div className="absolute top-8 right-10 z-[100000] flex items-center gap-4">
        <button
          type="button"
          onClick={handleSkipClick}
          className="px-5 py-2.5 rounded-full border border-[#5DE8FF]/40 bg-[#5DE8FF]/15 text-[#5DE8FF] font-['JetBrains_Mono',monospace] text-xs font-bold tracking-widest hover:bg-[#5DE8FF]/30 hover:border-[#5DE8FF] transition-all duration-300 cursor-pointer shadow-[0_0_20px_rgba(93,232,255,0.3)]"
        >
          SKIP INTRO â†’
        </button>
      </div>

      {/* â”€â”€ 4. Central OpeningSequence 3D Typography Render â”€â”€ */}
      <div className="relative z-10 max-w-6xl w-full px-6 text-center flex flex-col items-center justify-center">
        <AnimatePresence mode="wait">
          {activePhrase.isMain ? (
            /* â”€â”€ DEDICATED SLOW & EMOTIONAL REVEAL FOR "A I D A 2.0" â”€â”€ */
            <motion.div
              key="aida-main-stage"
              initial={{ opacity: 0, scale: 0.5, filter: 'blur(40px)', letterSpacing: '1.2em' }}
              animate={{ opacity: 1, scale: 1.05, filter: 'blur(0px)', letterSpacing: '0.5em' }}
              exit={{ opacity: 0, scale: 1.3, filter: 'blur(30px)', letterSpacing: '1.4em' }}
              transition={{ duration: 2.8, ease: [0.16, 1, 0.3, 1] }}
              className="flex flex-col items-center gap-8 w-full relative"
            >
              {/* Pulsing Core Light Ring behind AIDA 2.0 */}
              <motion.div
                initial={{ scale: 0, opacity: 0 }}
                animate={{ scale: [0.8, 1.3, 1.05], opacity: [0.2, 0.6, 0.4] }}
                transition={{ duration: 3.5, repeat: Infinity, ease: 'easeInOut' }}
                className="absolute w-[450px] h-[450px] rounded-full border border-[#5DE8FF]/30 bg-gradient-to-r from-[#5DE8FF]/15 via-[#4C7DFF]/15 to-[#7C5CFF]/15 blur-2xl pointer-events-none"
              />

              {/* Aesthetic Light Beam Line */}
              <motion.div
                initial={{ width: 0, opacity: 0 }}
                animate={{ width: '280px', opacity: 1 }}
                transition={{ duration: 2.0, delay: 0.5 }}
                className="h-[2px] bg-gradient-to-r from-transparent via-[#5DE8FF] to-transparent shadow-[0_0_20px_#5DE8FF]"
              />

              {/* BREATHTAKING SLOW "A I D A 2.0" HEADLINE */}
              <h1 className="font-['Space_Grotesk',sans-serif] font-black text-6xl sm:text-8xl md:text-[9.5rem] uppercase leading-none tracking-widest text-transparent bg-clip-text bg-gradient-to-r from-[#5DE8FF] via-[#4C7DFF] to-[#7C5CFF] filter drop-shadow-[0_0_60px_rgba(93,232,255,0.75)]">
                A I D A   2 . 0
              </h1>

              {/* Deep Emotional Subtitle Statement */}
              <motion.p
                initial={{ opacity: 0, y: 20, filter: 'blur(15px)' }}
                animate={{ opacity: 1, y: 0, filter: 'blur(0px)' }}
                transition={{ duration: 1.8, delay: 1.2, ease: [0.16, 1, 0.3, 1] }}
                className="text-lg sm:text-2xl md:text-3xl font-light text-[#F5F7FF]/90 font-sans max-w-3xl leading-relaxed tracking-wide drop-shadow-[0_0_15px_rgba(255,255,255,0.3)]"
              >
                {activePhrase.subtitle}
              </motion.p>

              {/* Technical Subline */}
              <motion.span
                initial={{ opacity: 0 }}
                animate={{ opacity: 0.7 }}
                transition={{ duration: 1.2, delay: 2.0 }}
                className="font-['JetBrains_Mono',monospace] text-xs md:text-sm tracking-[0.4em] text-[#5DE8FF] uppercase"
              >
                AUTONOMOUS NEURAL SYNAPSE // OPERATIONAL
              </motion.span>
            </motion.div>
          ) : (
            /* â”€â”€ STANDARD STAGE REVEAL â”€â”€ */
            <motion.div
              key={currentPhraseIndex}
              initial={{ opacity: 0, scale: 0.75, rotateX: -45, filter: 'blur(20px)', letterSpacing: '0.7em' }}
              animate={{ opacity: 1, scale: 1, rotateX: 0, filter: 'blur(0px)', letterSpacing: '0.25em' }}
              exit={{ opacity: 0, scale: 1.2, rotateX: 30, filter: 'blur(15px)', letterSpacing: '0.8em' }}
              transition={{ duration: 1.4, ease: [0.16, 1, 0.3, 1] }}
              className="flex flex-col items-center gap-6 w-full"
            >
              {/* Aesthetic Glow Line */}
              <motion.div
                initial={{ width: 0 }}
                animate={{ width: '160px' }}
                transition={{ duration: 1.0 }}
                className="h-[2px] bg-gradient-to-r from-transparent via-[#5DE8FF] to-transparent shadow-[0_0_15px_#5DE8FF]"
              />

              {/* Typography Heading */}
              <h1 className="font-['Space_Grotesk',sans-serif] font-black uppercase text-center leading-none tracking-widest text-3xl sm:text-5xl md:text-7xl text-[#F5F7FF] drop-shadow-[0_0_25px_rgba(93,232,255,0.4)]">
                {activePhrase.text}
              </h1>

              {/* Aesthetic Subline */}
              <span className="font-['JetBrains_Mono',monospace] text-xs md:text-sm tracking-[0.35em] text-[#5DE8FF]/80 uppercase font-semibold">
                {activePhrase.subtitle}
              </span>
            </motion.div>
          )}
        </AnimatePresence>
      </div>

      {/* Bottom Progress Bar */}
      <div className="absolute bottom-10 left-1/2 -translate-x-1/2 w-80 h-[3px] bg-white/10 rounded-full overflow-hidden">
        <motion.div
          initial={{ width: '0%' }}
          animate={{ width: '100%' }}
          transition={{ duration: 30, ease: 'linear' }}
          className="h-full bg-gradient-to-r from-[#5DE8FF] via-[#4C7DFF] to-[#7C5CFF] shadow-[0_0_12px_#5DE8FF]"
        />
      </div>

    </div>
  );
}

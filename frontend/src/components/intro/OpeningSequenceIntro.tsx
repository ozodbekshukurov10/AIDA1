import React, { useEffect, useState } from 'react';
import { motion, AnimatePresence } from 'motion/react';

interface OpeningSequenceIntroProps {
  onComplete: () => void;
}

const PHRASES = [
  { text: "KELAJAK CHEGARASIDA", isMain: false },
  { text: "SUN'IY INTELLEKT TAFAKKURI", isMain: false },
  { text: "CHEKSIZ IMKONIYATLAR UYG'UNLIGI", isMain: false },
  { text: "O'Z-O'ZINI ANGLOVCHI TIZIM", isMain: false },
  { text: "A I D A  2 . 0", isMain: true },
  { text: "SUN'IY ONG DUNYOSIGA XUSH KELIBSIZ", isMain: false },
];

export default function OpeningSequenceIntro({ onComplete }: OpeningSequenceIntroProps) {
  const [currentPhraseIndex, setCurrentPhraseIndex] = useState(0);

  useEffect(() => {
    // Lock body scroll when intro is open
    document.body.style.overflow = 'hidden';

    const totalTimer = setTimeout(() => {
      document.body.style.overflow = '';
      onComplete();
    }, 27000);

    const interval = setInterval(() => {
      setCurrentPhraseIndex((prev) => {
        if (prev < PHRASES.length - 1) return prev + 1;
        clearInterval(interval);
        return prev;
      });
    }, 4300);

    return () => {
      document.body.style.overflow = '';
      clearTimeout(totalTimer);
      clearInterval(interval);
    };
  }, [onComplete]);

  const activePhrase = PHRASES[currentPhraseIndex];

  const handleSkipClick = () => {
    document.body.style.overflow = '';
    onComplete();
  };

  return (
    <div className="fixed inset-0 w-screen h-screen z-[99999] bg-[#020409] flex items-center justify-center overflow-hidden select-none font-sans">
      
      {/* â”€â”€ 1. Fullscreen Ambient Video Backdrop â”€â”€ */}
      <div className="absolute inset-0 w-full h-full pointer-events-none z-0 overflow-hidden opacity-50">
        <video
          autoPlay
          muted
          loop
          playsInline
          className="w-full h-full object-cover"
          style={{ filter: 'blur(2px) saturate(0.8) brightness(0.45)' }}
        >
          <source src="/bg-video.mp4" type="video/mp4" />
        </video>
        <div className="absolute inset-0 bg-gradient-to-b from-[#020409]/90 via-[#020409]/60 to-[#020409]/95" />
      </div>

      {/* â”€â”€ 2. Top Bar Controls â”€â”€ */}
      <div className="absolute top-8 right-10 z-[100000] flex items-center gap-4">
        <button
          type="button"
          onClick={handleSkipClick}
          className="px-5 py-2.5 rounded-full border border-[#5DE8FF]/40 bg-[#5DE8FF]/15 text-[#5DE8FF] font-['JetBrains_Mono',monospace] text-xs font-bold tracking-widest hover:bg-[#5DE8FF]/30 hover:border-[#5DE8FF] transition-all duration-300 cursor-pointer shadow-[0_0_20px_rgba(93,232,255,0.3)]"
        >
          SKIP INTRO â†’
        </button>
      </div>

      {/* â”€â”€ 3. Central OpeningSequence 3D Typography Render â”€â”€ */}
      <div className="relative z-10 max-w-6xl w-full px-6 text-center flex flex-col items-center justify-center">
        <AnimatePresence mode="wait">
          <motion.div
            key={currentPhraseIndex}
            initial={{ opacity: 0, scale: 0.7, rotateX: -60, filter: 'blur(20px)', letterSpacing: '0.8em' }}
            animate={{ opacity: 1, scale: 1, rotateX: 0, filter: 'blur(0px)', letterSpacing: activePhrase.isMain ? '0.4em' : '0.25em' }}
            exit={{ opacity: 0, scale: 1.3, rotateX: 45, filter: 'blur(15px)', letterSpacing: '0.9em' }}
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
            <h1
              className={`font-['Space_Grotesk',sans-serif] font-black uppercase text-center leading-none tracking-widest ${
                activePhrase.isMain
                  ? 'text-6xl sm:text-8xl md:text-9xl text-transparent bg-clip-text bg-gradient-to-r from-[#5DE8FF] via-[#4C7DFF] to-[#7C5CFF] filter drop-shadow-[0_0_50px_rgba(93,232,255,0.6)]'
                  : 'text-3xl sm:text-5xl md:text-7xl text-[#F5F7FF] drop-shadow-[0_0_25px_rgba(93,232,255,0.4)]'
              }`}
            >
              {activePhrase.text}
            </h1>

            {/* Aesthetic Subline */}
            <span className="font-['JetBrains_Mono',monospace] text-xs md:text-sm tracking-[0.35em] text-[#5DE8FF]/80 uppercase font-semibold">
              AIDA CINEMATIC OPENING // STAGE 0{currentPhraseIndex + 1}
            </span>
          </motion.div>
        </AnimatePresence>
      </div>

      {/* Bottom Progress Bar */}
      <div className="absolute bottom-10 left-1/2 -translate-x-1/2 w-72 h-[3px] bg-white/10 rounded-full overflow-hidden">
        <motion.div
          initial={{ width: '0%' }}
          animate={{ width: '100%' }}
          transition={{ duration: 27, ease: 'linear' }}
          className="h-full bg-gradient-to-r from-[#5DE8FF] via-[#4C7DFF] to-[#7C5CFF] shadow-[0_0_12px_#5DE8FF]"
        />
      </div>

    </div>
  );
}

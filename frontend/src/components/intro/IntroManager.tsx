import React, { useEffect, useState, useRef } from 'react';
import { motion, AnimatePresence } from 'motion/react';
import IntroScene from './IntroScene';
import StoryText from './StoryText';
import AIDALogoReveal from './AIDALogoReveal';
import ProductReveal from './ProductReveal';
import IntroTransition from './IntroTransition';
import VirtualBrainExperience from './VirtualBrainExperience';

interface IntroManagerProps {
  onComplete: () => void;
}

/**
 * Phase timeline:
 *   0  →  0–3s   Black opening
 *   1  →  3–6s   AIDA Logo Reveal
 *   2  →  6–9s   Story Text
 *   3  →  9–12s  "AIDA Connects It All"
 *   4  → 12–15s  AI Core title
 *   5  → 15–20s  Virtual Brain — brain map emerges
 *   6  → 20–25s  Virtual Brain — Input / Context
 *   7  → 25–30s  Virtual Brain — Reasoning
 *   8  → 30–35s  Virtual Brain — Tools & Memory
 *   9  → 35–40s  Virtual Brain — Verification
 *  10  → 40–45s  Virtual Brain — Brain Map + What makes AIDA different
 *  11  → 45–50s  Virtual Brain — Final message + Intelligence Loop
 *  12  → 50–53s  Product Reveal
 *  13  → 53–55s  Intro Transition → Hero
 */

export default function IntroManager({ onComplete }: IntroManagerProps) {
  const [isPreloading, setIsPreloading] = useState(true);
  const [preloadProgress, setPreloadProgress] = useState(0);
  const [phase, setPhase] = useState(0);
  const [elapsedTime, setElapsedTime] = useState(0);
  const [isSkipped, setIsSkipped] = useState(false);
  const [isReducedMotion, setIsReducedMotion] = useState(false);

  const startTimeRef = useRef<number | null>(null);
  const animFrameRef = useRef<number | null>(null);

  // Sound-ready event hooks architecture
  const triggers = {
    onParticleActivate:  () => console.log('[AIDA AUDIO EVENT] onParticleActivate'),
    onLogoReveal:        () => console.log('[AIDA AUDIO EVENT] onLogoReveal'),
    onTextReveal:        () => console.log('[AIDA AUDIO EVENT] onTextReveal'),
    onCoreActivate:      () => console.log('[AIDA AUDIO EVENT] onCoreActivate'),
    onBrainReveal:       () => console.log('[AIDA AUDIO EVENT] onBrainReveal'),
    onModuleActivate:    () => console.log('[AIDA AUDIO EVENT] onModuleActivate'),
    onLoopStart:         () => console.log('[AIDA AUDIO EVENT] onLoopStart'),
    onAIResponse:        () => console.log('[AIDA AUDIO EVENT] onAIResponse'),
    onFinalTransition:   () => console.log('[AIDA AUDIO EVENT] onFinalTransition'),
  };

  // Preloader 2.0 micro-initialization routine
  useEffect(() => {
    const seen = sessionStorage.getItem('aida_intro_seen');
    if (seen === 'true') {
      onComplete();
      return;
    }

    let current = 0;
    const interval = setInterval(() => {
      current += 25;
      setPreloadProgress(current);
      if (current >= 100) {
        clearInterval(interval);
        setTimeout(() => setIsPreloading(false), 200);
      }
    }, 180);

    return () => clearInterval(interval);
  }, []);

  useEffect(() => {
    if (isPreloading) return;

    const mediaQuery = window.matchMedia('(prefers-reduced-motion: reduce)');
    setIsReducedMotion(mediaQuery.matches);

    triggers.onParticleActivate();

    const tick = (timestamp: number) => {
      if (!startTimeRef.current) startTimeRef.current = timestamp;

      const elapsed = (timestamp - startTimeRef.current) / 1000;
      setElapsedTime(elapsed);

      if (isReducedMotion) {
        // Reduced-motion fast path
        if      (elapsed < 1.5) setPhase(1);
        else if (elapsed < 3.5) setPhase(2);
        else if (elapsed < 5.0) setPhase(12);
        else { handleIntroFinish(); return; }
      } else {
        // Full cinematic timeline
        if      (elapsed < 3.0)  { if (phase !== 0)  setPhase(0); }
        else if (elapsed < 6.0)  { if (phase !== 1)  { setPhase(1);  triggers.onLogoReveal(); } }
        else if (elapsed < 9.0)  { if (phase !== 2)  { setPhase(2);  triggers.onTextReveal(); } }
        else if (elapsed < 12.0) { if (phase !== 3)  setPhase(3); }
        else if (elapsed < 15.0) { if (phase !== 4)  { setPhase(4);  triggers.onCoreActivate(); } }
        else if (elapsed < 20.0) { if (phase !== 5)  { setPhase(5);  triggers.onBrainReveal(); } }
        else if (elapsed < 25.0) { if (phase !== 6)  { setPhase(6);  triggers.onModuleActivate(); } }
        else if (elapsed < 30.0) { if (phase !== 7)  { setPhase(7);  triggers.onModuleActivate(); } }
        else if (elapsed < 35.0) { if (phase !== 8)  { setPhase(8);  triggers.onModuleActivate(); } }
        else if (elapsed < 40.0) { if (phase !== 9)  { setPhase(9);  triggers.onModuleActivate(); } }
        else if (elapsed < 45.0) { if (phase !== 10) { setPhase(10); triggers.onModuleActivate(); } }
        else if (elapsed < 50.0) { if (phase !== 11) { setPhase(11); triggers.onLoopStart(); } }
        else {
          // Phase 12 Hold: Wait for user to click START button!
          if (phase < 12) {
            setPhase(12);
            triggers.onAIResponse();
          }
        }
      }

      animFrameRef.current = requestAnimationFrame(tick);
    };

    animFrameRef.current = requestAnimationFrame(tick);

    return () => {
      if (animFrameRef.current) cancelAnimationFrame(animFrameRef.current);
    };
  }, [isPreloading, isReducedMotion]);

  const handleIntroFinish = () => {
    sessionStorage.setItem('aida_intro_seen', 'true');
    onComplete();
  };

  const handleStartClick = () => {
    setPhase(13);
    triggers.onFinalTransition();
    setTimeout(() => {
      handleIntroFinish();
    }, 1400);
  };

  const handleSkip = () => {
    setIsSkipped(true);
    setPhase(13);
    triggers.onFinalTransition();

    setTimeout(() => {
      handleIntroFinish();
    }, 1000);
  };

  if (isSkipped && phase !== 13) return null;

  const isBrainPhase = phase >= 5 && phase <= 10;

  return (
    <div className="fixed inset-0 w-screen h-screen z-[9999] bg-[#03050A] text-[#F5F7FF] overflow-hidden select-none">
      
      {/* Preloader 2.0 HUD Overlay */}
      <AnimatePresence>
        {isPreloading && (
          <motion.div
            initial={{ opacity: 1 }}
            exit={{ opacity: 0, filter: "blur(10px)" }}
            transition={{ duration: 0.6 }}
            className="absolute inset-0 flex flex-col items-center justify-center bg-[#03050A] z-50 font-mono"
          >
            <div className="flex flex-col items-start gap-2 w-64">
              <div className="text-xs text-[#5DE8FF] tracking-[0.25em] uppercase font-semibold">
                INITIALIZING AIDA
              </div>
              <div className="w-full bg-[#07101A] h-1 rounded-full overflow-hidden border border-[#5DE8FF]/20">
                <motion.div
                  className="bg-gradient-to-r from-[#5DE8FF] to-[#7C5CFF] h-full"
                  style={{ width: `${preloadProgress}%` }}
                />
              </div>
              <div className="flex justify-between w-full text-[10px] text-[#F5F7FF]/40 mt-1">
                <span>Neural System</span>
                <span className="text-[#5DE8FF]">{preloadProgress}%</span>
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* 3D WebGL Canvas Scene */}
      <IntroScene 
        phase={phase} 
        time={elapsedTime} 
        isReducedMotion={isReducedMotion} 
      />

      {/* Skip Intro Control */}
      <AnimatePresence>
        {!isPreloading && phase < 13 && (
          <motion.button
            type="button"
            onClick={handleSkip}
            initial={{ opacity: 0 }}
            animate={{ opacity: 0.6 }}
            exit={{ opacity: 0 }}
            whileHover={{ opacity: 1, textShadow: "0 0 8px rgba(93,232,255,0.6)" }}
            className="absolute top-8 right-8 z-50 font-mono text-[10px] md:text-xs tracking-[0.2em] text-[#5DE8FF] uppercase cursor-pointer py-2 px-4 border border-[#5DE8FF]/15 rounded-full bg-[#03050A]/40 backdrop-blur-md transition-all duration-300 hover:border-[#5DE8FF]/40 pointer-events-auto"
          >
            Skip Intro &rarr;
          </motion.button>
        )}
      </AnimatePresence>

      {/* ─── Phase 1, 12 & 13: AIDA Logo Reveals & Wordmark Fly-Through Transition ─── */}
      <AIDALogoReveal active={!isPreloading && (phase === 1 || phase === 12 || phase === 13)} phase={phase} onStartClick={handleStartClick} />
      <StoryText active={!isPreloading && phase === 2} />

      <AnimatePresence>
        {!isPreloading && phase === 3 && (
          <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            exit={{ opacity: 0, filter: "blur(8px)" }}
            transition={{ duration: 1.0 }}
            className="absolute inset-0 flex items-center justify-center bg-transparent z-25 pl-[0.1em]"
          >
            <h2 className="font-['Space_Grotesk'] text-3xl md:text-5xl lg:text-6xl font-bold tracking-[0.1em] text-[#F5F7FF] text-center">
              BUT <span className="text-[#5DE8FF] filter drop-shadow-[0_0_12px_rgba(93,232,255,0.4)]">AIDA</span> CONNECTS IT ALL.
            </h2>
          </motion.div>
        )}
      </AnimatePresence>

      <AnimatePresence>
        {!isPreloading && phase === 4 && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.8 }}
            className="absolute inset-0 flex flex-col items-center justify-between py-24 z-25 bg-transparent"
          >
            <div className="font-['Space_Grotesk'] text-4xl md:text-5xl font-extrabold text-[#F5F7FF] tracking-[0.15em] pl-[0.15em] drop-shadow-[0_0_20px_rgba(255,255,255,0.1)]">
              AIDA
            </div>
            <motion.div
              initial={{ opacity: 0, y: 15 }}
              animate={{ opacity: 0.8, y: 0 }}
              transition={{ delay: 0.4, duration: 1.0 }}
              className="text-[10px] md:text-xs font-mono text-[#5DE8FF] tracking-[0.3em] uppercase"
            >
              Your intelligent digital mind.
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* ─── Phase 5–10: Virtual Brain / Neural Intelligence Experience ─── */}
      <AnimatePresence>
        {!isPreloading && isBrainPhase && (
          <VirtualBrainExperience active={isBrainPhase} phase={phase} />
        )}
      </AnimatePresence>

      {/* ─── Phase 13: Final Transition ─── */}
      <IntroTransition active={!isPreloading && phase === 13} />

      {/* Ambient vignette background glow */}
      <div className="absolute inset-0 pointer-events-none bg-[radial-gradient(ellipse_at_center,transparent_40%,rgba(3,5,10,0.85))] z-20" />
      
    </div>
  );
}

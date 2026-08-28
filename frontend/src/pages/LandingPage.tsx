import React, { useState } from 'react';
import { motion, AnimatePresence } from 'motion/react';
import Navbar from '../components/navigation/Navbar';
import Hero from '../sections/Hero';
import Capabilities from '../sections/Capabilities';
import Technology from '../sections/Technology';
import Demo from '../sections/Demo';
import Dashboard from '../sections/Dashboard';
import Intelligence from '../sections/Intelligence';
import CTA from '../sections/CTA';
import Footer from '../sections/Footer';
import CustomCursor from '../components/ui/CustomCursor';
import IntroManager from '../components/intro/IntroManager';

interface LandingPageProps {
  onGetStarted: () => void;
}

export default function LandingPage({ onGetStarted }: LandingPageProps) {
  const [showIntro, setShowIntro] = useState(true);
  const [fromIntro, setFromIntro] = useState(false);
  
  const handleNavigate = (sectionId: string) => {
    const el = document.getElementById(sectionId);
    if (el) {
      el.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }
  };

  const handleReplayIntro = () => {
    sessionStorage.removeItem('aida_intro_seen');
    setFromIntro(false);
    setShowIntro(true);
  };

  return (
    <div className="bg-[#05070D] text-[#F5F7FA] font-sans antialiased min-h-screen overflow-x-hidden relative selection:bg-[#5FE8FF]/20 selection:text-[#5FE8FF]">
      
      {/* Intro Experience Overlay */}
      <AnimatePresence>
        {showIntro && (
          <IntroManager onComplete={() => {
            setShowIntro(false);
            setFromIntro(true);
          }} />
        )}
      </AnimatePresence>

      {/* Custom Spring Cursor ring */}
      <CustomCursor />

      {/* Main page content wrapped in a cinematic entry animation */}
      <motion.div
        initial={showIntro ? { opacity: 0 } : false}
        animate={{ opacity: 1 }}
        transition={{ duration: 1.5, ease: "easeOut" }}
      >
        {/* Sticky Premium Glassmorphism Navbar */}
        <Navbar onGetStarted={onGetStarted} onNavigate={handleNavigate} onReplayIntro={handleReplayIntro} />

        {/* Main Sections */}
        <Hero onStart={onGetStarted} onExplore={() => handleNavigate('features')} morphFromIntro={fromIntro} />

        {/* ─── City Intelligence Strip — Full-bleed city image with white brand text ─── */}
        <section className="relative overflow-hidden -mt-1">
          <div className="relative h-[240px] md:h-[340px] overflow-hidden">
            <img
              src="https://images.unsplash.com/photo-1477959858617-67f85cf4f1df?w=1600&q=85&fit=crop"
              alt="City skyline representing AIDA Intelligence everywhere"
              className="w-full h-full object-cover"
              style={{ filter: 'saturate(0.55) brightness(0.45)' }}
            />
            <div className="absolute inset-0 bg-gradient-to-b from-[#05070D] via-transparent to-[#05070D]" />
            <div className="absolute inset-0 bg-gradient-to-r from-[#05070D]/75 via-transparent to-[#05070D]/75" />
            {/* Centered white text overlay */}
            <div className="absolute inset-0 flex flex-col items-center justify-center text-center px-6">
              <p className="font-['JetBrains_Mono',monospace] text-[10px] tracking-[0.35em] text-[#5DE8FF] uppercase mb-3">
                AIDA Intelligence — Everywhere
              </p>
              <h2
                className="font-['Space_Grotesk',sans-serif] font-bold text-white tracking-tight leading-tight max-w-2xl"
                style={{ fontSize: 'clamp(1.4rem, 3vw, 2.5rem)' }}
              >
                Built for the world that{' '}
                <span className="text-transparent bg-clip-text bg-gradient-to-r from-[#5DE8FF] to-[#7C5CFF]">
                  never stops.
                </span>
              </h2>
            </div>
          </div>
        </section>
        
        <Capabilities />
        
        <Technology />
        
        <Demo />

        <Dashboard />
        
        <Intelligence />

        <CTA onStart={onGetStarted} />

        {/* Footer */}
        <Footer onNavigate={handleNavigate} />
      </motion.div>

    </div>
  );
}


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
import OnScrollShapeMorphSection from '../sections/OnScrollShapeMorphSection';

interface LandingPageProps {
  onGetStarted: () => void;
}

export default function LandingPage({ onGetStarted }: LandingPageProps) {
  const [showIntro, setShowIntro] = useState(false);
  const [fromIntro, setFromIntro] = useState(false);
  
  const handleNavigate = (sectionId: string) => {
    const el = document.getElementById(sectionId);
    if (el) {
      el.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }
  };

  const handleReplayIntro = () => {
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
        <Hero onStart={onGetStarted} onExplore={() => handleNavigate('demo')} morphFromIntro={fromIntro} />

        {/* â”€â”€â”€ Holographic Cortana AI HUD Workspace â”€â”€â”€ */}
        <Demo />

        {/* â”€â”€â”€ On-Scroll Shape Morphing Kinetic Showcase â”€â”€â”€ */}
        <OnScrollShapeMorphSection />

        <CTA onStart={onGetStarted} />

        {/* Footer */}
        <Footer onNavigate={handleNavigate} />
      </motion.div>

    </div>
  );
}


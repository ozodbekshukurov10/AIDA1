import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'motion/react';

interface SplashScreenProps {
  onComplete: () => void;
}

export default function SplashScreen({ onComplete }: SplashScreenProps) {
  const [phase, setPhase] = useState(0);

  useEffect(() => {
    const timers = [
      setTimeout(() => setPhase(1), 800),
      setTimeout(() => setPhase(2), 1800),
      setTimeout(() => setPhase(3), 2800),
      setTimeout(() => onComplete(), 4300),
    ];
    return () => timers.forEach(t => clearTimeout(t));
  }, [onComplete]);

  return (
    <motion.div
      className="ae-splash"
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0, scale: 1.1, filter: "brightness(2) blur(10px)" }}
      transition={{ duration: 1 }}
    >
      {/* Dynamic Energy Background */}
      <div className="ae-bg">
        <div className="ae-nebula ae-nebula-1" />
        <div className="ae-nebula ae-nebula-2" />
        <div className="ae-hex-grid" />
      </div>

      <div className="ae-container">
        {/* Central Energy Core */}
        <motion.div 
          className="ae-core"
          animate={{ 
            rotate: 360,
            scale: [1, 1.1, 1],
          }}
          transition={{ 
            rotate: { duration: 10, repeat: Infinity, ease: "linear" },
            scale: { duration: 4, repeat: Infinity, ease: "easeInOut" }
          }}
        >
          <div className="ae-core-glow" />
          <div className="ae-core-inner" />
          
          {/* Orbits */}
          <div className="ae-orbit ae-orbit-1" />
          <div className="ae-orbit ae-orbit-2" />
          <div className="ae-orbit ae-orbit-3" />
        </motion.div>

        <div className="ae-status-copy">
          <div className="ae-status-kicker">AIDA boot sequence</div>
          <div className="ae-status-text">Animatsiya tugashi bilan asosiy panel ochiladi.</div>
        </div>

        {/* Cinematic Elements */}
        <AnimatePresence>
          {phase >= 1 && (
            <motion.div 
              className="ae-rings"
              initial={{ opacity: 0, scale: 0.5 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ duration: 1, ease: "easeOut" }}
            >
              <div className="ae-ring ae-ring-dashed" />
              <div className="ae-ring ae-ring-solid" />
            </motion.div>
          )}

          {phase >= 2 && (
            <motion.div 
              className="ae-wordmark-reveal"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 1 }}
            >
              <h1 className="ae-logo">
                <span className="ae-logo-text">AIDA</span>
                <span className="ae-logo-glimmer" />
              </h1>
              <motion.div 
                className="ae-loader-line"
                initial={{ width: 0 }}
                animate={{ width: "200px" }}
                transition={{ duration: 1.5, ease: "easeInOut" }}
              />
            </motion.div>
          )}

          {phase >= 3 && (
            <motion.div
              className="ae-action"
              initial={{ opacity: 0, scale: 0.9 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ duration: 0.5 }}
            >
              <button className="ae-btn" type="button" onClick={onComplete}>
                <div className="ae-btn-content">
                  <span className="ae-btn-text">BOSHLASH</span>
                  <div className="ae-btn-corner ae-tl" />
                  <div className="ae-btn-corner ae-tr" />
                  <div className="ae-btn-corner ae-bl" />
                  <div className="ae-btn-corner ae-br" />
                </div>
                <div className="ae-btn-glow" />
              </button>
              <button className="ae-skip" type="button" onClick={onComplete}>
                O'tkazib yuborish
              </button>
            </motion.div>
          )}
        </AnimatePresence>
      </div>

      {/* Crosshair / HUD elements */}
      <div className="ae-hud">
        <div className="ae-crosshair ae-ch-h" />
        <div className="ae-crosshair ae-ch-v" />
        <div className="ae-corner-bracket ae-cb-tl" />
        <div className="ae-corner-bracket ae-cb-tr" />
        <div className="ae-corner-bracket ae-cb-bl" />
        <div className="ae-corner-bracket ae-cb-br" />
      </div>
    </motion.div>
  );
}

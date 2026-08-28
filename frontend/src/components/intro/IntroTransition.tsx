import React, { useEffect, useState } from 'react';
import { motion, AnimatePresence } from 'motion/react';

interface IntroTransitionProps {
  active: boolean;
}

export default function IntroTransition({ active }: IntroTransitionProps) {
  const [showFlash, setShowFlash] = useState(false);

  useEffect(() => {
    if (active) {
      const timer = setTimeout(() => {
        setShowFlash(true);
      }, 150);
      return () => clearTimeout(timer);
    } else {
      setShowFlash(false);
    }
  }, [active]);

  if (!active) return null;

  return (
    <div className="absolute inset-0 z-40 pointer-events-none overflow-hidden bg-transparent">
      
      {/* Deep Blue/Midnight Volumetric Fog */}
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 0.9 }}
        exit={{ opacity: 0 }}
        transition={{ duration: 1.6, ease: "easeInOut" }}
        className="absolute inset-0 bg-gradient-to-t from-[#03050A] via-[#07101A]/70 to-[#03050A]"
      />

      {/* Particle Flyby (Thrusting towards camera) */}
      <div className="absolute inset-0">
        {[...Array(28)].map((_, i) => {
          const size = Math.random() * 8 + 3;
          const left = Math.random() * 100;
          const top = Math.random() * 100;
          const duration = Math.random() * 1.2 + 0.8;
          const delay = Math.random() * 0.3;
          
          return (
            <motion.div
              key={i}
              initial={{ 
                opacity: 0, 
                scale: 0.2,
                x: 0,
                y: 0,
                filter: "blur(0px)" 
              }}
              animate={{ 
                opacity: [0, 1, 0],
                scale: [0.5, 3.8, 1.2],
                x: (Math.random() - 0.5) * 350,
                y: -200 - Math.random() * 200,
                filter: ["blur(0px)", "blur(3px)", "blur(0px)"]
              }}
              transition={{ 
                duration, 
                delay,
                ease: [0.1, 0.9, 0.2, 1],
                repeat: Infinity 
              }}
              className="absolute bg-[#5DE8FF] rounded-full shadow-[0_0_15px_#5DE8FF]"
              style={{
                width: `${size}px`,
                height: `${size}px`,
                left: `${left}%`,
                top: `${top}%`,
              }}
            />
          );
        })}
      </div>

      {/* Cyan & Violet Volumetric Core Glow Expansion */}
      <motion.div
        initial={{ opacity: 0, scale: 0.5, filter: "blur(100px)" }}
        animate={{ 
          opacity: [0, 0.55, 0.2],
          scale: [0.5, 1.6, 1.3],
          filter: "blur(180px)"
        }}
        transition={{ duration: 1.8, ease: "easeOut" }}
        className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[700px] h-[700px] rounded-full bg-gradient-to-tr from-[#5DE8FF]/25 via-[#4C7DFF]/20 to-[#7C5CFF]/25"
      />

      {/* Fullscreen light burst */}
      <AnimatePresence>
        {showFlash && (
          <motion.div
            initial={{ opacity: 0, filter: "brightness(0.5)" }}
            animate={{ 
              opacity: [0, 0.85, 1, 0.4, 0],
              filter: ["brightness(0.5)", "brightness(2.2)", "brightness(2.8)", "brightness(1)", "brightness(1)"]
            }}
            exit={{ opacity: 0 }}
            transition={{ duration: 1.6, ease: [0.22, 1, 0.36, 1] }}
            className="absolute inset-0 bg-[#03050A]"
          >
            <div className="absolute inset-0 bg-radial-gradient from-[#5DE8FF]/45 via-transparent to-transparent mix-blend-screen opacity-80" />
          </motion.div>
        )}
      </AnimatePresence>
      
    </div>
  );
}

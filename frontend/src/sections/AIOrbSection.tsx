import React from 'react';
import { motion } from 'motion/react';
import AIOrb from '../components/AIOrb/AIOrb';

export default function AIOrbSection() {
  return (
    <section className="relative py-24 px-6 md:px-12 bg-[#05070D] flex flex-col items-center justify-center overflow-hidden z-10">
      
      {/* Top and Bottom Divider Lines */}
      <div className="absolute top-0 left-1/2 -translate-x-1/2 w-3/4 h-[1px] bg-gradient-to-r from-transparent via-[#5FE8FF]/10 to-transparent pointer-events-none" />
      <div className="absolute bottom-0 left-1/2 -translate-x-1/2 w-3/4 h-[1px] bg-gradient-to-r from-transparent via-[#8B5CF6]/10 to-transparent pointer-events-none" />

      {/* Decorative background grid and nodes */}
      <div className="absolute inset-0 bg-[radial-gradient(circle_at_center,rgba(95,232,255,0.015)_1.5px,transparent_0)] bg-[size:32px_32px] pointer-events-none opacity-60" />

      <div className="max-w-4xl mx-auto flex flex-col items-center gap-12 relative z-10 text-center">
        
        {/* Core Header */}
        <div className="flex flex-col items-center gap-4">
          <span className="text-xs font-mono tracking-[0.3em] text-[#5FE8FF] uppercase">
            System Architecture
          </span>
          <h2 className="font-['Space_Grotesk'] text-3xl sm:text-4xl font-extrabold text-[#F5F7FA] tracking-tight">
            AIDA AI Core
          </h2>
          <p className="text-sm text-[#F5F7FA]/40 font-light max-w-md leading-relaxed">
            The neural processing core of the platform, combining dynamic machine learning and contextual natural language compilers.
          </p>
        </div>

        {/* Central Orb Component */}
        <div className="relative flex items-center justify-center my-6">
          <AIOrb />
        </div>

        {/* Core Subtitle Text */}
        <motion.div 
          initial={{ opacity: 0, y: 15 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.8, delay: 0.2 }}
          className="flex flex-col items-center gap-2 mt-4"
        >
          <span className="font-['Space_Grotesk'] text-lg font-bold tracking-[0.1em] text-[#F5F7FA]">
            Artificial Intelligence Digital Assistant
          </span>
          <span className="text-xs text-[#5FE8FF]/60 font-mono tracking-widest uppercase">
            Model status: Active / Synaptic Rate: 4.8 THz
          </span>
        </motion.div>

      </div>

    </section>
  );
}

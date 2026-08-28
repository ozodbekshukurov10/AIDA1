import React, { useState } from 'react';
import { motion } from 'motion/react';
import AICore, { CoreState } from '../components/ai/AICore';
import AIChat from '../components/ai/AIChat';
import NeuralNetwork from '../components/ai/NeuralNetwork';

export default function Demo() {
  const [coreState, setCoreState] = useState<CoreState>('idle');

  return (
    <section id="demo" className="relative py-24 px-6 md:px-12 bg-[#03050A] z-10 overflow-hidden">
      
      {/* Background ambient network */}
      <div className="absolute inset-0 opacity-10 pointer-events-none">
        <NeuralNetwork mode="ambient" />
      </div>

      {/* Background Soft Glow blobs */}
      <div className="absolute top-1/3 left-10 w-[400px] h-[400px] bg-[#5DE8FF]/3 blur-[120px] rounded-full pointer-events-none" />
      <div className="absolute bottom-10 right-10 w-[350px] h-[350px] bg-[#A78BFA]/3 blur-[100px] rounded-full pointer-events-none" />

      <div className="max-w-7xl mx-auto flex flex-col gap-16 relative z-10">
        
        {/* Section Heading */}
        <div className="flex flex-col items-center text-center gap-4 max-w-xl mx-auto">
          <span className="text-xs font-mono tracking-[0.25em] text-[#5DE8FF] uppercase">
            Live Sandbox
          </span>
          <h2 className="font-['Space_Grotesk'] text-3xl sm:text-4xl md:text-5xl font-extrabold text-[#F5F7FF] tracking-tight leading-tight">
            Interactive <span className="text-transparent bg-clip-text bg-gradient-to-r from-[#5DE8FF] via-[#4C7DFF] to-[#7C5CFF] filter drop-shadow-[0_0_10px_rgba(93,232,255,0.15)]">AI Demo</span>
          </h2>
          <p className="text-sm text-[#9CA9BC] font-light leading-relaxed">
            Witness AIDA's cognitive layers operate in real-time as you submit complex queries.
          </p>
        </div>

        {/* Dual Column Layout: AI Core + Active Chat Console */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-12 items-center">
          
          {/* Left Column: Interactive State Core */}
          <div className="lg:col-span-5 flex flex-col items-center justify-center relative min-h-[360px] border border-white/8 bg-white/[0.03] rounded-3xl p-6 backdrop-blur-2xl shadow-[0_20px_50px_rgba(0,0,0,0.5)]">
            <AICore state={coreState} className="relative z-10" />
            
            {/* Holographic light beams */}
            <div className="absolute bottom-4 left-1/2 -translate-x-1/2 flex items-center gap-2">
              <span className={`w-2 h-2 rounded-full ${
                coreState === 'thinking' ? 'bg-[#7C5CFF] animate-ping' : 
                coreState === 'processing' ? 'bg-[#5DE8FF] animate-pulse' : 'bg-[#5DE8FF]/30'
              }`} />
              <span className="text-[10px] font-mono text-[#9CA9BC]/40 tracking-widest uppercase">
                Core State: {coreState.toUpperCase()}
              </span>
            </div>
          </div>

          {/* Right Column: Predefined Chat Preview Console */}
          <div className="lg:col-span-7 flex justify-center w-full">
            <AIChat onStateChange={(newState) => setCoreState(newState)} />
          </div>

        </div>

      </div>

    </section>
  );
}

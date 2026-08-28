import React from 'react';
import AIHoloInterface from '../components/ai/AIHoloInterface';

export default function Demo() {
  return (
    <section id="demo" className="relative py-20 px-4 md:px-12 bg-[#03050A] z-10 overflow-hidden">
      
      {/* Background Soft Glow blobs */}
      <div className="absolute top-1/3 left-10 w-[500px] h-[500px] bg-[#5DE8FF]/4 blur-[140px] rounded-full pointer-events-none" />
      <div className="absolute bottom-10 right-10 w-[450px] h-[450px] bg-[#7C5CFF]/4 blur-[120px] rounded-full pointer-events-none" />

      <div className="max-w-7xl mx-auto flex flex-col gap-10 relative z-10">
        
        {/* Section Heading */}
        <div className="flex flex-col items-center text-center gap-3 max-w-xl mx-auto">
          <span className="text-xs font-mono tracking-[0.3em] text-[#5DE8FF] uppercase font-bold">
            Tactical AI Workspace
          </span>
          <h2 className="font-['Space_Grotesk'] text-3xl sm:text-4xl md:text-5xl font-extrabold text-[#F5F7FF] tracking-tight leading-tight">
            Holographic <span className="text-transparent bg-clip-text bg-gradient-to-r from-[#5DE8FF] via-[#4C7DFF] to-[#7C5CFF] filter drop-shadow-[0_0_12px_rgba(93,232,255,0.3)]">Cortana HUD</span>
          </h2>
          <p className="text-xs md:text-sm text-[#9CA9BC] font-light leading-relaxed">
            Experience AIDA's next-generation holographic AI neural interface in real-time.
          </p>
        </div>

        {/* Futuristic Holographic HUD Interface */}
        <AIHoloInterface />

      </div>

    </section>
  );
}

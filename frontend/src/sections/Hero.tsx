import React from 'react';
import AIHoloInterface from '../components/ai/AIHoloInterface';

interface HeroProps {
  onStart: () => void;
  onExplore: () => void;
  morphFromIntro?: boolean;
}

export default function Hero({ onStart, onExplore, morphFromIntro = false }: HeroProps) {
  return (
    <section
      id="hero"
      className="relative min-h-screen bg-[#03050A] flex flex-col items-center justify-center overflow-hidden pt-28 pb-12 px-4 md:px-10 z-10"
    >
      {/* â”€â”€ Custom 4K video background â”€â”€ */}
      <div className="absolute inset-0 pointer-events-none z-0 overflow-hidden">
        <video
          autoPlay
          muted
          loop
          playsInline
          className="w-full h-full object-cover opacity-35"
          style={{ filter: 'blur(1px) saturate(0.7) brightness(0.38)', transform: 'scale(1.05)' }}
        >
          <source src="/bg-video.mp4" type="video/mp4" />
        </video>
        <div className="absolute inset-0 bg-gradient-to-b from-[#03050A] via-transparent to-[#03050A] opacity-80" />
      </div>

      {/* â”€â”€ Main Holographic Cortana AI HUD â”€â”€ */}
      <div className="max-w-[1400px] w-full mx-auto relative z-10">
        <AIHoloInterface />
      </div>

    </section>
  );
}

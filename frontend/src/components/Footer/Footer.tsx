import React from 'react';
import AIDALogo from '../ui/AIDALogo';

interface FooterProps {
  onNavigate: (sectionId: string) => void;
}

export default function Footer({ onNavigate }: FooterProps) {
  return (
    <footer className="relative bg-[#03050A] border-t border-white/8 py-16 px-6 md:px-12 overflow-hidden z-10">
      
      {/* Background Soft Glow */}
      <div className="absolute bottom-0 right-1/4 w-[400px] h-[400px] bg-[#7C5CFF]/5 blur-[120px] rounded-full pointer-events-none" />

      <div className="max-w-7xl mx-auto flex flex-col md:flex-row items-start justify-between gap-12">
        
        {/* Brand Information */}
        <div className="flex flex-col gap-4 max-w-sm">
          <a 
            href="#" 
            onClick={(e) => { e.preventDefault(); onNavigate('hero'); }}
            className="flex items-center gap-3 group"
          >
            <div className="w-6 h-6 flex items-center justify-center">
              <AIDALogo 
                size={20} 
                strokeWidth={9}
                className="text-[#5DE8FF] filter drop-shadow-[0_0_5px_rgba(93,232,255,0.45)] group-hover:text-[#4C7DFF] transition-all duration-300" 
              />
            </div>
            <span className="font-['Space_Grotesk'] text-lg font-bold tracking-[0.2em] text-[#F5F7FF] transition-colors group-hover:text-[#5DE8FF]">
              AIDA
            </span>
          </a>
          <p className="text-sm text-[#9CA9BC] font-light leading-relaxed">
            Artificial Intelligence for the next generation. Think faster, build limitlessly, evolve.
          </p>
        </div>

        {/* Links Grid */}
        <div className="grid grid-cols-2 sm:grid-cols-3 gap-8 md:gap-16">
          <div className="flex flex-col gap-3">
            <span className="text-xs font-semibold uppercase tracking-[0.2em] text-[#5DE8FF]">Product</span>
            <a href="#features" onClick={(e) => { e.preventDefault(); onNavigate('features'); }} className="text-sm text-[#F5F7FF]/50 hover:text-[#F5F7FF] transition-colors duration-200">Capabilities</a>
            <a href="#demo" onClick={(e) => { e.preventDefault(); onNavigate('demo'); }} className="text-sm text-[#F5F7FF]/50 hover:text-[#F5F7FF] transition-colors duration-200">AI Demo</a>
          </div>

          <div className="flex flex-col gap-3">
            <span className="text-xs font-semibold uppercase tracking-[0.2em] text-[#5DE8FF]">Technology</span>
            <a href="#technology" onClick={(e) => { e.preventDefault(); onNavigate('technology'); }} className="text-sm text-[#F5F7FF]/50 hover:text-[#F5F7FF] transition-colors duration-200">AI Core</a>
            <a href="#technology" onClick={(e) => { e.preventDefault(); onNavigate('technology'); }} className="text-sm text-[#F5F7FF]/50 hover:text-[#F5F7FF] transition-colors duration-200">Neural Nets</a>
          </div>

          <div className="flex flex-col gap-3 col-span-2 sm:col-span-1">
            <span className="text-xs font-semibold uppercase tracking-[0.2em] text-[#5DE8FF]">Company</span>
            <a href="#" className="text-sm text-[#F5F7FF]/50 hover:text-[#F5F7FF] transition-colors duration-200">Privacy Policy</a>
            <a href="#" className="text-sm text-[#F5F7FF]/50 hover:text-[#F5F7FF] transition-colors duration-200">Terms of Use</a>
          </div>
        </div>

      </div>

      <div className="max-w-7xl mx-auto mt-16 pt-8 border-t border-white/8 flex flex-col sm:flex-row items-center justify-between gap-4">
        <span className="text-xs text-[#9CA9BC]/30">
          © 2026 AIDA. All rights reserved.
        </span>
        <span className="text-xs text-[#9CA9BC]/20 font-mono">
          DESIGNED FOR A HIGHER CONNECTIVITY
        </span>
      </div>

    </footer>
  );
}

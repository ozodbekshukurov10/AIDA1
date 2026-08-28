import React, { useState, useEffect } from 'react';

interface NavbarProps {
  onGetStarted: () => void;
  onNavigate: (sectionId: string) => void;
}

export default function Navbar({ onGetStarted, onNavigate }: NavbarProps) {
  const [isScrolled, setIsScrolled] = useState(false);

  useEffect(() => {
    const handleScroll = () => {
      setIsScrolled(window.scrollY > 20);
    };
    window.addEventListener('scroll', handleScroll);
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  return (
    <nav className={`fixed top-0 left-0 w-full z-50 transition-all duration-300 ${
      isScrolled 
        ? 'py-4 bg-[#05070D]/80 backdrop-blur-md border-b border-[#5FE8FF]/10 shadow-[0_4px_30px_rgba(5,7,13,0.3)]' 
        : 'py-6 bg-transparent'
    }`}>
      <div className="max-w-7xl mx-auto px-6 md:px-12 flex items-center justify-between">
        
        {/* Left Side: Logo & Name */}
        <a 
          href="#" 
          onClick={(e) => { e.preventDefault(); onNavigate('hero'); }}
          className="flex items-center gap-3 group"
        >
          {/* Futuristic AI-inspired Symbol Logo */}
          <div className="relative w-8 h-8 flex items-center justify-center">
            <svg viewBox="0 0 100 100" className="w-full h-full text-[#5FE8FF] filter drop-shadow-[0_0_8px_rgba(95,232,255,0.5)]">
              <polygon 
                points="50,15 85,35 85,75 50,95 15,75 15,35" 
                fill="none" 
                stroke="currentColor" 
                strokeWidth="6" 
                className="transition-all duration-500 group-hover:stroke-[#4D7CFF]"
              />
              <circle cx="50" cy="50" r="14" fill="none" stroke="currentColor" strokeWidth="8" />
              <line x1="50" y1="15" x2="50" y2="36" stroke="currentColor" strokeWidth="6" />
              <line x1="50" y1="64" x2="50" y2="95" stroke="currentColor" strokeWidth="6" />
              <line x1="15" y1="35" x2="38" y2="44" stroke="currentColor" strokeWidth="6" />
              <line x1="85" y1="35" x2="62" y2="44" stroke="currentColor" strokeWidth="6" />
              <line x1="15" y1="75" x2="38" y2="56" stroke="currentColor" strokeWidth="6" />
              <line x1="85" y1="75" x2="62" y2="56" stroke="currentColor" strokeWidth="6" />
            </svg>
            <div className="absolute inset-0 bg-[#5FE8FF] opacity-0 group-hover:opacity-10 blur-md transition-opacity duration-300 rounded-full" />
          </div>
          <span className="font-['Space_Grotesk'] text-xl font-bold tracking-[0.2em] text-[#F5F7FA] transition-colors duration-300 group-hover:text-[#5FE8FF]">
            AIDA
          </span>
        </a>

        {/* Center: Navigation Menu */}
        <div className="hidden md:flex items-center gap-8">
          <a 
            href="#hero" 
            onClick={(e) => { e.preventDefault(); onNavigate('hero'); }}
            className="text-sm font-medium tracking-wider text-[#F5F7FA]/70 hover:text-[#5FE8FF] transition-colors duration-200"
          >
            Home
          </a>
          <a 
            href="#features" 
            onClick={(e) => { e.preventDefault(); onNavigate('features'); }}
            className="text-sm font-medium tracking-wider text-[#F5F7FA]/70 hover:text-[#5FE8FF] transition-colors duration-200"
          >
            Capabilities
          </a>
          <a 
            href="#technology" 
            onClick={(e) => { e.preventDefault(); onNavigate('technology'); }}
            className="text-sm font-medium tracking-wider text-[#F5F7FA]/70 hover:text-[#5FE8FF] transition-colors duration-200"
          >
            Technology
          </a>
          <a 
            href="#demo" 
            onClick={(e) => { e.preventDefault(); onNavigate('demo'); }}
            className="text-sm font-medium tracking-wider text-[#F5F7FA]/70 hover:text-[#5FE8FF] transition-colors duration-200"
          >
            AI Demo
          </a>
        </div>

        {/* Right Side: CTA Button */}
        <div>
          <button 
            onClick={onGetStarted}
            className="relative px-6 py-2.5 bg-transparent border border-[#5FE8FF]/30 rounded-xl overflow-hidden group cursor-pointer transition-all duration-300 hover:border-[#5FE8FF] hover:shadow-[0_0_20px_rgba(95,232,255,0.25)]"
          >
            <div className="absolute inset-0 w-0 bg-gradient-to-r from-[#5FE8FF]/10 to-[#4D7CFF]/10 transition-all duration-300 ease-out group-hover:w-full" />
            <span className="relative text-sm font-bold tracking-wider text-[#F5F7FA] group-hover:text-[#5FE8FF] transition-colors duration-300">
              Get Started
            </span>
          </button>
        </div>

      </div>
    </nav>
  );
}

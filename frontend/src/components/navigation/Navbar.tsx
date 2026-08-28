import React, { useState, useEffect } from 'react';
import { Menu } from 'lucide-react';
import MobileMenu from './MobileMenu';
import AIDALogo from '../ui/AIDALogo';

interface NavbarProps {
  onGetStarted: () => void;
  onNavigate: (sectionId: string) => void;
  onReplayIntro?: () => void;
}

export default function Navbar({ onGetStarted, onNavigate, onReplayIntro }: NavbarProps) {
  const [isScrolled, setIsScrolled] = useState(false);
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);
  const [activeSection, setActiveSection] = useState('hero');

  useEffect(() => {
    const handleScroll = () => {
      setIsScrolled(window.scrollY > 20);

      // Simple active link highlight calculation
      const sections = ['hero', 'features', 'technology', 'demo'];
      const scrollPos = window.scrollY + 120;
      
      for (const sectionId of sections) {
        const el = document.getElementById(sectionId);
        if (el) {
          const top = el.offsetTop;
          const height = el.offsetHeight;
          if (scrollPos >= top && scrollPos < top + height) {
            setActiveSection(sectionId);
            break;
          }
        }
      }
    };
    window.addEventListener('scroll', handleScroll);
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  return (
    <>
      <nav className={`fixed top-0 left-0 w-full z-50 transition-all duration-300 ${
        isScrolled 
          ? 'py-4 bg-[#03050A]/85 backdrop-blur-md border-b border-white/8 shadow-[0_4px_30px_rgba(3,5,10,0.4)]' 
          : 'py-6 bg-transparent'
      }`}>
        <div className="max-w-7xl mx-auto px-6 md:px-12 flex items-center justify-between">
          
          {/* Logo & Geometric branding symbol */}
          <a 
            href="#" 
            onClick={(e) => { e.preventDefault(); onNavigate('hero'); }}
            className="flex items-center gap-3 group magnetic-target"
          >
            <div className="relative w-8 h-8 flex items-center justify-center">
              <AIDALogo 
                size={26} 
                strokeWidth={9}
                className="text-[#5DE8FF] filter drop-shadow-[0_0_8px_rgba(93,232,255,0.45)] group-hover:text-[#4C7DFF] transition-all duration-300" 
              />
            </div>
            <span className="font-['Space_Grotesk'] text-xl font-bold tracking-[0.2em] text-[#F5F7FF] transition-colors duration-300 group-hover:text-[#5DE8FF]">
              AIDA
            </span>
          </a>

          {/* Desktop Menu Navigation */}
          <div className="hidden md:flex items-center gap-8">
            {[
              { id: 'hero', label: 'Home' },
              { id: 'features', label: 'Capabilities' },
              { id: 'technology', label: 'Technology' },
              { id: 'demo', label: 'AI Demo' }
            ].map(link => (
              <a 
                key={link.id}
                href={`#${link.id}`} 
                onClick={(e) => { e.preventDefault(); onNavigate(link.id); }}
                className={`text-sm font-medium tracking-wider transition-colors duration-250 relative py-1 ${
                  activeSection === link.id ? 'text-[#5DE8FF]' : 'text-[#F5F7FF]/70 hover:text-[#5DE8FF]'
                }`}
              >
                {link.label}
                {/* Active Indicator Underline */}
                {activeSection === link.id && (
                  <span className="absolute bottom-0 left-0 w-full h-[1.5px] bg-[#5DE8FF] rounded" />
                )}
              </a>
            ))}
          </div>

          {/* Right Column Action */}
          <div className="flex items-center gap-4">
            {onReplayIntro && (
              <button 
                type="button"
                onClick={onReplayIntro}
                className="inline-flex items-center gap-1.5 px-3.5 py-1.5 rounded-xl border border-[#5DE8FF]/35 text-xs font-mono text-[#5DE8FF] hover:bg-[#5DE8FF]/15 bg-[#5DE8FF]/8 shadow-[0_0_15px_rgba(93,232,255,0.2)] transition-all cursor-pointer font-bold tracking-wider"
                title="Replay Cinematic Intro"
              >
                <span>🎬</span> Replay Intro
              </button>
            )}
            <button 
              onClick={onGetStarted}
              className="relative hidden sm:inline-flex px-6 py-2.5 bg-transparent border border-[#5DE8FF]/30 rounded-xl overflow-hidden group cursor-pointer transition-all duration-300 hover:border-[#5DE8FF] hover:shadow-[0_0_20px_rgba(93,232,255,0.25)] magnetic-target"
            >
              <div className="absolute inset-0 w-0 bg-gradient-to-r from-[#5DE8FF]/10 to-[#4C7DFF]/10 transition-all duration-300 ease-out group-hover:w-full" />
              <span className="relative text-sm font-bold tracking-wider text-[#F5F7FF] group-hover:text-[#5DE8FF] transition-colors duration-300">
                Get Started
              </span>
            </button>

            {/* Mobile Sidebar Hamburger Toggle */}
            <button 
              onClick={() => setIsMobileMenuOpen(true)}
              className="md:hidden p-2 rounded-xl border border-[#F5F7FF]/10 hover:border-[#5DE8FF]/30 text-[#F5F7FF]/80 hover:text-[#5DE8FF] transition-colors duration-250 cursor-pointer"
            >
              <Menu className="w-5 h-5" />
            </button>
          </div>

        </div>
      </nav>

      {/* Sliding Mobile menu layout overlay */}
      <MobileMenu 
        isOpen={isMobileMenuOpen}
        onClose={() => setIsMobileMenuOpen(false)}
        onNavigate={onNavigate}
        onGetStarted={onGetStarted}
      />
    </>
  );
}

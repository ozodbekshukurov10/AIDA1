import React, { useState, useEffect } from 'react';
import { Menu, Globe } from 'lucide-react';
import MobileMenu from './MobileMenu';
import AIDALogo from '../ui/AIDALogo';
import { useLanguage, Language } from '../../context/LanguageContext';

interface NavbarProps {
  onGetStarted: () => void;
  onNavigate: (sectionId: string) => void;
  onReplayIntro?: () => void;
  onOpenContext?: () => void;
}

export default function Navbar({ onGetStarted, onNavigate, onReplayIntro, onOpenContext }: NavbarProps) {
  const [isScrolled, setIsScrolled] = useState(false);
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);
  const [activeSection, setActiveSection] = useState('hero');

  const { lang, setLang, t } = useLanguage();

  useEffect(() => {
    const handleScroll = () => {
      setIsScrolled(window.scrollY > 20);

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

  const navLinks = [
    { id: 'hero', label: t.nav.home },
    { id: 'features', label: t.nav.capabilities },
    { id: 'technology', label: t.nav.technology },
    { id: 'demo', label: t.nav.demo }
  ];

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
            {navLinks.map(link => (
              <a 
                key={link.id}
                href={`#${link.id}`} 
                onClick={(e) => { e.preventDefault(); onNavigate(link.id); }}
                className={`text-sm font-medium tracking-wider transition-colors duration-250 relative py-1 ${
                  activeSection === link.id ? 'text-[#5DE8FF]' : 'text-[#F5F7FF]/70 hover:text-[#5DE8FF]'
                }`}
              >
                {link.label}
                {activeSection === link.id && (
                  <span className="absolute bottom-0 left-0 w-full h-[1.5px] bg-[#5DE8FF] rounded" />
                )}
              </a>
            ))}
          </div>

          {/* Right Column Actions & 3-Language Selector */}
          <div className="flex items-center gap-3">

            {/* Language Switcher Pill (UZ / EN / RU) */}
            <div className="flex items-center p-1 rounded-xl bg-white/5 border border-white/10 backdrop-blur-md">
              {(['uz', 'en', 'ru'] as Language[]).map((l) => (
                <button
                  key={l}
                  type="button"
                  onClick={() => setLang(l)}
                  className={`px-2.5 py-1 rounded-lg font-mono text-xs font-bold tracking-wider uppercase transition-all duration-300 cursor-pointer ${
                    lang === l
                      ? 'bg-[#5DE8FF] text-[#03050A] shadow-[0_0_10px_rgba(93,232,255,0.5)]'
                      : 'text-[#9CA9BC] hover:text-white'
                  }`}
                >
                  {l === 'uz' ? 'UZ' : l === 'en' ? 'EN' : 'RU'}
                </button>
              ))}
            </div>

            {onReplayIntro && (
              <button 
                type="button"
                onClick={onReplayIntro}
                className="hidden sm:inline-flex items-center gap-1.5 px-3.5 py-1.5 rounded-xl border border-[#5DE8FF]/35 text-xs font-mono text-[#5DE8FF] hover:bg-[#5DE8FF]/15 bg-[#5DE8FF]/8 shadow-[0_0_15px_rgba(93,232,255,0.2)] transition-all cursor-pointer font-bold tracking-wider"
                title="Replay Cinematic Intro"
              >
                <span>ðŸŽ¬</span> {t.nav.replayIntro}
              </button>
            )}

            <button 
              onClick={onGetStarted}
              className="relative hidden sm:inline-flex px-6 py-2 bg-gradient-to-r from-[#5B75FF] to-[#8C52FF] text-white font-['Space_Grotesk'] text-xs font-bold tracking-wider rounded-xl overflow-hidden group cursor-pointer transition-all duration-300 hover:shadow-[0_0_20px_rgba(140,82,255,0.4)]"
            >
              <span>{t.nav.getStarted}</span>
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

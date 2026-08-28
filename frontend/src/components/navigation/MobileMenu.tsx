import React from 'react';
import { motion } from 'motion/react';
import { X } from 'lucide-react';
import AIDALogo from '../ui/AIDALogo';

interface MobileMenuProps {
  isOpen: boolean;
  onClose: () => void;
  onNavigate: (sectionId: string) => void;
  onGetStarted: () => void;
}

export default function MobileMenu({ 
  isOpen, 
  onClose, 
  onNavigate, 
  onGetStarted 
}: MobileMenuProps) {
  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-[100] md:hidden">
      
      {/* Dark Overlay backdrop */}
      <motion.div 
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        exit={{ opacity: 0 }}
        onClick={onClose}
        className="absolute inset-0 bg-black/60 backdrop-blur-sm"
      />

      {/* Sliding Menu Panel */}
      <motion.div 
        initial={{ x: '100%' }}
        animate={{ x: 0 }}
        exit={{ x: '100%' }}
        transition={{ type: 'spring', damping: 25, stiffness: 220 }}
        className="absolute top-0 right-0 w-[280px] h-full bg-[#03050A] border-l border-white/8 p-6 flex flex-col justify-between"
      >
        
        {/* Header Toggler */}
        <div className="flex justify-between items-center pb-6 border-b border-white/8">
          <div className="flex items-center gap-2">
            <AIDALogo size={18} strokeWidth={9} className="text-[#5DE8FF] filter drop-shadow-[0_0_5px_rgba(93,232,255,0.45)]" />
            <span className="font-['Space_Grotesk'] font-bold text-lg text-[#F5F7FF] tracking-widest">
              AIDA
            </span>
          </div>
          <button 
            onClick={onClose}
            className="p-1 rounded-lg border border-white/8 text-[#F5F7FF]/60 hover:text-[#F5F7FF] cursor-pointer"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Links Stack */}
        <div className="flex flex-col gap-6 my-auto">
          {['Home', 'Capabilities', 'Technology', 'AI Demo'].map((label, idx) => {
            const ids = ['hero', 'features', 'technology', 'demo'];
            return (
              <a
                key={idx}
                href={`#${ids[idx]}`}
                onClick={(e) => {
                  e.preventDefault();
                  onNavigate(ids[idx]);
                  onClose();
                }}
                className="text-lg font-medium tracking-wider text-[#F5F7FF]/75 hover:text-[#5DE8FF] transition-colors duration-200"
              >
                {label}
              </a>
            );
          })}
        </div>

        {/* Bottom CTA Action */}
        <div className="pt-6 border-t border-white/8">
          <button 
            onClick={() => {
              onGetStarted();
              onClose();
            }}
            className="w-full py-4 bg-gradient-to-r from-[#4C7DFF] to-[#7C5CFF] text-[#F5F7FF] font-bold text-sm tracking-wider rounded-xl shadow-[0_0_15px_rgba(76,125,255,0.15)] hover:from-[#5DE8FF] hover:to-[#4C7DFF] hover:text-[#03050A] transition-all duration-300 cursor-pointer"
          >
            Get Started
          </button>
        </div>

      </motion.div>

    </div>
  );
}

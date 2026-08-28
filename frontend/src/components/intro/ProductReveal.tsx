import React, { useEffect, useState } from 'react';
import { motion, AnimatePresence } from 'motion/react';
import { Bot, User, CornerDownLeft, CircleAlert } from 'lucide-react';

interface ProductRevealProps {
  active: boolean; // active when phase === 11 || phase === 12 || phase === 13
  phase: number;
}

export default function ProductReveal({ active, phase }: ProductRevealProps) {
  const [typedPrompt, setTypedPrompt] = useState('');
  const [typedResponse, setTypedResponse] = useState('');
  const [step, setStep] = useState(0); // 0: Idle, 1: Typing Prompt, 2: Typing Response, 3: Completed

  const fullPrompt = "Explain how neural networks work.";
  const fullResponse = "Neural networks learn patterns by processing connected layers of information.";

  useEffect(() => {
    if (!active) {
      setTypedPrompt('');
      setTypedResponse('');
      setStep(0);
      return;
    }

    if (phase === 11) {
      // Type User Prompt
      setStep(1);
      let index = 0;
      const typePrompt = () => {
        if (index <= fullPrompt.length) {
          setTypedPrompt(fullPrompt.slice(0, index));
          index++;
          setTimeout(typePrompt, 40);
        } else {
          setStep(2);
        }
      };
      const trigger = setTimeout(typePrompt, 1200); // delay after UI frame fades in
      return () => clearTimeout(trigger);
    }

    if (phase === 12) {
      // Type AIDA Response
      setStep(2);
      let index = 0;
      const typeResponse = () => {
        if (index <= fullResponse.length) {
          setTypedResponse(fullResponse.slice(0, index));
          index++;
          setTimeout(typeResponse, 30);
        } else {
          setStep(3);
        }
      };
      const trigger = setTimeout(typeResponse, 300);
      return () => clearTimeout(trigger);
    }
  }, [active, phase]);

  if (!active) return null;

  // Animation values for Phase 13 full screen morph
  const isTransitioning = phase === 13;

  return (
    <div className="absolute inset-0 flex items-center justify-center bg-transparent z-35 p-4 md:p-6 pointer-events-none select-none">
      
      {/* Assembling Container with Fragment Delays */}
      <motion.div
        initial={{ opacity: 0, y: 40, scale: 0.88, filter: "blur(15px)" }}
        animate={{ 
          opacity: isTransitioning ? [1, 0.9, 0] : 1, 
          y: isTransitioning ? -100 : 0, 
          scale: isTransitioning ? 2.8 : 1, 
          filter: isTransitioning ? "blur(20px)" : "blur(0px)",
          backdropFilter: isTransitioning ? "blur(0px)" : "blur(24px)"
        }}
        exit={{ opacity: 0, scale: 0.9, filter: "blur(10px)" }}
        transition={{ 
          duration: isTransitioning ? 1.6 : 1.2, 
          ease: isTransitioning ? [0.22, 1, 0.36, 1] : [0.16, 1, 0.3, 1] 
        }}
        className="w-full max-w-lg bg-[#03050A]/75 border border-[#5DE8FF]/15 rounded-2xl shadow-[0_30px_90px_rgba(0,0,0,0.9)] overflow-hidden relative"
      >
        
        {/* Shimmer Outline Sweep */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: [0, 0.5, 0] }}
          transition={{ duration: 2.0, repeat: Infinity, repeatDelay: 1 }}
          className="absolute inset-0 border border-[#5DE8FF]/25 rounded-2xl pointer-events-none"
        />

        {/* Fragment 1: Terminal Header */}
        <div className="flex items-center justify-between px-4 py-3 bg-[#03050A]/90 border-b border-white/5">
          <div className="flex items-center gap-2">
            <span className="w-2 h-2 rounded-full bg-[#ef4444]/60" />
            <span className="w-2 h-2 rounded-full bg-[#f59e0b]/60" />
            <span className="w-2 h-2 rounded-full bg-[#10b981]/60" />
          </div>
          <div className="text-[10px] font-mono text-[#5DE8FF]/60 tracking-widest font-semibold flex items-center gap-1.5">
            <Bot size={12} className="text-[#5DE8FF]" /> AIDA INTERACTION TERMINAL
          </div>
          <div className="w-10" />
        </div>

        {/* Fragment 2: Chat Output Area */}
        <div className="p-5 flex flex-col gap-4 min-h-[180px] font-sans text-sm">
          
          {/* User Message */}
          <AnimatePresence>
            {typedPrompt.length > 0 && (
              <motion.div
                initial={{ opacity: 0, y: 12, filter: "blur(5px)" }}
                animate={{ opacity: 1, y: 0, filter: "blur(0px)" }}
                transition={{ duration: 0.4 }}
                className="flex items-start gap-3 justify-end"
              >
                <div className="flex flex-col items-end gap-1 max-w-[80%]">
                  <div className="px-4 py-2.5 bg-[#4C7DFF]/15 border border-[#4C7DFF]/30 text-[#F5F7FF] rounded-2xl rounded-tr-sm text-[13px] leading-relaxed shadow-[0_0_20px_rgba(76,125,255,0.1)]">
                    {typedPrompt}
                    {step === 1 && <span className="inline-block w-1.5 h-3.5 bg-[#4C7DFF] animate-pulse ml-1" />}
                  </div>
                  <span className="text-[9px] font-mono text-[#F5F7FF]/25 flex items-center gap-1">
                    User <User size={9} />
                  </span>
                </div>
              </motion.div>
            )}
          </AnimatePresence>

          {/* AIDA Response */}
          <AnimatePresence>
            {(phase >= 12 || typedResponse.length > 0) && (
              <motion.div
                initial={{ opacity: 0, y: 12, filter: "blur(5px)" }}
                animate={{ opacity: 1, y: 0, filter: "blur(0px)" }}
                transition={{ duration: 0.4 }}
                className="flex items-start gap-3"
              >
                <div className="flex flex-col items-start gap-1 max-w-[85%]">
                  <div className="px-4 py-2.5 bg-[#5DE8FF]/6 border border-[#5DE8FF]/20 text-[#5DE8FF] rounded-2xl rounded-tl-sm text-[13px] leading-relaxed font-medium filter drop-shadow-[0_0_15px_rgba(93,232,255,0.15)]">
                    {typedResponse}
                    {phase === 12 && step === 2 && <span className="inline-block w-1.5 h-3.5 bg-[#5DE8FF] animate-pulse ml-1" />}
                  </div>
                  <span className="text-[9px] font-mono text-[#5DE8FF]/60 flex items-center gap-1.5">
                    <Bot size={10} className="text-[#5DE8FF]/70" /> AIDA CORE
                  </span>
                </div>
              </motion.div>
            )}
          </AnimatePresence>

        </div>

        {/* Fragment 3: Input Bar panel with AIDA Status */}
        <div className="p-3 bg-[#03050A]/70 border-t border-white/5 flex items-center justify-between gap-3">
          <div className="flex items-center gap-2 text-[#F5F7FF]/40 font-mono text-[10px] px-3 py-2 rounded-lg bg-[#03050A]/90 border border-white/5 w-full">
            <span className="text-[#5DE8FF] font-bold animate-pulse">&gt;</span>
            {phase === 11 && (
              <span className="text-[#F5F7FF]/35">AIDA is typing prompt...</span>
            )}
            {phase === 12 && step === 2 && (
              <span className="text-[#F5F7FF]/35">AIDA is thinking...</span>
            )}
            {phase >= 12 && step === 3 && (
              <span className="text-[#10b981] font-semibold flex items-center gap-1 animate-pulse">
                <span className="w-1.5 h-1.5 rounded-full bg-[#10b981]" /> AIDA is ready.
              </span>
            )}
          </div>
          <div className="w-8 h-8 rounded-lg bg-[#5DE8FF]/10 border border-[#5DE8FF]/25 flex items-center justify-center text-[#5DE8FF] opacity-80 shrink-0">
            <CornerDownLeft size={14} />
          </div>
        </div>

      </motion.div>
    </div>
  );
}

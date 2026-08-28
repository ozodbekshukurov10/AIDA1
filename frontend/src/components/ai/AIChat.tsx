import React, { useEffect, useState } from 'react';
import { motion } from 'motion/react';
import { Terminal, Send, Bot } from 'lucide-react';

interface AIChatProps {
  onStateChange?: (state: 'idle' | 'thinking' | 'processing' | 'response') => void;
}

export default function AIChat({ onStateChange }: AIChatProps) {
  const [phase, setPhase] = useState(0); // 0: idle, 1: user text typing, 2: thinking, 3: AIDA typing
  const [typedUserText, setTypedUserText] = useState('');
  const [typedAidaText, setTypedAidaText] = useState('');

  const userText = "Create a modern landing page for my startup.";
  const aidaText = "Absolutely. I'll help you design a clean, high-converting and modern interface.";

  useEffect(() => {
    // Phase 0 -> 1: delay start
    const timer1 = setTimeout(() => {
      setPhase(1);
    }, 1000);

    return () => clearTimeout(timer1);
  }, []);

  // Animate User Text typing
  useEffect(() => {
    if (phase !== 1) return;
    let charIndex = 0;
    const interval = setInterval(() => {
      if (charIndex < userText.length) {
        setTypedUserText(userText.slice(0, charIndex + 1));
        charIndex++;
      } else {
        clearInterval(interval);
        // Switch to Thinking phase
        setPhase(2);
        if (onStateChange) onStateChange('thinking');
      }
    }, 40);

    return () => clearInterval(interval);
  }, [phase]);

  // Animate Thinking phase delay
  useEffect(() => {
    if (phase !== 2) return;
    const timer = setTimeout(() => {
      setPhase(3);
      if (onStateChange) onStateChange('processing');
    }, 2000); // 2s thinking loading dot animation

    return () => clearTimeout(timer);
  }, [phase]);

  // Animate AIDA response typing
  useEffect(() => {
    if (phase !== 3) return;
    let charIndex = 0;
    const interval = setInterval(() => {
      if (charIndex < aidaText.length) {
        setTypedAidaText(aidaText.slice(0, charIndex + 1));
        charIndex++;
      } else {
        clearInterval(interval);
        if (onStateChange) onStateChange('response');
        // Reset/loop again after 6 seconds to keep landing page active
        setTimeout(() => {
          setPhase(0);
          setTypedUserText('');
          setTypedAidaText('');
          if (onStateChange) onStateChange('idle');
          // Restart loop
          setTimeout(() => setPhase(1), 1000);
        }, 6000);
      }
    }, 35);

    return () => clearInterval(interval);
  }, [phase]);

  return (
    <div className="w-full max-w-lg rounded-3xl border border-[#5FE8FF]/15 bg-[#08111F]/20 backdrop-blur-xl p-6 md:p-8 flex flex-col gap-6 shadow-[0_20px_50px_rgba(0,0,0,0.4)] relative overflow-hidden">
      
      {/* Top Banner Control indicator */}
      <div className="flex items-center justify-between border-b border-[#F5F7FA]/5 pb-4">
        <div className="flex items-center gap-2 text-xs font-mono text-[#F5F7FA]/30">
          <Terminal className="w-4 h-4 text-[#5FE8FF] animate-pulse" />
          <span>AIDA_AI_ASSISTANT.SH</span>
        </div>
        <span className="text-[9px] font-mono tracking-widest text-[#5FE8FF]/50 uppercase bg-[#5FE8FF]/5 border border-[#5FE8FF]/10 px-2 py-0.5 rounded">
          Operational Preview
        </span>
      </div>

      {/* Message Feed Display */}
      <div className="flex flex-col gap-5 min-h-[160px] justify-end">
        
        {/* User Message */}
        {phase >= 1 && (
          <motion.div 
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            className="flex flex-col items-end gap-1.5 self-end max-w-[85%]"
          >
            <span className="text-[10px] font-mono text-[#F5F7FA]/30 mr-1 uppercase">User</span>
            <div className="bg-[#5FE8FF]/10 border border-[#5FE8FF]/20 text-[#F5F7FA] text-sm px-4 py-3 rounded-2xl rounded-tr-sm font-light shadow-[0_5px_15px_rgba(95,232,255,0.03)]">
              {typedUserText}
              {phase === 1 && <span className="inline-block w-1.5 h-3.5 bg-[#5FE8FF] ml-0.5 animate-pulse" />}
            </div>
          </motion.div>
        )}

        {/* AIDA Thinking Loading Indicator */}
        {phase === 2 && (
          <motion.div 
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            className="flex items-start gap-3 max-w-[85%]"
          >
            <div className="w-8 h-8 rounded-full border border-[#5FE8FF]/20 bg-[#08111F]/50 flex items-center justify-center text-[#5FE8FF] flex-shrink-0">
              <Bot className="w-4 h-4 animate-bounce" />
            </div>
            <div className="flex flex-col gap-1.5">
              <span className="text-[10px] font-mono text-[#5FE8FF]/50 uppercase">AIDA is thinking</span>
              <div className="bg-[#05070D]/60 border border-[#5FE8FF]/10 text-sm px-4 py-3.5 rounded-2xl rounded-tl-sm flex gap-1.5 items-center">
                <span className="w-2 h-2 rounded-full bg-[#5FE8FF] animate-[typing_1.4s_infinite]" />
                <span className="w-2 h-2 rounded-full bg-[#5FE8FF] animate-[typing_1.4s_infinite_0.2s]" />
                <span className="w-2 h-2 rounded-full bg-[#5FE8FF] animate-[typing_1.4s_infinite_0.4s]" />
              </div>
            </div>
          </motion.div>
        )}

        {/* AIDA Typing Output */}
        {phase >= 3 && (
          <motion.div 
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            className="flex items-start gap-3 max-w-[85%]"
          >
            <div className="w-8 h-8 rounded-full border border-[#5FE8FF]/20 bg-[#08111F]/50 flex items-center justify-center text-[#5FE8FF] flex-shrink-0">
              <Bot className="w-4 h-4" />
            </div>
            <div className="flex flex-col gap-1.5">
              <span className="text-[10px] font-mono text-[#5FE8FF]/50 uppercase">AIDA</span>
              <div className="bg-[#05070D]/70 border border-[#5FE8FF]/10 text-[#F5F7FA] text-sm px-4 py-3 rounded-2xl rounded-tl-sm font-light leading-relaxed shadow-[0_5px_15px_rgba(0,0,0,0.15)]">
                {typedAidaText}
                {phase === 3 && <span className="inline-block w-1.5 h-3.5 bg-[#8B5CF6] ml-0.5 animate-pulse" />}
              </div>
            </div>
          </motion.div>
        )}

      </div>

      {/* Input panel console placeholder */}
      <div className="relative border border-[#F5F7FA]/10 bg-[#05070D]/50 rounded-xl px-4 py-3 flex items-center justify-between">
        <span className="text-xs text-[#F5F7FA]/30">Ask AIDA anything...</span>
        <div className="p-1.5 rounded-lg bg-[#5FE8FF]/10 text-[#5FE8FF] opacity-40">
          <Send className="w-3.5 h-3.5" />
        </div>
      </div>

    </div>
  );
}

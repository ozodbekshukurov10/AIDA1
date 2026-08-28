import React, { useEffect, useState } from 'react';
import { motion, AnimatePresence } from 'motion/react';

interface VirtualBrainExperienceProps {
  active: boolean;
  phase: number; // 5–11
}

// State labels for floating HUD UI
interface HUDState {
  status: string;
  latency: string;
  mode: string;
}

const PHASE_HUD_STATES: Record<number, HUDState> = {
  5: { status: 'MEMORY SYSTEM ACTIVE', latency: 'CONCEPT', mode: 'EXPLORING STORAGE' },
  6: { status: 'SEMANTIC RETRIEVAL', latency: 'CONCEPT', mode: 'VECTOR INDEX MATCH' },
  7: { status: 'REASONING FLOW', latency: 'CONCEPT', mode: 'MULTI-STEP VALIDATION' },
  8: { status: 'TOOL READY ARCHITECTURE', latency: 'CONCEPT', mode: 'CONNECTIONS OPEN' },
  9: { status: 'VERIFICATION LAYER', latency: 'CONCEPT', mode: 'ACCURACY CROSS-CHECK' },
  10: { status: 'ULTRA INTELLIGENCE', latency: 'CONCEPT', mode: 'GLOBAL CASCADE' },
  11: { status: 'INTELLIGENCE LOOP', latency: 'DEMO', mode: 'AIDA OPERATIONAL' },
};

export default function VirtualBrainExperience({ active, phase }: VirtualBrainExperienceProps) {
  const [hud, setHud] = useState<HUDState>({ status: 'STANDBY', latency: 'CONCEPT', mode: 'IDLE' });

  useEffect(() => {
    if (PHASE_HUD_STATES[phase]) {
      setHud(PHASE_HUD_STATES[phase]);
    }
  }, [phase]);

  if (!active) return null;

  const blurVariants = {
    hidden: { opacity: 0, filter: 'blur(14px)', y: 15 },
    visible: { 
      opacity: 1, 
      filter: 'blur(0px)', 
      y: 0,
      transition: { duration: 0.95, ease: [0.16, 1, 0.3, 1] }
    },
    exit: { 
      opacity: 0, 
      filter: 'blur(12px)', 
      y: -12,
      transition: { duration: 0.5, ease: 'easeIn' }
    }
  };

  const itemVariants = {
    hidden: { opacity: 0, filter: 'blur(8px)', x: -10 },
    visible: (i: number) => ({
      opacity: 1,
      filter: 'blur(0px)',
      x: 0,
      transition: { delay: i * 0.15, duration: 0.6, ease: 'easeOut' }
    })
  };

  return (
    <div className="absolute inset-0 z-25 overflow-hidden pointer-events-none select-none">
      
      {/* ─── 1. Persistent Floating Holographic HUD (Positioned at Top-Left Margin) ─── */}
      <div className="absolute top-6 left-6 md:left-10 z-30 pointer-events-auto max-w-[240px]">
        <div className="bg-[#03050A]/85 border border-[#5DE8FF]/20 backdrop-blur-xl rounded-xl p-3.5 font-mono text-[9.5px] text-[#F5F7FF]/80 flex flex-col gap-1.5 shadow-[0_4px_30px_rgba(0,0,0,0.6)]">
          <div className="flex items-center gap-2 text-[#5DE8FF] font-semibold text-[10px]">
            <span className="w-1.5 h-1.5 rounded-full bg-[#5DE8FF] animate-pulse" />
            AIDA BRAIN ARCHITECTURE
          </div>
          <div className="h-px bg-white/10 w-full my-0.5" />
          <div className="flex justify-between gap-4">
            <span className="text-[#F5F7FF]/40">STATUS:</span>
            <span className="text-[#5DE8FF] font-medium">{hud.status}</span>
          </div>
          <div className="flex justify-between gap-4">
            <span className="text-[#F5F7FF]/40">STATE:</span>
            <span className="px-1.5 py-0.2 bg-[#5DE8FF]/10 text-[#5DE8FF] border border-[#5DE8FF]/20 rounded font-semibold text-[8.5px]">{hud.latency}</span>
          </div>
          <div className="flex justify-between gap-4">
            <span className="text-[#F5F7FF]/40">MODE:</span>
            <span className="text-[#7C5CFF]">{hud.mode}</span>
          </div>
        </div>
      </div>

      {/* ─── 2. Stage-Specific Text Overlays with Dark Glass Backdrop Card ─── */}
      <div className="relative z-10 flex flex-col justify-center h-full w-full max-w-xl px-6 md:px-16 lg:px-24 pt-28 pb-10 gap-4 pointer-events-auto">
        <AnimatePresence mode="wait">
          
          {phase === 5 && (
            <motion.div key="p5" initial="hidden" animate="visible" exit="exit" variants={blurVariants} className="bg-[#03050A]/85 border border-white/10 backdrop-blur-xl rounded-2xl p-6 md:p-8 shadow-[0_8px_32px_rgba(0,0,0,0.6)] flex flex-col gap-3">
              <span className="font-mono text-[10px] tracking-[0.25em] text-[#7C5CFF] uppercase font-semibold">
                SYSTEM CORE / STAGE 01
              </span>
              <h2 className="font-['Space_Grotesk'] font-bold text-2xl md:text-4xl text-[#F5F7FF] tracking-[0.02em] leading-tight">
                MEMORY ARCHITECTURE
              </h2>
              <p className="font-sans text-xs md:text-sm text-[#9CA9BC] leading-relaxed">
                Exploring internal layers: context window limits, local buffer caches, and retrieval routing mechanisms.
              </p>
              
              <div className="flex flex-col gap-2 mt-3">
                {[
                  { label: 'WORKING MEMORY', val: 'Active Parameters (Temporary Cache)' },
                  { label: 'CONTEXT BUFFER', val: 'Conversation Context Sync' },
                  { label: 'LONG-TERM MEMORY', val: 'Persistent Memory — Architecture focus' },
                  { label: 'USER CONTEXT', val: 'Designed for user preference alignment' },
                  { label: 'KNOWLEDGE', val: 'Retrieval Index Base' },
                ].map((item, idx) => (
                  <motion.div custom={idx} variants={itemVariants} initial="hidden" animate="visible" key={item.label} className="flex flex-col gap-0.5 border-l-2 border-[#7C5CFF]/40 pl-3">
                    <span className="font-mono text-[9px] text-[#7C5CFF] tracking-wider font-semibold">{item.label}</span>
                    <span className="text-[11px] text-[#F5F7FF]/75">{item.val}</span>
                  </motion.div>
                ))}
              </div>
            </motion.div>
          )}

          {phase === 6 && (
            <motion.div key="p6" initial="hidden" animate="visible" exit="exit" variants={blurVariants} className="bg-[#03050A]/85 border border-white/10 backdrop-blur-xl rounded-2xl p-6 md:p-8 shadow-[0_8px_32px_rgba(0,0,0,0.6)] flex flex-col gap-3">
              <span className="font-mono text-[10px] tracking-[0.25em] text-[#4C7DFF] uppercase font-semibold">
                INFORMATION RETRIEVAL / STAGE 02
              </span>
              <h2 className="font-['Space_Grotesk'] font-bold text-2xl md:text-4xl text-[#F5F7FF] tracking-[0.02em] leading-tight">
                EMBEDDINGS & VECTOR SEARCH
              </h2>
              <p className="font-sans text-xs md:text-sm text-[#9CA9BC] leading-relaxed">
                Converting incoming user requests into multi-dimensional vectors for similarity queries across codebase embedding spaces.
              </p>

              <div className="bg-[#03050A]/60 border border-white/10 p-4 rounded-xl flex flex-col gap-2 mt-3 font-mono text-[10px]">
                <span className="text-[#F5F7FF]/40 text-[9px] tracking-wider">RETRIEVAL GRAPH:</span>
                <div className="flex flex-col gap-1 text-[#F5F7FF]/80">
                  <div className="flex justify-between border-b border-white/5 pb-1">
                    <span>QUERY ENCODE</span>
                    <span className="text-[#5DE8FF]">SUCCESS</span>
                  </div>
                  <div className="flex justify-between border-b border-white/5 pb-1">
                    <span>VECTOR INDEX MATCH</span>
                    <span className="text-[#5DE8FF]">MATCHED (3 points)</span>
                  </div>
                  <div className="flex justify-between border-b border-white/5 pb-1">
                    <span>RANK CONTEXT</span>
                    <span className="text-[#4C7DFF]">INJECTED</span>
                  </div>
                </div>
                <div className="text-[9px] text-[#7C5CFF]/80 italic mt-1 text-center font-sans">
                  Semantic Retrieval Architecture
                </div>
              </div>
            </motion.div>
          )}

          {phase === 7 && (
            <motion.div key="p7" initial="hidden" animate="visible" exit="exit" variants={blurVariants} className="bg-[#03050A]/85 border border-white/10 backdrop-blur-xl rounded-2xl p-6 md:p-8 shadow-[0_8px_32px_rgba(0,0,0,0.6)] flex flex-col gap-3">
              <span className="font-mono text-[10px] tracking-[0.25em] text-[#7C5CFF] uppercase font-semibold">
                LOGIC PROCESS / STAGE 03
              </span>
              <h2 className="font-['Space_Grotesk'] font-bold text-2xl md:text-4xl text-[#F5F7FF] tracking-[0.02em] leading-tight">
                REASONING SYSTEM
              </h2>
              <p className="font-sans text-xs md:text-sm text-[#9CA9BC] leading-relaxed">
                Parallel inference pathways analyze constraints, plan execution steps, and generate structured outcomes.
              </p>

              <div className="flex flex-col gap-2.5 mt-3">
                {[
                  { step: '01', title: 'INTERPRET INTENT', desc: 'Isolate user request core variables' },
                  { step: '02', title: 'PLAN EXECUTION', desc: 'Break task down into logical steps' },
                  { step: '03', title: 'RESOLVE DEPENDENCIES', desc: 'Assemble local/remote resources' },
                ].map((item, idx) => (
                  <motion.div custom={idx} variants={itemVariants} initial="hidden" animate="visible" key={item.step} className="flex gap-3 items-start border-l-2 border-[#7C5CFF]/40 pl-3">
                    <span className="font-mono text-[11px] text-[#7C5CFF] font-bold mt-0.5">{item.step}</span>
                    <div className="flex flex-col">
                      <span className="font-mono text-[10px] text-[#F5F7FF] font-semibold tracking-wider">{item.title}</span>
                      <span className="text-[11px] text-[#9CA9BC]">{item.desc}</span>
                    </div>
                  </motion.div>
                ))}
              </div>
            </motion.div>
          )}

          {phase === 8 && (
            <motion.div key="p8" initial="hidden" animate="visible" exit="exit" variants={blurVariants} className="bg-[#03050A]/85 border border-white/10 backdrop-blur-xl rounded-2xl p-6 md:p-8 shadow-[0_8px_32px_rgba(0,0,0,0.6)] flex flex-col gap-3">
              <span className="font-mono text-[10px] tracking-[0.25em] text-[#A78BFA] uppercase font-semibold">
                CAPABILITIES / STAGE 04
              </span>
              <h2 className="font-['Space_Grotesk'] font-bold text-2xl md:text-4xl text-[#F5F7FF] tracking-[0.02em] leading-tight">
                TOOL INTEGRATION
              </h2>
              <p className="font-sans text-xs md:text-sm text-[#9CA9BC] leading-relaxed">
                Connecting core models with sandbox filesystems, web search clients, shell agents, and automation loops.
              </p>

              <div className="grid grid-cols-2 gap-2 mt-3 max-w-xs">
                {['WEB SEARCH', 'SANDBOX FS', 'SHELL TERMINAL', 'FILE WRITER'].map((t, idx) => (
                  <motion.div custom={idx} variants={itemVariants} initial="hidden" animate="visible" key={t} className="border border-white/10 rounded-lg p-2.5 bg-[#03050A]/60 text-center font-mono text-[9px] text-[#A78BFA] tracking-wider font-semibold">
                    {t}
                  </motion.div>
                ))}
              </div>
              <div className="font-mono text-[9px] text-[#F5F7FF]/40 tracking-wider mt-1">
                Tool-ready architecture. Designed for integration.
              </div>
            </motion.div>
          )}

          {phase === 9 && (
            <motion.div key="p9" initial="hidden" animate="visible" exit="exit" variants={blurVariants} className="bg-[#03050A]/85 border border-white/10 backdrop-blur-xl rounded-2xl p-6 md:p-8 shadow-[0_8px_32px_rgba(0,0,0,0.6)] flex flex-col gap-3">
              <span className="font-mono text-[10px] tracking-[0.25em] text-[#5DE8FF] uppercase font-semibold">
                SAFETY & VERIFICATION / STAGE 05
              </span>
              <h2 className="font-['Space_Grotesk'] font-bold text-2xl md:text-4xl text-[#F5F7FF] tracking-[0.02em] leading-tight">
                EVALUATION LAYER
              </h2>
              <p className="font-sans text-xs md:text-sm text-[#9CA9BC] leading-relaxed">
                Cross-checking generated steps against factual constraints and security criteria to guarantee predictable outcomes.
              </p>

              <div className="flex flex-col gap-2 mt-3 border border-[#5DE8FF]/20 p-4 rounded-xl bg-[#03050A]/60 backdrop-blur-sm">
                <div className="flex justify-between font-mono text-[9.5px]">
                  <span className="text-[#F5F7FF]/50">PRIVACY PROTOCOL:</span>
                  <span className="text-[#5DE8FF] font-semibold">SECURE</span>
                </div>
                <div className="h-px bg-white/10 my-1" />
                <div className="text-[11px] text-[#9CA9BC] leading-relaxed font-sans">
                  User credentials and sandbox paths are isolated locally. Context database is fully secure.
                </div>
                <div className="text-[9px] text-[#5DE8FF]/65 italic font-mono text-center mt-1">
                  Designed for secure data handling
                </div>
              </div>
            </motion.div>
          )}

          {phase === 10 && (
            <motion.div key="p10" initial="hidden" animate="visible" exit="exit" variants={blurVariants} className="bg-[#03050A]/85 border border-[#5DE8FF]/30 backdrop-blur-xl rounded-2xl p-6 md:p-8 shadow-[0_8px_32px_rgba(0,0,0,0.6)] flex flex-col gap-3">
              <span className="font-mono text-[10px] tracking-[0.25em] text-[#5DE8FF] uppercase font-semibold flex items-center gap-2">
                <span className="w-1.5 h-1.5 rounded-full bg-[#5DE8FF] animate-ping" />
                ULTRA INTELLIGENCE ACTIVATED / STAGE 06
              </span>
              <h2 className="font-['Space_Grotesk'] font-bold text-2xl md:text-4xl text-transparent bg-clip-text bg-gradient-to-r from-[#F5F7FF] via-[#5DE8FF] to-[#7C5CFF] tracking-[0.02em] leading-tight">
                GLOBAL NEURAL CASCADE
              </h2>
              <p className="font-sans text-xs md:text-sm text-[#9CA9BC] leading-relaxed">
                All computational nodes, 3D Bezier pathways, and verification systems enter peak synchronized operation.
              </p>

              <div className="flex flex-wrap gap-1.5 mt-2">
                {[
                  'NEURAL CORE', 'CONTEXT ENGINE', 'MEMORY LAYER',
                  'REASONING CLUSTER', 'RETRIEVAL', 'TOOL ORCHESTRATION',
                  'VERIFICATION', 'INFERENCE'
                ].map((tag, idx) => (
                  <motion.span
                    custom={idx}
                    variants={itemVariants}
                    initial="hidden"
                    animate="visible"
                    key={tag}
                    className="px-2 py-0.5 border border-[#5DE8FF]/20 rounded font-mono text-[8.5px] text-[#5DE8FF] bg-[#5DE8FF]/10"
                  >
                    {tag}
                  </motion.span>
                ))}
              </div>
            </motion.div>
          )}

        </AnimatePresence>
      </div>

    </div>
  );
}

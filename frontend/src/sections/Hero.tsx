import React, { useState } from 'react';
import { motion, AnimatePresence } from 'motion/react';
import AIBrain, { BrainRegion } from '../components/ai/AIBrain';
import Button from '../components/ui/Button';

interface HeroProps {
  onStart: () => void;
  onExplore: () => void;
  morphFromIntro?: boolean;
}

// HUD status panel shown alongside the brain
const REGION_LABELS: Record<BrainRegion, { process: string; mode: string; status: string }> = {
  idle:         { process: '—',            mode: 'STANDBY',   status: 'READY' },
  perception:   { process: 'PERCEPTION',   mode: 'INPUT',     status: 'ACTIVE' },
  context:      { process: 'CONTEXT',      mode: 'ANALYSIS',  status: 'ACTIVE' },
  reasoning:    { process: 'REASONING',    mode: 'INFERENCE', status: 'ACTIVE' },
  planning:     { process: 'PLANNING',     mode: 'STRATEGY',  status: 'ACTIVE' },
  tools:        { process: 'TOOL LAYER',   mode: 'EXECUTION', status: 'ACTIVE' },
  memory:       { process: 'MEMORY',       mode: 'RETRIEVAL', status: 'ACTIVE' },
  verification: { process: 'VERIFICATION', mode: 'CHECKING',  status: 'ACTIVE' },
  response:     { process: 'GENERATION',   mode: 'OUTPUT',    status: 'LIVE' },
};

export default function Hero({ onStart, onExplore, morphFromIntro = false }: HeroProps) {
  const [currentRegion, setCurrentRegion] = useState<BrainRegion>('idle');
  const hud = REGION_LABELS[currentRegion];

  return (
    <section
      id="hero"
      className="relative min-h-screen bg-[#03050A] flex items-center justify-center overflow-hidden pt-24 pb-16 px-6 md:px-10 lg:px-14 z-10"
    >
      {/* ── Ambient background light projections ── */}
      <div className="absolute top-1/4 left-1/4 w-[450px] h-[450px] bg-[#4C7DFF]/4 blur-[130px] rounded-full pointer-events-none" />
      <div className="absolute bottom-1/4 right-1/4 w-[500px] h-[500px] bg-[#7C5CFF]/4 blur-[160px] rounded-full pointer-events-none" />

      {/* ── Custom 4K video background ── */}
      <div className="absolute inset-0 pointer-events-none z-0 overflow-hidden">
        <video
          autoPlay
          muted
          loop
          playsInline
          className="w-full h-full object-cover"
          style={{ filter: 'blur(1px) saturate(0.7) brightness(0.38)', transform: 'scale(1.05)' }}
        >
          <source src="/bg-video.mp4" type="video/mp4" />
        </video>
        {/* Cinematic top/bottom gradient blend */}
        <div className="absolute inset-0 bg-gradient-to-b from-[#03050A] via-transparent to-[#03050A] opacity-80" />
        <div className="absolute inset-0 bg-gradient-to-r from-[#03050A]/65 via-transparent to-[#03050A]/65" />
      </div>

      {/* ── Main grid ── */}
      <div className="max-w-[1400px] w-full mx-auto grid grid-cols-1 lg:grid-cols-12 items-center gap-10 lg:gap-16 relative z-10">

        {/* ─── Left: Copy ─────────────────────────────────── */}
        <div className="lg:col-span-5 flex flex-col items-start gap-7 text-left">

          {/* Status badge */}
          <motion.div
            initial={morphFromIntro ? { opacity: 0, x: -50, filter: "blur(10px)" } : { opacity: 0, y: -12 }}
            animate={{ opacity: 1, x: 0, y: 0, filter: "blur(0px)" }}
            transition={{ duration: morphFromIntro ? 1.2 : 0.7, delay: morphFromIntro ? 0.2 : 0 }}
            className="flex items-center gap-2.5 px-3 py-1.5 bg-[#5DE8FF]/6 border border-[#5DE8FF]/15 rounded-full"
          >
            <span className="w-1.5 h-1.5 bg-[#5DE8FF] rounded-full animate-pulse shadow-[0_0_6px_#5DE8FF]" />
            <span className="font-['JetBrains_Mono',monospace] text-[10px] tracking-[0.28em] text-[#5DE8FF] uppercase">
              Neural Core — Operational
            </span>
          </motion.div>

          {/* Hero heading — clamp() for fluid typography */}
          <motion.h1
            initial={morphFromIntro ? { opacity: 0, x: -60, filter: "blur(12px)" } : { opacity: 0, y: 24 }}
            animate={{ opacity: 1, x: 0, y: 0, filter: "blur(0px)" }}
            transition={{ duration: morphFromIntro ? 1.4 : 0.8, delay: morphFromIntro ? 0.35 : 0.12 }}
            style={{ fontSize: 'clamp(2.5rem, 6.5vw, 5rem)' }}
            className="font-['Space_Grotesk',sans-serif] font-extrabold text-[#F5F7FF] tracking-tight leading-[1.06] max-w-[11ch]"
          >
            The{' '}
            <span
              className="text-transparent bg-clip-text"
              style={{
                backgroundImage: 'linear-gradient(120deg, #5DE8FF 0%, #4C7DFF 45%, #7C5CFF 100%)',
                filter: 'drop-shadow(0 0 18px rgba(93,232,255,0.22))',
              }}
            >
              Intelligence
            </span>{' '}
            Layer
          </motion.h1>

          {/* Subheading */}
          <motion.p
            initial={morphFromIntro ? { opacity: 0, x: -50, filter: "blur(10px)" } : { opacity: 0, y: 18 }}
            animate={{ opacity: 1, x: 0, y: 0, filter: "blur(0px)" }}
            transition={{ duration: morphFromIntro ? 1.4 : 0.8, delay: morphFromIntro ? 0.48 : 0.22 }}
            style={{ fontSize: 'clamp(1rem, 1.3vw, 1.18rem)' }}
            className="text-[#C4CEDF] font-light leading-[1.72] max-w-[44ch]"
          >
            AIDA is a modular AI system built for context, reasoning,
            and tool orchestration — not just text generation.
          </motion.p>

          {/* Architecture micro-labels */}
          <motion.div
            initial={morphFromIntro ? { opacity: 0, x: -40, filter: "blur(8px)" } : { opacity: 0, y: 12 }}
            animate={{ opacity: 1, x: 0, y: 0, filter: "blur(0px)" }}
            transition={{ duration: morphFromIntro ? 1.4 : 0.7, delay: morphFromIntro ? 0.58 : 0.32 }}
            className="flex flex-wrap gap-2"
          >
            {['Context-First', 'Modular Architecture', 'Tool-Ready', 'Verification Layer'].map((tag) => (
              <span
                key={tag}
                className="px-2.5 py-1 border border-white/8 rounded-full font-['JetBrains_Mono',monospace] text-[10px] tracking-[0.14em] text-[#9CA9BC]/70 bg-white/2"
              >
                {tag}
              </span>
            ))}
          </motion.div>

          {/* CTA buttons */}
          <motion.div
            initial={morphFromIntro ? { opacity: 0, x: -40, filter: "blur(8px)" } : { opacity: 0, y: 12 }}
            animate={{ opacity: 1, x: 0, y: 0, filter: "blur(0px)" }}
            transition={{ duration: morphFromIntro ? 1.4 : 0.7, delay: morphFromIntro ? 0.68 : 0.42 }}
            className="flex flex-row items-center gap-4 mt-2"
          >
            <Button variant="primary" onClick={onStart}>
              Start with AIDA →
            </Button>
            <Button variant="secondary" onClick={onExplore}>
              Explore AI
            </Button>
          </motion.div>

        </div>

        {/* ─── Right: AI Brain Panel ────────────────────────── */}
        <div className="lg:col-span-7 relative flex items-center justify-center">

          {/* Glassmorphic brain container */}
          <motion.div
            initial={morphFromIntro ? { opacity: 0, scale: 2.8, y: -80, filter: "blur(18px)" } : { opacity: 0, scale: 0.96 }}
            animate={{ opacity: 1, scale: 1, y: 0, filter: "blur(0px)" }}
            transition={{ 
              duration: morphFromIntro ? 1.8 : 1.0, 
              delay: morphFromIntro ? 0.1 : 0.2, 
              ease: [0.16, 1, 0.3, 1] 
            }}
            className="relative w-full"
            style={{ height: 'clamp(380px, 55vw, 580px)' }}
          >
            {/* Outer frame */}
            <div className="absolute inset-0 rounded-3xl border border-white/7 bg-white/[0.025] backdrop-blur-3xl shadow-[0_20px_60px_rgba(0,0,0,0.55)] overflow-hidden">

              {/* Scan-line overlay (subtle) */}
              <div
                className="absolute inset-0 pointer-events-none opacity-[0.015]"
                style={{
                  backgroundImage: 'repeating-linear-gradient(0deg, transparent, transparent 2px, rgba(255,255,255,0.4) 2px, rgba(255,255,255,0.4) 3px)',
                }}
              />

              {/* AIBrain canvas fills the entire panel */}
              <AIBrain autoCycle={true} className="absolute inset-0" />

              {/* ── Holographic HUD Panel — bottom-left ── */}
              <div className="absolute bottom-5 left-5 z-10 pointer-events-none select-none">
                <AnimatePresence mode="wait">
                  <motion.div
                    key={currentRegion}
                    initial={{ opacity: 0, y: 6 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0, y: -4 }}
                    transition={{ duration: 0.35 }}
                    className="flex flex-col gap-1 bg-[#03050A]/70 border border-[#5DE8FF]/12 rounded-xl px-3 py-2.5 backdrop-blur-sm"
                  >
                    <HUDRow label="PROCESS" value={hud.process} highlight={currentRegion !== 'idle'} />
                    <HUDRow label="MODE" value={hud.mode} />
                    <HUDRow label="STATUS" value={hud.status} isStatus />
                  </motion.div>
                </AnimatePresence>
              </div>

              {/* ── Holographic HUD Panel — top-right ── */}
              <div className="absolute top-5 right-5 z-10 pointer-events-none select-none">
                <div className="flex flex-col gap-1 bg-[#03050A]/60 border border-white/8 rounded-xl px-3 py-2.5 backdrop-blur-sm">
                  <HUDRow label="LATENCY" value="—" />
                  <HUDRow label="CONTEXT" value="LIVE" isStatus />
                  <HUDRow label="LAYER" value="v2.0" />
                </div>
              </div>

              {/* Corner brackets — decorative technical framing */}
              <div className="absolute top-3 left-3 w-5 h-5 border-t border-l border-[#5DE8FF]/25 rounded-tl-lg pointer-events-none" />
              <div className="absolute top-3 right-3 w-5 h-5 border-t border-r border-[#5DE8FF]/25 rounded-tr-lg pointer-events-none" />
              <div className="absolute bottom-3 left-3 w-5 h-5 border-b border-l border-[#5DE8FF]/25 rounded-bl-lg pointer-events-none" />
              <div className="absolute bottom-3 right-3 w-5 h-5 border-b border-r border-[#5DE8FF]/25 rounded-br-lg pointer-events-none" />

            </div>
          </motion.div>

          {/* Intelligence flow label below brain */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 1.2, duration: 0.8 }}
            className="absolute -bottom-8 left-0 right-0 flex justify-center gap-1.5 items-center pointer-events-none select-none"
          >
            {['PERCEPTION', '→', 'CONTEXT', '→', 'REASONING', '→', 'RESPONSE'].map((item, i) => (
              <span
                key={i}
                className={`font-['JetBrains_Mono',monospace] text-[9px] tracking-[0.14em] ${
                  item === '→' ? 'text-white/20' : 'text-[#5DE8FF]/40'
                }`}
              >
                {item}
              </span>
            ))}
          </motion.div>

        </div>
      </div>

      {/* Scroll indicator */}
      <div className="absolute bottom-8 left-1/2 -translate-x-1/2 flex flex-col items-center gap-2 text-[#9CA9BC]/35 pointer-events-none select-none">
        <span className="font-['JetBrains_Mono',monospace] text-[9px] tracking-[0.35em] uppercase">
          Scroll to explore
        </span>
        <motion.div
          animate={{ y: [0, 5, 0] }}
          transition={{ duration: 1.6, repeat: Infinity, ease: 'easeInOut' }}
          className="w-1 h-3 bg-[#5DE8FF]/25 rounded-full"
        />
      </div>

    </section>
  );
}

// ─── HUD Row ────────────────────────────────────────────────────────────────

function HUDRow({
  label,
  value,
  highlight = false,
  isStatus = false,
}: {
  label: string;
  value: string;
  highlight?: boolean;
  isStatus?: boolean;
}) {
  const statusColor =
    value === 'LIVE' || value === 'ACTIVE'
      ? '#5DE8FF'
      : value === 'READY'
      ? '#4C7DFF'
      : '#9CA9BC';

  return (
    <div className="flex items-center gap-3">
      <span className="font-['JetBrains_Mono',monospace] text-[8.5px] tracking-[0.2em] text-white/30 uppercase w-14 shrink-0">
        {label}
      </span>
      <span
        className="font-['JetBrains_Mono',monospace] text-[8.5px] tracking-[0.14em] uppercase"
        style={{
          color: isStatus
            ? statusColor
            : highlight
            ? '#5DE8FF'
            : 'rgba(245,247,255,0.6)',
        }}
      >
        {isStatus && (value === 'LIVE' || value === 'ACTIVE') && (
          <span className="inline-block w-1.5 h-1.5 rounded-full bg-current mr-1.5 animate-pulse" />
        )}
        {value}
      </span>
    </div>
  );
}

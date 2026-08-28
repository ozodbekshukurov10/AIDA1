import React, { useState } from 'react';
import { motion, AnimatePresence } from 'motion/react';
import AIOrb from './AIOrb';

interface AbilityNode {
  id: string;
  name: string;
  icon: string;
  category: string;
  description: string;
  stats: { accuracy: string; speed: string; energy: string };
}

const ABILITIES: AbilityNode[] = [
  { id: '1', name: 'LIGHTNING REASONING', icon: 'âš¡', category: 'LOGIC', description: 'Multi-step parallel logical chain validation with sub-second breakdown.', stats: { accuracy: '99.4%', speed: '12ms', energy: 'OPTIMAL' } },
  { id: '2', name: 'INFINITE MEMORY', icon: 'â™¾ï¸-', category: 'STORAGE', description: 'Context vector index matching across database knowledge chunks.', stats: { accuracy: '98.9%', speed: '8ms', energy: 'ACTIVE' } },
  { id: '3', name: 'NEURAL CASCADE', icon: 'ðŸŒŒ', category: 'COGNITION', description: 'All computational nodes enter peak synchronized parallel inference.', stats: { accuracy: '99.8%', speed: '15ms', energy: 'MAXIMUM' } },
  { id: '4', name: 'SELF-HEALING SHIELD', icon: 'ðŸ›¡ï¸-', category: 'SECURITY', description: 'Autonomous syntax repair & rate-limit resilience failover engine.', stats: { accuracy: '100.0%', speed: '4ms', energy: 'PROTECTED' } },
  { id: '5', name: 'WEB SEARCH RAG', icon: 'ðŸŒ-', category: 'RETRIEVAL', description: 'DuckDuckGo HTML query injection for real-time fresh web context.', stats: { accuracy: '97.5%', speed: '450ms', energy: 'ONLINE' } },
  { id: '6', name: 'MODEL AUTO-START', icon: 'âš™ï¸-', category: 'SYSTEM', description: 'Automatic local Ollama / LM Studio plugin auto-discovery.', stats: { accuracy: '99.1%', speed: '2ms', energy: 'READY' } },
  { id: '7', name: 'CODE GENERATOR', icon: 'ðŸ’»', category: 'DEVELOPMENT', description: 'AST-validated Python and React code synthesis with instant syntax checks.', stats: { accuracy: '98.7%', speed: '22ms', energy: 'HIGH' } },
  { id: '8', name: 'TASK DECOMPOSITION', icon: 'ðŸŽ¯', category: 'PLANNING', description: 'Decomposes complex requests into executable micro-tasks.', stats: { accuracy: '99.3%', speed: '18ms', energy: 'BALANCED' } },
  { id: '9', name: 'ASTROLOGY & PHYSICS', icon: 'ðŸ”¬', category: 'SCIENCE', description: 'Rayleigh scattering & spectrum analysis reasoning engine.', stats: { accuracy: '99.9%', speed: '14ms', energy: 'OPTIMAL' } },
  { id: '10', name: 'LIVE API GATEWAY', icon: 'ðŸ“¡', category: 'NETWORK', description: 'Token-secured REST API & WebSockets streaming endpoints.', stats: { accuracy: '100.0%', speed: '1ms', energy: 'SECURE' } },
  { id: '11', name: 'AUTONOMOUS LOOP', icon: 'ðŸš€', category: 'AUTOMATION', description: 'Self-reflection background loop for continuous model tuning.', stats: { accuracy: '98.4%', speed: '30ms', energy: 'CRUISING' } },
  { id: '12', name: 'TOKEN SECURITY', icon: 'ðŸ”-', category: 'SECURITY', description: 'Strict HTTP header X-AIDA-Security-Token authorization layer.', stats: { accuracy: '100.0%', speed: '0ms', energy: 'ENFORCED' } },
];

export default function AIHoloInterface() {
  const [activeTab, setActiveTab] = useState<'sitrep' | 'missions' | 'chief' | 'cortana' | 'codex'>('cortana');
  const [selectedAbility, setSelectedAbility] = useState<AbilityNode>(ABILITIES[0]);

  return (
    <div className="w-full min-h-[640px] bg-[#020409]/95 border border-[#5DE8FF]/20 rounded-3xl p-6 md:p-10 backdrop-blur-2xl shadow-[0_0_80px_rgba(3,5,10,0.9)] relative overflow-hidden select-none font-sans">
      
      {/* Background Holographic Grid Mesh */}
      <div className="absolute inset-0 bg-[radial-gradient(circle_at_center,rgba(93,232,255,0.06)_0,transparent_70%)] pointer-events-none" />
      <div className="absolute inset-0 bg-[linear-gradient(to_right,rgba(93,232,255,0.03)_1px,transparent_1px),linear-gradient(to_bottom,rgba(93,232,255,0.03)_1px,transparent_1px)] bg-[size:32px_32px] pointer-events-none" />

      {/* â”€â”€â”€ 1. TOP HUD NAVBAR TABS (Cortana HUD style) â”€â”€â”€ */}
      <div className="flex items-center justify-between border-b border-[#5DE8FF]/15 pb-4 mb-8 relative z-20">
        <div className="flex items-center gap-6 md:gap-12 overflow-x-auto">
          {[
            { id: 'sitrep', label: 'SITREP' },
            { id: 'missions', label: 'MISSIONS' },
            { id: 'chief', label: 'CHIEF' },
            { id: 'cortana', label: 'CORTANA AIDA' },
            { id: 'codex', label: 'CODEX' },
          ].map((tab) => {
            const isActive = activeTab === tab.id;
            return (
              <button
                key={tab.id}
                type="button"
                onClick={() => setActiveTab(tab.id as any)}
                className={`font-mono text-xs md:text-sm tracking-[0.25em] uppercase font-bold relative py-2 transition-all cursor-pointer ${
                  isActive
                    ? 'text-[#5DE8FF] filter drop-shadow-[0_0_8px_rgba(93,232,255,0.6)]'
                    : 'text-[#F5F7FF]/40 hover:text-[#F5F7FF]/80'
                }`}
              >
                {tab.label}
                {isActive && (
                  <motion.div
                    layoutId="activeTabUnderline"
                    className="absolute bottom-0 left-0 w-full h-[2px] bg-gradient-to-r from-[#5DE8FF] via-[#4C7DFF] to-[#7C5CFF] rounded-full shadow-[0_0_10px_#5DE8FF]"
                  />
                )}
              </button>
            );
          })}
        </div>

        {/* Top Right Live Telemetry Badge */}
        <div className="hidden sm:flex items-center gap-3 font-mono text-[10px] text-[#5DE8FF] bg-[#5DE8FF]/10 border border-[#5DE8FF]/20 px-3 py-1.5 rounded-full">
          <span className="w-1.5 h-1.5 rounded-full bg-[#5DE8FF] animate-ping" />
          <span>HUD v2.4 // ONLINE</span>
        </div>
      </div>

      {/* â”€â”€â”€ 2. MAIN HUD BODY LAYOUT (Left Matrix + Right 3D Orb) â”€â”€â”€ */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-center relative z-20">
        
        {/* LEFT COLUMN: Skill Matrix Grid & Ability Specs */}
        <div className="lg:col-span-6 flex flex-col gap-6">
          
          {/* Header Title */}
          <div className="flex flex-col gap-1">
            <span className="font-mono text-[10px] tracking-[0.3em] text-[#5DE8FF] uppercase font-semibold">
              TACTICAL NEURAL ABILITIES
            </span>
            <h1 className="font-['Space_Grotesk'] text-3xl md:text-4xl font-extrabold text-[#F5F7FF] tracking-wider uppercase">
              {activeTab === 'cortana' ? 'C O R T A N A' : activeTab.toUpperCase()}
            </h1>
          </div>

          {/* Circular Node Matrix Grid (4x3) */}
          <div className="grid grid-cols-4 sm:grid-cols-6 gap-3">
            {ABILITIES.map((node) => {
              const isSelected = selectedAbility.id === node.id;
              return (
                <button
                  key={node.id}
                  type="button"
                  onClick={() => setSelectedAbility(node)}
                  className={`w-12 h-12 md:w-14 md:h-14 rounded-full flex items-center justify-center text-lg md:text-xl relative transition-all duration-300 cursor-pointer ${
                    isSelected
                      ? 'bg-[#5DE8FF]/20 border-2 border-[#5DE8FF] shadow-[0_0_20px_rgba(93,232,255,0.6)] scale-110'
                      : 'bg-[#07101A]/80 border border-[#5DE8FF]/20 hover:border-[#5DE8FF]/60 hover:bg-[#5DE8FF]/10'
                  }`}
                  title={node.name}
                >
                  <span>{node.icon}</span>
                  {isSelected && (
                    <motion.div
                      layoutId="selectedNodePulse"
                      className="absolute -inset-1 rounded-full border border-[#5DE8FF]/40 animate-pulse pointer-events-none"
                    />
                  )}
                </button>
              );
            })}
          </div>

          {/* Selected Ability Description Card */}
          <AnimatePresence mode="wait">
            <motion.div
              key={selectedAbility.id}
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -10 }}
              transition={{ duration: 0.25 }}
              className="bg-[#07101A]/90 border border-[#5DE8FF]/25 rounded-2xl p-5 md:p-6 backdrop-blur-xl flex flex-col gap-3 shadow-[0_8px_32px_rgba(0,0,0,0.5)]"
            >
              <div className="flex items-center justify-between">
                <span className="font-mono text-xs text-[#5DE8FF] tracking-[0.2em] font-bold uppercase">
                  {selectedAbility.category} // #{selectedAbility.id}
                </span>
                <span className="font-mono text-[10px] text-[#9CA9BC] border border-white/10 px-2 py-0.5 rounded">
                  LATENCY: {selectedAbility.stats.speed}
                </span>
              </div>

              <h3 className="font-['Space_Grotesk'] font-bold text-xl text-[#F5F7FF] tracking-wide">
                {selectedAbility.name}
              </h3>

              <p className="text-xs md:text-sm text-[#9CA9BC] leading-relaxed font-sans font-light">
                {selectedAbility.description}
              </p>

              {/* Stats & Action Controls */}
              <div className="flex items-center justify-between border-t border-white/10 pt-4 mt-1">
                <div className="flex items-center gap-4 font-mono text-[11px]">
                  <div>
                    <span className="text-[#F5F7FF]/40">ACCURACY: </span>
                    <span className="text-[#5DE8FF] font-semibold">{selectedAbility.stats.accuracy}</span>
                  </div>
                  <div>
                    <span className="text-[#F5F7FF]/40">STATE: </span>
                    <span className="text-[#7C5CFF] font-semibold">{selectedAbility.stats.energy}</span>
                  </div>
                </div>

                <div className="flex items-center gap-3">
                  <button
                    type="button"
                    className="px-4 py-1.5 rounded-xl border border-[#5DE8FF]/40 bg-[#5DE8FF]/15 text-[#5DE8FF] font-mono text-xs font-bold tracking-wider hover:bg-[#5DE8FF]/30 hover:shadow-[0_0_15px_rgba(93,232,255,0.4)] transition-all cursor-pointer"
                  >
                    Equip Ability
                  </button>
                </div>
              </div>
            </motion.div>
          </AnimatePresence>

        </div>

        {/* RIGHT COLUMN: Holographic 3D Interactive AI Orb (Cortana Style) */}
        <div className="lg:col-span-6 flex flex-col items-center justify-center relative min-h-[420px]">
          
          {/* Holographic Glowing Hand & Orb Backdrop Frame */}
          <div className="relative w-full max-w-md h-[400px] flex items-center justify-center">
            
            {/* Background Halo Pulse rings */}
            <div className="absolute w-[280px] h-[280px] rounded-full border border-[#5DE8FF]/15 animate-ping opacity-25" />
            <div className="absolute w-[340px] h-[340px] rounded-full border border-[#4C7DFF]/10 animate-pulse" />
            
            {/* Ambient Cyan Core Glow */}
            <div className="absolute w-[220px] h-[220px] bg-gradient-to-r from-[#5DE8FF]/20 via-[#4C7DFF]/20 to-[#7C5CFF]/20 blur-3xl rounded-full pointer-events-none" />

            {/* AI Interactive Orb Component */}
            <div className="relative z-10 scale-125">
              <AIOrb state="thinking" size={240} />
            </div>

            {/* HUD Telemetry Floating Orbit Badges */}
            <div className="absolute top-4 left-2 font-mono text-[9px] text-[#5DE8FF] bg-[#03050A]/80 border border-[#5DE8FF]/20 px-2.5 py-1 rounded-md backdrop-blur-md">
              NEURAL LINKS: 1,024 ACTIVE
            </div>

            <div className="absolute bottom-6 right-2 font-mono text-[9px] text-[#7C5CFF] bg-[#03050A]/80 border border-[#7C5CFF]/20 px-2.5 py-1 rounded-md backdrop-blur-md">
              SYNAPSE FREQ: 4.8 GHz
            </div>

          </div>

        </div>

      </div>

    </div>
  );
}

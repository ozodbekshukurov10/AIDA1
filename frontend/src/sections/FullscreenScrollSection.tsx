import React, { useState } from 'react';
import { motion, AnimatePresence } from 'motion/react';
import { ArrowRight, ChevronDown, ChevronUp, Sparkles, Brain, Globe, Cpu, Zap } from 'lucide-react';

const slidesData = [
  {
    id: 'synapse',
    title: 'QUANTUM SYNAPSE MATRIX',
    tagline: '2,097,152 Token Context Capacity',
    description: 'AIDA processes multi-dimensional context windows in real-time, retrieving vector embeddings across millions of tokens with 99.8% lossless compression.',
    icon: Brain,
    image: 'https://images.unsplash.com/photo-1620712943543-bcc4688e7485?q=80&w=1600&auto=format&fit=crop',
    color: '#5DE8FF',
  },
  {
    id: 'swarm',
    title: 'AUTONOMOUS SWARM ORCHESTRATION',
    tagline: '1,024 Parallel Regional Hubs',
    description: 'Self-organizing AI agents coordinate across global infrastructure hubs, executing complex multi-step workflows, code debugging, and autonomous task execution.',
    icon: Cpu,
    image: 'https://images.unsplash.com/photo-1618005182384-a83a8bd57fbe?q=80&w=1600&auto=format&fit=crop',
    color: '#7C5CFF',
  },
  {
    id: 'healing',
    title: 'SELF-HEALING CODE ENGINE',
    tagline: 'Zero-Bug Verification Pipeline',
    description: 'Continuous static & dynamic analysis inspects runtime stack traces, auto-corrects syntax errors, and validates API contracts before deployment.',
    icon: Zap,
    image: 'https://images.unsplash.com/photo-1526374965328-7f61d4dc18c5?q=80&w=1600&auto=format&fit=crop',
    color: '#FF007F',
  },
  {
    id: 'planetary',
    title: 'PLANETARY INTELLIGENCE MESH',
    tagline: '1.2ms Global Synapse Latency',
    description: 'High-speed optical neural arcs connect Tashkent, Tokyo, London, NYC, and Sydney in a unified cognitive mesh spanning the entire globe.',
    icon: Globe,
    image: 'https://images.unsplash.com/photo-1451187580459-43490279c0fa?q=80&w=1600&auto=format&fit=crop',
    color: '#00F2FF',
  },
  {
    id: 'symbiosis',
    title: 'HUMAN-AI SYMBIOTIC COGNITION',
    tagline: 'The Future of Augmented Intelligence',
    description: 'Human creative vision and ethical intent fuse seamlessly with AIDA\'s ultra-fast computational engine, transcending single-brain limitations.',
    icon: Sparkles,
    image: 'https://images.unsplash.com/photo-1507413245164-6160d8298b31?q=80&w=1600&auto=format&fit=crop',
    color: '#5DE8FF',
  },
];

export default function FullscreenScrollSection() {
  const [currentSlide, setCurrentSlide] = useState(0);

  const nextSlide = () => {
    setCurrentSlide((prev) => (prev + 1) % slidesData.length);
  };

  const prevSlide = () => {
    setCurrentSlide((prev) => (prev - 1 + slidesData.length) % slidesData.length);
  };

  const activeSlide = slidesData[currentSlide];
  const IconComponent = activeSlide.icon;

  return (
    <section className="relative w-full min-h-screen bg-[#03050A] flex flex-col justify-between p-6 md:p-12 overflow-hidden select-none">
      
      {/* â”€â”€ Background Image & Gradient Overlay â”€â”€ */}
      <AnimatePresence mode="wait">
        <motion.div
          key={activeSlide.id}
          initial={{ opacity: 0, scale: 1.1, filter: 'blur(20px)' }}
          animate={{ opacity: 0.35, scale: 1, filter: 'blur(0px)' }}
          exit={{ opacity: 0, scale: 0.95, filter: 'blur(20px)' }}
          transition={{ duration: 1.2, ease: [0.16, 1, 0.3, 1] }}
          className="absolute inset-0 z-0 bg-cover bg-center pointer-events-none"
          style={{ backgroundImage: `url(${activeSlide.image})` }}
        />
      </AnimatePresence>

      <div className="absolute inset-0 bg-gradient-to-b from-[#03050A] via-[#03050A]/70 to-[#03050A] pointer-events-none z-0" />

      {/* â”€â”€ Top Header Controls â”€â”€ */}
      <div className="relative z-10 flex flex-wrap items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <div
            className="w-3 h-3 rounded-full animate-ping"
            style={{ backgroundColor: activeSlide.color }}
          />
          <span className="font-['Space_Grotesk'] text-xs font-bold tracking-[0.25em] text-[#F5F7FF] uppercase">
            AIDA 2.0 // KINETIC SHOWCASE
          </span>
        </div>

        {/* Slide Selector Buttons */}
        <div className="flex items-center gap-2 p-1 rounded-full bg-white/5 border border-white/10 backdrop-blur-md">
          {slidesData.map((slide, idx) => (
            <button
              key={slide.id}
              type="button"
              onClick={() => setCurrentSlide(idx)}
              className={`px-3 py-1.5 rounded-full font-['JetBrains_Mono',monospace] text-xs font-bold tracking-wider transition-all duration-300 cursor-pointer ${
                currentSlide === idx
                  ? 'bg-white text-[#03050A] shadow-[0_0_15px_rgba(255,255,255,0.4)]'
                  : 'text-[#9CA9BC] hover:text-white'
              }`}
            >
              0{idx + 1}
            </button>
          ))}
        </div>
      </div>

      {/* â”€â”€ Main Slide Content â”€â”€ */}
      <div className="relative z-10 max-w-5xl mx-auto my-auto flex flex-col gap-6 py-12">
        <AnimatePresence mode="wait">
          <motion.div
            key={activeSlide.id}
            initial={{ opacity: 0, y: 30, filter: 'blur(10px)' }}
            animate={{ opacity: 1, y: 0, filter: 'blur(0px)' }}
            exit={{ opacity: 0, y: -30, filter: 'blur(10px)' }}
            transition={{ duration: 0.8, ease: [0.16, 1, 0.3, 1] }}
            className="flex flex-col gap-6"
          >
            {/* Tag Pill */}
            <div
              className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full border w-fit backdrop-blur-md"
              style={{
                borderColor: `${activeSlide.color}40`,
                backgroundColor: `${activeSlide.color}15`,
                color: activeSlide.color,
              }}
            >
              <IconComponent className="w-4 h-4" />
              <span className="font-['JetBrains_Mono',monospace] text-xs font-bold tracking-wider uppercase">
                {activeSlide.tagline}
              </span>
            </div>

            {/* BOLD TITLE */}
            <h2 className="font-['Space_Grotesk'] text-4xl sm:text-6xl md:text-7xl font-black text-white tracking-wide uppercase leading-tight">
              {activeSlide.title}
            </h2>

            {/* Description */}
            <p className="font-sans text-base sm:text-xl text-[#C4CEDF] max-w-2xl leading-relaxed">
              {activeSlide.description}
            </p>
          </motion.div>
        </AnimatePresence>
      </div>

      {/* â”€â”€ Bottom Controls & Slide Progress Indicator â”€â”€ */}
      <div className="relative z-10 flex items-center justify-between pt-6 border-t border-white/10">
        <div className="flex items-center gap-4">
          <span className="font-['JetBrains_Mono',monospace] text-sm text-[#5DE8FF] font-bold">
            0{currentSlide + 1} / 0{slidesData.length}
          </span>
          <div className="w-32 bg-white/10 h-1.5 rounded-full overflow-hidden">
            <div
              className="h-full bg-[#5DE8FF] transition-all duration-500"
              style={{ width: `${((currentSlide + 1) / slidesData.length) * 100}%` }}
            />
          </div>
        </div>

        {/* Up / Down Navigation Buttons */}
        <div className="flex items-center gap-3">
          <button
            type="button"
            onClick={prevSlide}
            className="p-3 rounded-full border border-white/20 bg-white/5 text-white hover:bg-white/20 transition-all cursor-pointer"
            aria-label="Previous slide"
          >
            <ChevronUp className="w-5 h-5" />
          </button>

          <button
            type="button"
            onClick={nextSlide}
            className="p-3 rounded-full border border-[#5DE8FF]/40 bg-[#5DE8FF]/15 text-[#5DE8FF] hover:bg-[#5DE8FF]/30 transition-all cursor-pointer shadow-[0_0_15px_rgba(93,232,255,0.2)]"
            aria-label="Next slide"
          >
            <ChevronDown className="w-5 h-5" />
          </button>
        </div>
      </div>

    </section>
  );
}

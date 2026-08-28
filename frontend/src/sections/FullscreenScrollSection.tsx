import React, { useState, useEffect, useRef } from 'react';
import { motion, AnimatePresence } from 'motion/react';
import { ArrowLeft, ArrowUpRight, Sparkles, Brain, Globe, Cpu, Zap, X } from 'lucide-react';
import { useLanguage } from '../context/LanguageContext';

const slidesData = [
  {
    id: 'synapse',
    title: 'QUANTUM SYNAPSE MATRIX',
    tagline: '2,097,152 Token Context Capacity',
    shortDesc: 'Multi-dimensional context processing engine with 99.8% lossless vector compression.',
    fullDesc: 'AIDA processes multi-dimensional context windows in real-time, retrieving vector embeddings across millions of tokens with 99.8% lossless compression. Our synaptic matrix ensures zero information degradation across massive multi-turn conversation trajectories.',
    icon: Brain,
    image: 'https://images.unsplash.com/photo-1620712943543-bcc4688e7485?q=85&w=2000&auto=format&fit=crop',
    color: '#5DE8FF',
  },
  {
    id: 'swarm',
    title: 'AUTONOMOUS SWARM ORCHESTRATION',
    tagline: '1,024 Parallel Regional Hubs',
    shortDesc: 'Self-organizing AI agents coordinate across global infrastructure hubs.',
    fullDesc: 'Self-organizing AI agents coordinate across global infrastructure hubs, executing complex multi-step workflows, code debugging, and autonomous task execution with microsecond-level synchronization.',
    icon: Cpu,
    image: 'https://images.unsplash.com/photo-1618005182384-a83a8bd57fbe?q=85&w=2000&auto=format&fit=crop',
    color: '#7C5CFF',
  },
  {
    id: 'healing',
    title: 'SELF-HEALING CODE ENGINE',
    tagline: 'Zero-Bug Verification Pipeline',
    shortDesc: 'Continuous static & dynamic analysis inspects runtime stack traces.',
    fullDesc: 'Continuous static & dynamic analysis inspects runtime stack traces, auto-corrects syntax errors, and validates API contracts before deployment. If an execution pipeline encounters a fault, AIDA re-routes logic autonomously.',
    icon: Zap,
    image: 'https://images.unsplash.com/photo-1634017839464-5c339ebe3cb4?q=85&w=2000&auto=format&fit=crop',
    color: '#FF007F',
  },
  {
    id: 'planetary',
    title: 'PLANETARY INTELLIGENCE MESH',
    tagline: '1.2ms Global Synapse Latency',
    shortDesc: 'High-speed optical neural arcs connect Tashkent, Tokyo, London & NYC.',
    fullDesc: 'High-speed optical neural arcs connect Tashkent, Tokyo, London, NYC, and Sydney in a unified cognitive mesh spanning the entire globe, delivering instant planetary-scale intelligence.',
    icon: Globe,
    image: 'https://images.unsplash.com/photo-1451187580459-43490279c0fa?q=85&w=2000&auto=format&fit=crop',
    color: '#00F2FF',
  },
  {
    id: 'symbiosis',
    title: 'HUMAN-AI SYMBIOTIC COGNITION',
    tagline: 'The Future of Augmented Intelligence',
    shortDesc: 'Human creative vision fuses seamlessly with AIDA\'s computational engine.',
    fullDesc: 'Human creative vision and ethical intent fuse seamlessly with AIDA\'s ultra-fast computational engine, transcending single-brain limitations to create an augmented human-AI supermind.',
    icon: Sparkles,
    image: 'https://images.unsplash.com/photo-1677442136019-21780efad99a?q=85&w=2000&auto=format&fit=crop',
    color: '#5DE8FF',
  },
];

export default function FullscreenScrollSection() {
  const [currentSlide, setCurrentSlide] = useState(0);
  const [isOpen, setIsOpen] = useState(false);
  const [isAnimating, setIsAnimating] = useState(false);
  
  const { t } = useLanguage();

  const sectionRef = useRef<HTMLElement>(null);
  const currentSlideRef = useRef(currentSlide);
  const isAnimatingRef = useRef(isAnimating);

  useEffect(() => {
    currentSlideRef.current = currentSlide;
  }, [currentSlide]);

  useEffect(() => {
    isAnimatingRef.current = isAnimating;
  }, [isAnimating]);

  const activeSlide = slidesData[currentSlide];

  const changeSlide = (newIndex: number) => {
    if (isAnimatingRef.current) return;
    setIsAnimating(true);
    setCurrentSlide(newIndex);
    setTimeout(() => setIsAnimating(false), 750);
  };

  // â”€â”€ Bulletproof Scroll-Lock & Pinning Controller â”€â”€
  useEffect(() => {
    const el = sectionRef.current;
    if (!el || isOpen) return;

    let wheelCooldown = false;

    const handleWindowWheel = (e: WheelEvent) => {
      if (isOpen) return;

      const rect = el.getBoundingClientRect();
      const isInView = rect.top <= 100 && rect.bottom >= window.innerHeight - 100;

      if (!isInView) return;

      if (wheelCooldown || isAnimatingRef.current) {
        if (Math.abs(rect.top) < 200) {
          e.preventDefault();
        }
        return;
      }

      const curr = currentSlideRef.current;
      const maxIndex = slidesData.length - 1;

      if (e.deltaY > 15) {
        if (curr < maxIndex) {
          e.preventDefault();
          el.scrollIntoView({ behavior: 'smooth', block: 'start' });
          wheelCooldown = true;
          changeSlide(curr + 1);
          setTimeout(() => { wheelCooldown = false; }, 800);
        }
      } else if (e.deltaY < -15) {
        if (curr > 0) {
          e.preventDefault();
          el.scrollIntoView({ behavior: 'smooth', block: 'start' });
          wheelCooldown = true;
          changeSlide(curr - 1);
          setTimeout(() => { wheelCooldown = false; }, 800);
        }
      }
    };

    window.addEventListener('wheel', handleWindowWheel, { passive: false });

    return () => {
      window.removeEventListener('wheel', handleWindowWheel);
    };
  }, [isOpen]);

  return (
    <section
      ref={sectionRef}
      className="relative w-full h-screen bg-[#03050A] text-[#F5F7FF] overflow-hidden select-none font-sans"
    >
      
      {/* â”€â”€ 1. Fullscreen Background Image â”€â”€ */}
      <AnimatePresence mode="wait">
        <motion.div
          key={activeSlide.id}
          initial={{ opacity: 0, scale: 1.15, filter: 'blur(15px)' }}
          animate={{ opacity: 0.5, scale: 1, filter: 'blur(0px)' }}
          exit={{ opacity: 0, scale: 0.95, filter: 'blur(15px)' }}
          transition={{ duration: 0.9, ease: [0.16, 1, 0.3, 1] }}
          className="absolute inset-0 z-0 bg-cover bg-center cursor-pointer"
          style={{ backgroundImage: `url(${activeSlide.image})` }}
          onClick={() => setIsOpen(true)}
        />
      </AnimatePresence>

      <div className="absolute inset-0 bg-gradient-to-t from-[#03050A] via-transparent to-[#03050A]/70 pointer-events-none z-0" />

      {/* â”€â”€ 2. Top Bar UI Frame â”€â”€ */}
      <div className="absolute top-0 left-0 w-full p-8 md:p-12 flex items-start justify-between z-20 pointer-events-none">
        
        {/* Top Left: "+ DISCOVER MORE" */}
        <button
          type="button"
          onClick={() => setIsOpen(true)}
          className="pointer-events-auto flex items-center gap-2 text-xs font-mono font-bold tracking-[0.25em] text-[#F5F7FF] hover:text-[#5DE8FF] transition-colors cursor-pointer uppercase"
        >
          <span>{t.slides.discoverMore}</span>
        </button>

        {/* Top Right: Frame Title */}
        <div className="text-right text-xs font-mono tracking-widest text-[#9CA9BC] uppercase">
          {t.slides.engineOnline}
        </div>

      </div>

      {/* â”€â”€ 3. Bottom UI Frame â”€â”€ */}
      <div className="absolute bottom-0 left-0 w-full p-8 md:p-12 flex flex-col md:flex-row md:items-end justify-between gap-6 z-20 pointer-events-none">
        
        {/* Bottom Left Navigation Menu */}
        <div className="flex flex-col gap-2.5 pointer-events-auto">
          {slidesData.map((slide, idx) => (
            <button
              key={slide.id}
              type="button"
              onClick={() => changeSlide(idx)}
              className={`text-left font-['Space_Grotesk'] text-sm md:text-base font-bold tracking-wider uppercase transition-all duration-300 cursor-pointer ${
                currentSlide === idx
                  ? 'text-white border-b-2 border-[#5DE8FF] pb-1 pl-2'
                  : 'text-[#9CA9BC]/60 hover:text-white'
              }`}
            >
              {slide.title}
            </button>
          ))}
        </div>

        {/* Bottom Center: Scroll or Drag */}
        <div
          onClick={() => {
            if (currentSlide < slidesData.length - 1) {
              changeSlide(currentSlide + 1);
            }
          }}
          className="pointer-events-auto text-center font-['JetBrains_Mono',monospace] text-xs font-bold tracking-[0.3em] text-[#9CA9BC] hover:text-[#5DE8FF] transition-colors cursor-pointer uppercase animate-bounce"
        >
          {currentSlide === slidesData.length - 1 ? t.slides.scrollForNext : t.slides.scrollOrClick}
        </div>

        {/* Bottom Right: Slide Indicator */}
        <div className="text-right font-['JetBrains_Mono',monospace] text-xs font-bold tracking-widest text-[#5DE8FF] uppercase">
          {t.slides.slideshow} 0{currentSlide + 1} / 0{slidesData.length} â†—
        </div>

      </div>

      {/* â”€â”€ 4. Main Floating Side-Blur Content (No Background Box!) â”€â”€ */}
      <div className="absolute inset-0 flex items-center justify-center p-6 z-10 pointer-events-none">
        <AnimatePresence mode="wait">
          <motion.div
            key={activeSlide.id}
            initial={{ opacity: 0, x: -90, filter: 'blur(25px)' }}
            animate={{ opacity: 1, x: 0, filter: 'blur(0px)' }}
            exit={{ opacity: 0, x: 90, filter: 'blur(25px)' }}
            transition={{ duration: 0.9, ease: [0.16, 1, 0.3, 1] }}
            className="max-w-3xl text-center flex flex-col items-center gap-5 pointer-events-auto drop-shadow-[0_4px_30px_rgba(0,0,0,0.9)]"
          >
            <div
              className="w-14 h-14 rounded-2xl flex items-center justify-center mb-1 backdrop-blur-md border border-white/20 shadow-[0_0_25px_rgba(93,232,255,0.3)]"
              style={{ backgroundColor: `${activeSlide.color}25`, color: activeSlide.color }}
            >
              <activeSlide.icon className="w-7 h-7" />
            </div>

            <span
              className="font-['JetBrains_Mono',monospace] text-xs font-bold tracking-[0.3em] uppercase px-4 py-1 rounded-full border border-white/10 backdrop-blur-md"
              style={{ color: activeSlide.color, backgroundColor: `${activeSlide.color}15` }}
            >
              {activeSlide.tagline}
            </span>

            <h2 className="font-['Space_Grotesk'] text-4xl sm:text-6xl md:text-7xl font-black text-white tracking-wide uppercase leading-none drop-shadow-[0_0_20px_rgba(0,0,0,0.8)]">
              {activeSlide.title}
            </h2>

            <p className="text-base sm:text-lg text-[#E2E8F0] font-medium leading-relaxed max-w-xl drop-shadow-[0_2px_10px_rgba(0,0,0,0.9)]">
              {activeSlide.shortDesc}
            </p>

            <button
              type="button"
              onClick={() => setIsOpen(true)}
              className="mt-4 px-9 py-3.5 rounded-full bg-white text-[#03050A] font-['Space_Grotesk'] text-xs font-bold tracking-widest hover:bg-[#5DE8FF] hover:scale-105 transition-all duration-300 cursor-pointer uppercase shadow-[0_0_30px_rgba(255,255,255,0.4)]"
            >
              {t.slides.discoverMoreBtn}
            </button>
          </motion.div>
        </AnimatePresence>
      </div>

      {/* â”€â”€ 5. Full-Bleed Content Detail Drawer â”€â”€ */}
      <AnimatePresence>
        {isOpen && (
          <motion.div
            initial={{ opacity: 0, y: '100%' }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: '100%' }}
            transition={{ duration: 0.8, ease: [0.16, 1, 0.3, 1] }}
            className="fixed inset-0 z-50 bg-[#03050A]/95 backdrop-blur-2xl p-8 md:p-16 flex flex-col justify-between overflow-y-auto"
          >
            {/* Drawer Header */}
            <div className="flex items-center justify-between">
              <button
                type="button"
                onClick={() => setIsOpen(false)}
                className="flex items-center gap-2 text-xs font-mono font-bold tracking-widest text-[#5DE8FF] hover:text-white transition-colors cursor-pointer"
              >
                <ArrowLeft className="w-4 h-4" />
                <span>{t.slides.goBack}</span>
              </button>

              <button
                type="button"
                onClick={() => setIsOpen(false)}
                className="p-2 rounded-full border border-white/20 text-white hover:bg-white/20 transition-all cursor-pointer"
              >
                <X className="w-6 h-6" />
              </button>
            </div>

            {/* Drawer Body */}
            <div className="max-w-4xl mx-auto my-auto py-12 flex flex-col gap-8">
              <div className="flex items-center gap-3">
                <span
                  className="px-4 py-1 rounded-full font-mono text-xs font-bold tracking-wider uppercase"
                  style={{ backgroundColor: `${activeSlide.color}20`, color: activeSlide.color }}
                >
                  {activeSlide.tagline}
                </span>
              </div>

              <h1 className="font-['Space_Grotesk'] text-4xl md:text-7xl font-black text-white uppercase tracking-tight leading-none">
                {activeSlide.title}
              </h1>

              <p className="font-sans text-lg md:text-2xl text-[#C4CEDF] leading-relaxed">
                {activeSlide.fullDesc}
              </p>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mt-6">
                <div className="p-6 rounded-2xl bg-white/5 border border-white/10 flex flex-col gap-2">
                  <span className="font-mono text-xs text-[#5DE8FF] font-bold uppercase">{t.slides.swarmStatus}</span>
                  <span className="font-['Space_Grotesk'] text-2xl font-bold text-white">{t.slides.operational}</span>
                </div>
                <div className="p-6 rounded-2xl bg-white/5 border border-white/10 flex flex-col gap-2">
                  <span className="font-mono text-xs text-[#7C5CFF] font-bold uppercase">{t.slides.latencyIndex}</span>
                  <span className="font-['Space_Grotesk'] text-2xl font-bold text-white">{t.slides.fastLatency}</span>
                </div>
              </div>
            </div>

          </motion.div>
        )}
      </AnimatePresence>

    </section>
  );
}

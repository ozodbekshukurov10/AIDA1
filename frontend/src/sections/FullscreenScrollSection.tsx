import React, { useState, useEffect, useRef } from 'react';
import { motion, AnimatePresence } from 'motion/react';
import { ArrowLeft, ArrowUpRight, Sparkles, Brain, Globe, Cpu, Zap, X } from 'lucide-react';

const slidesData = [
  {
    id: 'synapse',
    title: 'QUANTUM SYNAPSE MATRIX',
    tagline: '2,097,152 Token Context Capacity',
    shortDesc: 'Multi-dimensional context processing engine with 99.8% lossless vector compression.',
    fullDesc: 'AIDA processes multi-dimensional context windows in real-time, retrieving vector embeddings across millions of tokens with 99.8% lossless compression. Our synaptic matrix ensures zero information degradation across massive multi-turn conversation trajectories.',
    icon: Brain,
    image: 'https://images.unsplash.com/photo-1620712943543-bcc4688e7485?q=80&w=1600&auto=format&fit=crop',
    color: '#5DE8FF',
  },
  {
    id: 'swarm',
    title: 'AUTONOMOUS SWARM ORCHESTRATION',
    tagline: '1,024 Parallel Regional Hubs',
    shortDesc: 'Self-organizing AI agents coordinate across global infrastructure hubs.',
    fullDesc: 'Self-organizing AI agents coordinate across global infrastructure hubs, executing complex multi-step workflows, code debugging, and autonomous task execution with microsecond-level synchronization.',
    icon: Cpu,
    image: 'https://images.unsplash.com/photo-1618005182384-a83a8bd57fbe?q=80&w=1600&auto=format&fit=crop',
    color: '#7C5CFF',
  },
  {
    id: 'healing',
    title: 'SELF-HEALING CODE ENGINE',
    tagline: 'Zero-Bug Verification Pipeline',
    shortDesc: 'Continuous static & dynamic analysis inspects runtime stack traces.',
    fullDesc: 'Continuous static & dynamic analysis inspects runtime stack traces, auto-corrects syntax errors, and validates API contracts before deployment. If an execution pipeline encounters a fault, AIDA re-routes logic autonomously.',
    icon: Zap,
    image: 'https://images.unsplash.com/photo-1526374965328-7f61d4dc18c5?q=80&w=1600&auto=format&fit=crop',
    color: '#FF007F',
  },
  {
    id: 'planetary',
    title: 'PLANETARY INTELLIGENCE MESH',
    tagline: '1.2ms Global Synapse Latency',
    shortDesc: 'High-speed optical neural arcs connect Tashkent, Tokyo, London & NYC.',
    fullDesc: 'High-speed optical neural arcs connect Tashkent, Tokyo, London, NYC, and Sydney in a unified cognitive mesh spanning the entire globe, delivering instant planetary-scale intelligence.',
    icon: Globe,
    image: 'https://images.unsplash.com/photo-1451187580459-43490279c0fa?q=80&w=1600&auto=format&fit=crop',
    color: '#00F2FF',
  },
  {
    id: 'symbiosis',
    title: 'HUMAN-AI SYMBIOTIC COGNITION',
    tagline: 'The Future of Augmented Intelligence',
    shortDesc: 'Human creative vision fuses seamlessly with AIDA\'s computational engine.',
    fullDesc: 'Human creative vision and ethical intent fuse seamlessly with AIDA\'s ultra-fast computational engine, transcending single-brain limitations to create an augmented human-AI supermind.',
    icon: Sparkles,
    image: 'https://images.unsplash.com/photo-1507413245164-6160d8298b31?q=80&w=1600&auto=format&fit=crop',
    color: '#5DE8FF',
  },
];

export default function FullscreenScrollSection() {
  const [currentSlide, setCurrentSlide] = useState(0);
  const [isOpen, setIsOpen] = useState(false);
  const [isAnimating, setIsAnimating] = useState(false);
  
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
    setTimeout(() => setIsAnimating(false), 800);
  };

  // Pinning & Locked Scroll Sequence Controller
  useEffect(() => {
    const el = sectionRef.current;
    if (!el || isOpen) return;

    let wheelCooldown = false;

    const handleWheel = (e: WheelEvent) => {
      if (wheelCooldown || isAnimatingRef.current) return;

      const curr = currentSlideRef.current;
      const maxIndex = slidesData.length - 1;

      if (e.deltaY > 20) {
        // User scrolling DOWN
        if (curr < maxIndex) {
          // Lock window scroll & advance slide
          e.preventDefault();
          wheelCooldown = true;
          changeSlide(curr + 1);
          setTimeout(() => { wheelCooldown = false; }, 850);
        }
        // If curr === maxIndex, do NOT preventDefault() -> allows normal scroll to next section!
      } else if (e.deltaY < -20) {
        // User scrolling UP
        if (curr > 0) {
          // Lock window scroll & go back slide
          e.preventDefault();
          wheelCooldown = true;
          changeSlide(curr - 1);
          setTimeout(() => { wheelCooldown = false; }, 850);
        }
        // If curr === 0, do NOT preventDefault() -> allows normal scroll up to Hero!
      }
    };

    // Attach non-passive wheel listener to allow e.preventDefault()
    el.addEventListener('wheel', handleWheel, { passive: false });

    return () => {
      el.removeEventListener('wheel', handleWheel);
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
          initial={{ opacity: 0, scale: 1.15, y: 40 }}
          animate={{ opacity: 0.45, scale: 1, y: 0 }}
          exit={{ opacity: 0, scale: 0.95, y: -40 }}
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
          <span>+ DISCOVER MORE</span>
        </button>

        {/* Top Right: Frame Title */}
        <div className="text-right text-xs font-mono tracking-widest text-[#9CA9BC] uppercase">
          AIDA 2.0 // NEURAL ENGINE ONLINE â†’
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
          {currentSlide === slidesData.length - 1 ? 'â†“ SCROLL FOR NEXT SECTION â†“' : 'â†“ SCROLL OR CLICK â†“'}
        </div>

        {/* Bottom Right: Slide Indicator */}
        <div className="text-right font-['JetBrains_Mono',monospace] text-xs font-bold tracking-widest text-[#5DE8FF] uppercase">
          SLIDESHOW 0{currentSlide + 1} / 0{slidesData.length} â†—
        </div>

      </div>

      {/* â”€â”€ 4. Main Slide Overlay Card â”€â”€ */}
      <div className="absolute inset-0 flex items-center justify-center p-6 z-10 pointer-events-none">
        <motion.div
          key={activeSlide.id}
          initial={{ opacity: 0, y: 30 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0, y: -30 }}
          transition={{ duration: 0.8, ease: [0.16, 1, 0.3, 1] }}
          className="max-w-2xl text-center flex flex-col items-center gap-4 bg-[#03050A]/70 backdrop-blur-md p-8 md:p-12 rounded-3xl border border-white/10 shadow-[0_0_50px_rgba(0,0,0,0.8)] pointer-events-auto"
        >
          <div
            className="w-12 h-12 rounded-2xl flex items-center justify-center mb-2"
            style={{ backgroundColor: `${activeSlide.color}20`, color: activeSlide.color }}
          >
            <activeSlide.icon className="w-6 h-6" />
          </div>

          <span className="font-['JetBrains_Mono',monospace] text-xs font-bold tracking-[0.25em] text-[#5DE8FF] uppercase">
            {activeSlide.tagline}
          </span>

          <h2 className="font-['Space_Grotesk'] text-3xl md:text-5xl font-black text-white tracking-wide uppercase">
            {activeSlide.title}
          </h2>

          <p className="text-sm md:text-base text-[#C4CEDF] leading-relaxed">
            {activeSlide.shortDesc}
          </p>

          <button
            type="button"
            onClick={() => setIsOpen(true)}
            className="mt-4 px-8 py-3 rounded-full bg-white text-[#03050A] font-['Space_Grotesk'] text-xs font-bold tracking-widest hover:bg-[#5DE8FF] transition-all duration-300 cursor-pointer uppercase shadow-[0_0_20px_rgba(255,255,255,0.3)]"
          >
            DISCOVER MORE â†’
          </button>
        </motion.div>
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
                <span>â†- GO BACK</span>
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
                  <span className="font-mono text-xs text-[#5DE8FF] font-bold uppercase">SWARM PIPELINE STATUS</span>
                  <span className="font-['Space_Grotesk'] text-2xl font-bold text-white">100% OPERATIONAL</span>
                </div>
                <div className="p-6 rounded-2xl bg-white/5 border border-white/10 flex flex-col gap-2">
                  <span className="font-mono text-xs text-[#7C5CFF] font-bold uppercase">LATENCY INDEX</span>
                  <span className="font-['Space_Grotesk'] text-2xl font-bold text-white">1.2ms ULTRA-FAST</span>
                </div>
              </div>
            </div>

          </motion.div>
        )}
      </AnimatePresence>

    </section>
  );
}

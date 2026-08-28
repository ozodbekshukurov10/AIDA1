import React, { useEffect, useRef } from 'react';
import gsap from 'gsap';
import { ScrollTrigger } from 'gsap/ScrollTrigger';

gsap.registerPlugin(ScrollTrigger);

const BACKGROUND_TERMS = [
  { text: "A I D A // NEURAL ENGINE", pos: "left-6 top-[15vh]", blur: "blur-[1px]" },
  { text: "QUANTUM MEMORY STREAM", pos: "right-10 top-[35vh]", blur: "blur-[2px]" },
  { text: "CYBERNETIC ATTRACTOR", pos: "left-1/4 top-[55vh]", blur: "blur-[1.5px]" },
  { text: "AUTONOMOUS REASONING CORE", pos: "right-1/3 top-[75vh]", blur: "blur-[1px]" },
  { text: "SWARM AGENT ORCHESTRATION", pos: "left-12 top-[95vh]", blur: "blur-[2px]" },
  { text: "SELF-HEALING NEURAL SHIELD", pos: "right-8 top-[115vh]", blur: "blur-[1px]" },
  { text: "CONTEXT-FIRST MEMORY VECTOR", pos: "left-1/3 top-[135vh]", blur: "blur-[2px]" },
  { text: "A I D A   2 . 0   M A T R I X", pos: "right-1/4 top-[155vh]", blur: "blur-[0.8px]" },
];

export default function BackgroundScrollTextMotion() {
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const container = containerRef.current;
    if (!container) return;

    const elements = container.querySelectorAll('.bg-scroll-term');

    elements.forEach((el, idx) => {
      const direction = idx % 2 === 0 ? 1 : -1;

      gsap.fromTo(
        el,
        {
          x: direction * 80,
          opacity: 0.15,
        },
        {
          x: direction * -120,
          opacity: 0.45,
          ease: 'none',
          scrollTrigger: {
            trigger: el,
            start: 'top bottom',
            end: 'bottom top',
            scrub: 1.2,
          },
        }
      );
    });

    return () => {
      ScrollTrigger.getAll().forEach((st) => st.kill());
    };
  }, []);

  return (
    <div
      ref={containerRef}
      className="absolute inset-0 w-full h-full pointer-events-none z-0 overflow-hidden select-none font-['JetBrains_Mono',monospace]"
    >
      {BACKGROUND_TERMS.map((item, index) => (
        <div
          key={index}
          className={`bg-scroll-term absolute ${item.pos} ${item.blur} text-[#5DE8FF]/20 text-xs md:text-sm tracking-[0.35em] uppercase font-bold whitespace-nowrap`}
        >
          {item.text}
        </div>
      ))}
    </div>
  );
}

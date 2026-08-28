import React, { useEffect, useRef } from 'react';
import gsap from 'gsap';
import { ScrollTrigger } from 'gsap/ScrollTrigger';
import Lenis from 'lenis';
import Splitting from 'splitting';
import 'splitting/dist/splitting.css';
import '../styles/shape-morph.css';

gsap.registerPlugin(ScrollTrigger);

export default function OnScrollShapeMorphSection() {
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!containerRef.current) return;

    // 1. Initialize Lenis Smooth Scroll
    const lenis = new Lenis({
      lerp: 0.1,
      smoothWheel: true,
    });

    lenis.on('scroll', () => ScrollTrigger.update());

    let animationFrameId: number;
    const scrollFn = (time: number) => {
      lenis.raf(time);
      animationFrameId = requestAnimationFrame(scrollFn);
    };
    animationFrameId = requestAnimationFrame(scrollFn);

    // Helper: Animation Defaults setup
    const setupAnimationDefaults = (itemElement: Element, options: any = {}) => {
      const defaults = {
        clipPaths: {
          step1: {
            initial: 'polygon(0% 0%, 100% 0%, 100% 100%, 0% 100%)',
            final: 'polygon(50% 0%, 50% 50%, 50% 50%, 50% 100%)',
          },
          step2: {
            initial: 'polygon(50% 50%, 50% 0%, 50% 100%, 50% 50%)',
            final: 'polygon(0% 0%, 100% 0%, 100% 100%, 0% 100%)',
          },
        },
        scrollTrigger: {
          trigger: itemElement,
          start: 'top 75%',
          end: 'bottom 25%',
          scrub: 0.8,
        },
        perspective: false,
      };

      if (options && options.scrollTrigger) {
        defaults.scrollTrigger = {
          ...defaults.scrollTrigger,
          ...options.scrollTrigger,
        };
      }

      return {
        ...defaults,
        ...options,
        scrollTrigger: defaults.scrollTrigger,
      };
    };

    // Helper: Prepare text spans for splitting safely
    const prepareTextForAnimation = (itemElement: Element) => {
      const textSpans = itemElement.querySelectorAll('.content__text > span:not(.content__text-tiny)');
      if (!textSpans || textSpans.length === 0) return [];
      
      try {
        Splitting({ target: Array.from(textSpans) as any });
      } catch (err) {
        console.warn('Splitting warning:', err);
      }

      const charsArray = Array.from(textSpans).map((span) =>
        Array.from(span.querySelectorAll('.char'))
      );

      charsArray.forEach((charArray) => {
        if (charArray.length > 0) {
          gsap.set(charArray, { opacity: 0.35, y: 15, filter: 'blur(3px)' });
        }
      });

      return charsArray;
    };

    // â”€â”€ FX 1 â”€â”€
    const fx1 = (itemElement: Element, options: any) => {
      const settings = setupAnimationDefaults(itemElement, options);
      const imageElement = itemElement.querySelector('.content__img') as HTMLElement;
      const innerElements = imageElement?.querySelectorAll('.content__img-inner');
      if (!imageElement || !innerElements || innerElements.length < 2) return;
      const charsArray = prepareTextForAnimation(itemElement);

      const tl = gsap.timeline({
        defaults: { ease: 'none' },
        onStart: () => {
          if (settings.perspective) gsap.set(imageElement, { perspective: settings.perspective });
        },
        scrollTrigger: settings.scrollTrigger,
      })
        .fromTo(
          imageElement,
          { filter: 'brightness(100%)', 'clip-path': settings.clipPaths.step1.initial },
          { ease: 'sine.in', filter: 'brightness(250%)', 'clip-path': settings.clipPaths.step1.final },
          0
        )
        .to(innerElements[0], { ease: 'sine.in', rotationY: -30, scale: 1.25 }, 0)
        .add(() => {
          innerElements[0].classList.toggle('content__img-inner--hidden');
          innerElements[1].classList.toggle('content__img-inner--hidden');
        })
        .to(imageElement, {
          startAt: { 'clip-path': settings.clipPaths.step2.initial },
          'clip-path': settings.clipPaths.step2.final,
          filter: 'brightness(100%)',
        })
        .to(
          innerElements[1],
          { startAt: { rotationY: 30, scale: 1.25 }, rotationY: 0, scale: 1 },
          '<'
        );

      charsArray.forEach((charArray) => {
        if (charArray.length > 0) {
          tl.to(
            charArray,
            {
              opacity: 1,
              y: 0,
              filter: 'blur(0px)',
              stagger: 0.03,
            },
            0.1
          );
        }
      });
    };

    // â”€â”€ FX 2 â”€â”€
    const fx2 = (itemElement: Element, options: any) => {
      const settings = setupAnimationDefaults(itemElement, options);
      const imageElement = itemElement.querySelector('.content__img') as HTMLElement;
      const innerElements = imageElement?.querySelectorAll('.content__img-inner');
      if (!imageElement || !innerElements || innerElements.length < 2) return;
      const charsArray = prepareTextForAnimation(itemElement);

      const tl = gsap.timeline({
        defaults: { ease: 'none' },
        onStart: () => {
          if (settings.perspective) gsap.set([imageElement, itemElement], { perspective: settings.perspective });
        },
        scrollTrigger: settings.scrollTrigger,
      })
        .fromTo(
          imageElement,
          { filter: 'brightness(100%)', 'clip-path': settings.clipPaths.step1.initial },
          { ease: 'none', filter: 'brightness(300%)', 'clip-path': settings.clipPaths.step1.final },
          0
        )
        .to(innerElements[0], { ease: 'none', rotationX: 30, scale: 1.25 }, 0)
        .add(() => {
          innerElements[0].classList.toggle('content__img-inner--hidden');
          innerElements[1].classList.toggle('content__img-inner--hidden');
        })
        .to(imageElement, {
          startAt: { 'clip-path': settings.clipPaths.step2.initial },
          'clip-path': settings.clipPaths.step2.final,
          filter: 'brightness(100%)',
        })
        .to(
          innerElements[1],
          { startAt: { rotationX: -30, scale: 1.25 }, rotationX: 0, scale: 1 },
          '<'
        );

      charsArray.forEach((charArray) => {
        if (charArray.length > 0) {
          tl.to(
            charArray,
            {
              opacity: 1,
              y: 0,
              filter: 'blur(0px)',
              stagger: 0.03,
            },
            0.1
          );
        }
      });
    };

    // â”€â”€ FX 3 â”€â”€
    const fx3 = (itemElement: Element, options: any) => {
      const settings = setupAnimationDefaults(itemElement, options);
      const imageElement = itemElement.querySelector('.content__img') as HTMLElement;
      const innerElements = imageElement?.querySelectorAll('.content__img-inner');
      if (!imageElement || !innerElements || innerElements.length < 2) return;
      const charsArray = prepareTextForAnimation(itemElement);

      const tl = gsap.timeline({
        defaults: { ease: 'none' },
        onStart: () => {
          if (settings.perspective) gsap.set(imageElement, { perspective: settings.perspective });
        },
        scrollTrigger: settings.scrollTrigger,
      })
        .fromTo(
          imageElement,
          { filter: 'brightness(100%)', 'clip-path': settings.clipPaths.step1.initial },
          { ease: 'power2.in', filter: 'brightness(350%)', 'clip-path': settings.clipPaths.step1.final },
          0
        )
        .to(innerElements[0], { ease: 'power2.in', scale: 1.5, rotationZ: 10 }, 0)
        .add(() => {
          innerElements[0].classList.toggle('content__img-inner--hidden');
          innerElements[1].classList.toggle('content__img-inner--hidden');
        })
        .to(imageElement, {
          startAt: { 'clip-path': settings.clipPaths.step2.initial },
          'clip-path': settings.clipPaths.step2.final,
          filter: 'brightness(100%)',
        })
        .to(
          innerElements[1],
          { startAt: { scale: 1.5, rotationZ: -10 }, scale: 1, rotationZ: 0 },
          '<'
        );

      charsArray.forEach((charArray) => {
        if (charArray.length > 0) {
          tl.to(
            charArray,
            {
              opacity: 1,
              y: 0,
              filter: 'blur(0px)',
              stagger: 0.03,
            },
            0.1
          );
        }
      });
    };

    // â”€â”€ FX 4 â”€â”€
    const fx4 = (itemElement: Element, options: any) => {
      const settings = setupAnimationDefaults(itemElement, options);
      const imageElement = itemElement.querySelector('.content__img') as HTMLElement;
      const innerElements = imageElement?.querySelectorAll('.content__img-inner');
      if (!imageElement || !innerElements || innerElements.length < 2) return;
      const charsArray = prepareTextForAnimation(itemElement);

      const tl = gsap.timeline({
        defaults: { ease: 'none' },
        scrollTrigger: settings.scrollTrigger,
      })
        .fromTo(
          imageElement,
          { filter: 'brightness(100%)', 'clip-path': settings.clipPaths.step1.initial },
          { ease: 'sine.inOut', filter: 'brightness(250%)', 'clip-path': settings.clipPaths.step1.final },
          0
        )
        .to(innerElements[0], { ease: 'sine.inOut', scale: 1.25, xPercent: -15 }, 0)
        .add(() => {
          innerElements[0].classList.toggle('content__img-inner--hidden');
          innerElements[1].classList.toggle('content__img-inner--hidden');
        })
        .to(imageElement, {
          startAt: { 'clip-path': settings.clipPaths.step2.initial },
          'clip-path': settings.clipPaths.step2.final,
          filter: 'brightness(100%)',
        })
        .to(
          innerElements[1],
          { startAt: { scale: 1.25, xPercent: 15 }, scale: 1, xPercent: 0 },
          '<'
        );

      charsArray.forEach((charArray) => {
        if (charArray.length > 0) {
          tl.to(
            charArray,
            {
              opacity: 1,
              y: 0,
              filter: 'blur(0px)',
              stagger: 0.02,
            },
            0.1
          );
        }
      });
    };

    // â”€â”€ FX 5 â”€â”€
    const fx5 = (itemElement: Element, options: any) => {
      const settings = setupAnimationDefaults(itemElement, options);
      const imageElement = itemElement.querySelector('.content__img') as HTMLElement;
      const innerElements = imageElement?.querySelectorAll('.content__img-inner');
      if (!imageElement || !innerElements || innerElements.length < 2) return;
      const charsArray = prepareTextForAnimation(itemElement);

      const tl = gsap.timeline({
        defaults: { ease: 'none' },
        scrollTrigger: settings.scrollTrigger,
      })
        .fromTo(
          imageElement,
          { filter: 'brightness(100%)', 'clip-path': settings.clipPaths.step1.initial },
          { ease: 'power1.inOut', filter: 'brightness(280%)', 'clip-path': settings.clipPaths.step1.final },
          0
        )
        .to(innerElements[0], { ease: 'power1.inOut', scale: 1.35, yPercent: -20 }, 0)
        .add(() => {
          innerElements[0].classList.toggle('content__img-inner--hidden');
          innerElements[1].classList.toggle('content__img-inner--hidden');
        })
        .to(imageElement, {
          startAt: { 'clip-path': settings.clipPaths.step2.initial },
          'clip-path': settings.clipPaths.step2.final,
          filter: 'brightness(100%)',
        })
        .to(
          innerElements[1],
          { startAt: { scale: 1.35, yPercent: 20 }, scale: 1, yPercent: 0 },
          '<'
        );

      charsArray.forEach((charArray) => {
        if (charArray.length > 0) {
          tl.to(
            charArray,
            {
              opacity: 1,
              y: 0,
              filter: 'blur(0px)',
              stagger: 0.03,
            },
            0.1
          );
        }
      });
    };

    // â”€â”€ FX 6 â”€â”€
    const fx6 = (itemElement: Element, options: any) => {
      const settings = setupAnimationDefaults(itemElement, options);
      const imageElement = itemElement.querySelector('.content__img') as HTMLElement;
      const innerElements = imageElement?.querySelectorAll('.content__img-inner');
      if (!imageElement || !innerElements || innerElements.length < 2) return;
      const charsArray = prepareTextForAnimation(itemElement);

      const tl = gsap.timeline({
        defaults: { ease: 'none' },
        scrollTrigger: settings.scrollTrigger,
      })
        .fromTo(
          imageElement,
          { filter: 'brightness(100%)', 'clip-path': settings.clipPaths.step1.initial },
          { ease: 'sine.inOut', filter: 'brightness(300%)', 'clip-path': settings.clipPaths.step1.final },
          0
        )
        .to(innerElements[0], { ease: 'sine.inOut', scale: 1.3, rotationZ: 8 }, 0)
        .add(() => {
          innerElements[0].classList.toggle('content__img-inner--hidden');
          innerElements[1].classList.toggle('content__img-inner--hidden');
        })
        .to(imageElement, {
          startAt: { 'clip-path': settings.clipPaths.step2.initial },
          'clip-path': settings.clipPaths.step2.final,
          filter: 'brightness(100%)',
        })
        .to(
          innerElements[1],
          { startAt: { scale: 1.3, rotationZ: -8 }, scale: 1, rotationZ: 0 },
          '<'
        );

      charsArray.forEach((charArray) => {
        if (charArray.length > 0) {
          tl.to(
            charArray,
            {
              opacity: 1,
              y: 0,
              filter: 'blur(0px)',
              stagger: 0.03,
            },
            0.1
          );
        }
      });
    };

    // Items array mapping
    const items = [
      {
        id: '#item-1',
        animationProfile: fx1,
        options: {
          clipPaths: {
            step1: { initial: 'polygon(0% 0%, 100% 0%, 100% 100%, 0% 100%)', final: 'polygon(50% 0%, 50% 50%, 50% 50%, 50% 100%)' },
            step2: { initial: 'polygon(50% 50%, 50% 0%, 50% 100%, 50% 50%)', final: 'polygon(0% 0%, 100% 0%, 100% 100%, 0% 100%)' },
          },
          perspective: 1000,
        },
      },
      {
        id: '#item-2',
        animationProfile: fx2,
        options: {
          clipPaths: {
            step1: { initial: 'polygon(0% 0%, 100% 0%, 100% 100%, 0% 100%)', final: 'polygon(0% 50%, 100% 50%, 100% 50%, 0% 50%)' },
            step2: { initial: 'polygon(0% 50%, 0% 0%, 100% 0%, 100% 50%)', final: 'polygon(0% 0%, 100% 0%, 100% 100%, 0% 100%)' },
          },
          perspective: 800,
        },
      },
      {
        id: '#item-3',
        animationProfile: fx3,
        options: {
          clipPaths: {
            step1: { initial: 'polygon(0% 0%, 100% 0%, 100% 100%, 0% 100%)', final: 'polygon(30% 30%, 70% 30%, 70% 70%, 30% 70%)' },
            step2: { initial: 'polygon(30% 30%, 70% 30%, 70% 70%, 30% 70%)', final: 'polygon(0% 0%, 100% 0%, 100% 100%, 0% 100%)' },
          },
          perspective: 1200,
        },
      },
      {
        id: '#item-4',
        animationProfile: fx4,
        options: {
          clipPaths: {
            step1: { initial: 'polygon(0% 0%, 100% 0%, 100% 100%, 0% 100%)', final: 'polygon(50% 0%, 100% 50%, 50% 100%, 0% 50%)' },
            step2: { initial: 'polygon(50% 0%, 100% 50%, 50% 100%, 0% 50%)', final: 'polygon(0% 0%, 100% 0%, 100% 100%, 0% 100%)' },
          },
        },
      },
      {
        id: '#item-5',
        animationProfile: fx5,
        options: {
          clipPaths: {
            step1: { initial: 'polygon(0% 0%, 100% 0%, 100% 100%, 0% 100%)', final: 'polygon(0% 0%, 50% 50%, 100% 0%, 50% 100%)' },
            step2: { initial: 'polygon(0% 0%, 50% 50%, 100% 0%, 50% 100%)', final: 'polygon(0% 0%, 100% 0%, 100% 100%, 0% 100%)' },
          },
        },
      },
      {
        id: '#item-6',
        animationProfile: fx6,
        options: {
          clipPaths: {
            step1: { initial: 'polygon(0% 0%, 100% 0%, 100% 100%, 0% 100%)', final: 'polygon(50% 0%, 50% 50%, 50% 50%, 50% 100%)' },
            step2: { initial: 'polygon(50% 50%, 50% 0%, 50% 100%, 50% 50%)', final: 'polygon(0% 0%, 100% 0%, 100% 100%, 0% 100%)' },
          },
          perspective: 1000,
        },
      },
    ];

    items.forEach((item) => {
      const el = containerRef.current?.querySelector(item.id);
      if (el && item.animationProfile) {
        item.animationProfile(el, item.options);
      }
    });

    setTimeout(() => {
      ScrollTrigger.refresh();
    }, 400);

    return () => {
      cancelAnimationFrame(animationFrameId);
      lenis.destroy();
      ScrollTrigger.getAll().forEach((trigger) => trigger.kill());
    };
  }, []);

  return (
    <section ref={containerRef} className="relative py-28 px-4 bg-[#03050A] overflow-hidden z-10 font-sans">
      
      {/* Background Soft Glow blobs */}
      <div className="absolute top-1/4 left-1/2 -translate-x-1/2 w-[700px] h-[700px] bg-[#5DE8FF]/5 blur-[160px] rounded-full pointer-events-none" />
      <div className="absolute bottom-10 right-10 w-[550px] h-[550px] bg-[#7C5CFF]/5 blur-[140px] rounded-full pointer-events-none" />

      {/* Section Header */}
      <div className="flex flex-col items-center text-center gap-3 max-w-2xl mx-auto mb-20">
        <span className="font-['JetBrains_Mono',monospace] text-xs tracking-[0.35em] text-[#5DE8FF] uppercase font-bold">
          3D Kinetic Shape Morphing
        </span>
        <h2 className="font-['Space_Grotesk',sans-serif] text-3xl sm:text-5xl font-extrabold text-[#F5F7FF] tracking-tight leading-tight">
          AIDA <span className="text-transparent bg-clip-text bg-gradient-to-r from-[#5DE8FF] via-[#4C7DFF] to-[#7C5CFF]">Cognitive Architecture</span>
        </h2>
        <p className="text-xs md:text-sm text-[#9CA9BC] font-light leading-relaxed">
          Scroll down to explore how AIDA's neural layers dynamically morph & synthesize logic.
        </p>
      </div>

      {/* Shape Morphing Items Container */}
      <div className="content-wrap max-w-6xl mx-auto flex flex-col gap-32">
        
        {/* ITEM 1: Context-First Reasoning */}
        <div id="item-1" className="content">
          <div className="content__img-wrap">
            <div className="content__img content__img--1">
              <div className="content__img-inner" style={{ backgroundImage: 'url(https://images.unsplash.com/photo-1618005182384-a83a8bd57fbe?w=1600&q=85&fit=crop)' }} />
              <div className="content__img-inner content__img-inner--hidden" style={{ backgroundImage: 'url(https://images.unsplash.com/photo-1620712943543-bcc4688e7485?w=1600&q=85&fit=crop)' }} />
            </div>
          </div>
          <p className="content__text content__text--center content__text--large font-['Space_Grotesk'] text-[#F5F7FF]">
            <span>CONTEXT-FIRST REASONING</span>
            <span>MULTI-STEP VALIDATION</span>
          </p>
        </div>

        {/* ITEM 2: Autonomous Self-Healing */}
        <div id="item-2" className="content">
          <div className="content__img-wrap">
            <div className="content__img content__img--1">
              <div className="content__img-inner" style={{ backgroundImage: 'url(https://images.unsplash.com/photo-1634017839464-5c339ebe3cb4?w=1600&q=85&fit=crop)' }} />
              <div className="content__img-inner content__img-inner--hidden" style={{ backgroundImage: 'url(https://images.unsplash.com/photo-1614741118887-7a4ee193a5fa?w=1600&q=85&fit=crop)' }} />
            </div>
          </div>
          <p className="content__text content__text--left font-['Space_Grotesk'] text-[#5DE8FF]">
            <span>AUTONOMOUS SELF-HEALING</span>
            <span>RESILIENCE FAILOVER ENGINE</span>
          </p>
        </div>

        {/* ITEM 3: Web Search RAG Retrieval */}
        <div id="item-3" className="content">
          <div className="content__img-wrap">
            <div className="content__img content__img--2">
              <div className="content__img-inner" style={{ backgroundImage: 'url(https://images.unsplash.com/photo-1635070041078-e363dbe005cb?w=1600&q=85&fit=crop)' }} />
              <div className="content__img-inner content__img-inner--hidden" style={{ backgroundImage: 'url(https://images.unsplash.com/photo-1677442136019-21780efad99a?w=1600&q=85&fit=crop)' }} />
            </div>
          </div>
          <p className="content__text content__text--left font-['Space_Grotesk'] text-[#F5F7FF]">
            <span>WEB SEARCH RAG</span>
            <span>REAL-TIME KNOWLEDGE</span>
            <span className="content__text-tiny font-['Inter'] text-[#9CA9BC]">
              AIDA dynamically ingests real-time web search results for complex tasks, augmenting prompt context before inference execution.
            </span>
          </p>
        </div>

        {/* ITEM 4: Synaptic Task Decomposition */}
        <div id="item-4" className="content">
          <div className="content__img-wrap">
            <div className="content__img content__img--4">
              <div className="content__img-inner" style={{ backgroundImage: 'url(https://images.unsplash.com/photo-1620712943543-bcc4688e7485?w=1600&q=85&fit=crop)' }} />
              <div className="content__img-inner content__img-inner--hidden" style={{ backgroundImage: 'url(https://images.unsplash.com/photo-1634017839464-5c339ebe3cb4?w=1600&q=85&fit=crop)' }} />
            </div>
          </div>
          <p className="content__text content__text--center font-['Space_Grotesk'] text-[#7C5CFF]">
            <span>TASK DECOMPOSITION</span>
            <span>WORKFLOW GRAPH ORCHESTRATION</span>
          </p>
        </div>

        {/* ITEM 5: Infinite Memory Vector Store */}
        <div id="item-5" className="content">
          <div className="content__img-wrap">
            <div className="content__img content__img--5">
              <div className="content__img-inner" style={{ backgroundImage: 'url(https://images.unsplash.com/photo-1614741118887-7a4ee193a5fa?w=1600&q=85&fit=crop)' }} />
              <div className="content__img-inner content__img-inner--hidden" style={{ backgroundImage: 'url(https://images.unsplash.com/photo-1635070041078-e363dbe005cb?w=1600&q=85&fit=crop)' }} />
            </div>
          </div>
          <p className="content__text content__text--left font-['Space_Grotesk'] text-[#5DE8FF]">
            <span>INFINITE VECTOR STORE</span>
            <span>SIMILARITY INDEX MATCHING</span>
          </p>
        </div>

        {/* ITEM 6: Global Neural Orchestration */}
        <div id="item-6" className="content">
          <div className="content__img-wrap">
            <div className="content__img content__img--6">
              <div className="content__img-inner" style={{ backgroundImage: 'url(https://images.unsplash.com/photo-1677442136019-21780efad99a?w=1600&q=85&fit=crop)' }} />
              <div className="content__img-inner content__img-inner--hidden" style={{ backgroundImage: 'url(https://images.unsplash.com/photo-1618005182384-a83a8bd57fbe?w=1600&q=85&fit=crop)' }} />
            </div>
          </div>
          <p className="content__text content__text--center font-['Space_Grotesk'] text-[#F5F7FF]">
            <span>NEURAL SWARM COLLABORATION</span>
            <span>AIDA 2.0 OPERATIONAL</span>
          </p>
        </div>

      </div>

    </section>
  );
}

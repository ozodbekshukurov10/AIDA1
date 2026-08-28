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
          start: 'top 60%',
          end: '+=60%',
          scrub: true,
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

    // Helper: Prepare text spans for splitting
    const prepareTextForAnimation = (itemElement: Element) => {
      const textSpans = itemElement.querySelectorAll('.content__text > span');
      Splitting({ target: textSpans as any });
      const charsArray = Array.from(textSpans).map((span) =>
        Array.from(span.querySelectorAll('.char'))
      );
      charsArray.forEach((charArray) => {
        gsap.set(charArray, { opacity: 0 });
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
          { ease: 'sine.in', filter: 'brightness(400%)', 'clip-path': settings.clipPaths.step1.final },
          0
        )
        .to(innerElements[0], { ease: 'sine.in', rotationY: -40, scale: 1.4 }, 0)
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
          { startAt: { rotationY: 40, scale: 1.4 }, rotationY: 0, scale: 1 },
          '<'
        )
        .addLabel('texts', '<-=0.3');

      charsArray.forEach((charArray, index) => {
        const staggerDirection = index % 2 === 0 ? 1 : -1;
        tl.to(
          charArray,
          {
            startAt: { opacity: 1, scale: 0.2 },
            opacity: 1,
            scale: 1,
            yPercent: -staggerDirection * 40,
            stagger: staggerDirection * 0.04,
          },
          'texts'
        );
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
          { filter: 'brightness(100%) hue-rotate(0deg)', 'clip-path': settings.clipPaths.step1.initial },
          { filter: 'brightness(400%) hue-rotate(90deg)', 'clip-path': settings.clipPaths.step1.final },
          0
        )
        .to(innerElements[0], { rotationZ: -5, scaleX: 1.8 }, 0)
        .add(() => {
          innerElements[0].classList.toggle('content__img-inner--hidden');
          innerElements[1].classList.toggle('content__img-inner--hidden');
        })
        .to(imageElement, {
          startAt: { 'clip-path': settings.clipPaths.step2.initial },
          'clip-path': settings.clipPaths.step2.final,
          filter: 'brightness(100%) hue-rotate(0deg)',
        })
        .to(innerElements[1], { startAt: { rotationZ: 5, scaleX: 1.8 }, rotationZ: 0, scaleX: 1 }, '<')
        .addLabel('texts', '<-=0.3');

      charsArray.forEach((charArray, index) => {
        const staggerDirection = index % 2 === 0 ? 1 : -1;
        tl.to(charArray, { duration: 0.1, opacity: 1, stagger: staggerDirection * 0.04 }, 'texts');
      });
    };

    // â”€â”€ FX 3 â”€â”€
    const fx3 = (itemElement: Element, options: any) => {
      const settings = setupAnimationDefaults(itemElement, options);
      const imageElement = itemElement.querySelector('.content__img') as HTMLElement;
      const innerElements = imageElement?.querySelectorAll('.content__img-inner');
      const text = itemElement.querySelector('.content__text');
      if (!imageElement || !innerElements || innerElements.length < 2) return;

      gsap.timeline({
        defaults: { ease: 'none' },
        onStart: () => {
          if (settings.perspective) gsap.set([imageElement, itemElement], { perspective: settings.perspective });
        },
        scrollTrigger: settings.scrollTrigger,
      })
        .fromTo(
          imageElement,
          { scale: 0.3, filter: 'brightness(100%)', 'clip-path': settings.clipPaths.step1.initial },
          { ease: 'sine', rotationX: -35, rotationY: 35, filter: 'brightness(60%)', scale: 0.7, 'clip-path': settings.clipPaths.step1.final },
          0
        )
        .to(innerElements[0], { ease: 'sine', skewY: 10, scaleY: 1.2 }, 0)
        .add(() => {
          innerElements[0].classList.toggle('content__img-inner--hidden');
          innerElements[1].classList.toggle('content__img-inner--hidden');
        }, '>')
        .to(imageElement, {
          ease: 'sine.in',
          startAt: { 'clip-path': settings.clipPaths.step2.initial },
          'clip-path': settings.clipPaths.step2.final,
          filter: 'brightness(100%)',
          scale: 1,
          rotationX: 0,
          rotationY: 0,
        }, '<')
        .to(innerElements[1], { ease: 'sine.in', startAt: { skewY: 10, scaleY: 2 }, skewY: 0, scaleY: 1 }, '<')
        .fromTo(text, { opacity: 0, yPercent: 40 }, { opacity: 1, yPercent: 0 }, '>');
    };

    // â”€â”€ FX 4 â”€â”€
    const fx4 = (itemElement: Element, options: any) => {
      const settings = setupAnimationDefaults(itemElement, options);
      const imageElement = itemElement.querySelector('.content__img') as HTMLElement;
      const innerElements = imageElement?.querySelectorAll('.content__img-inner');
      if (!imageElement || !innerElements || innerElements.length < 2) return;
      const charsArray = prepareTextForAnimation(itemElement);

      const tl = gsap.timeline({
        defaults: { ease: 'power1.inOut' },
        onStart: () => {
          if (settings.perspective) gsap.set([imageElement, itemElement], { perspective: settings.perspective });
        },
        scrollTrigger: settings.scrollTrigger,
      })
        .fromTo(
          imageElement,
          { filter: 'brightness(100%)', 'clip-path': settings.clipPaths.step1.initial },
          { rotationZ: 90, scale: 0.6, filter: 'brightness(300%)', 'clip-path': settings.clipPaths.step1.final },
          0
        )
        .to(innerElements[0], { rotationZ: -5, scaleX: 1.4 }, 0)
        .add(() => {
          innerElements[0].classList.toggle('content__img-inner--hidden');
          innerElements[1].classList.toggle('content__img-inner--hidden');
        })
        .to(imageElement, {
          startAt: { 'clip-path': settings.clipPaths.step1.final, rotationZ: -90 },
          'clip-path': settings.clipPaths.step2.final,
          filter: 'brightness(100%)',
          rotationZ: 0,
          scale: 1,
        })
        .to(innerElements[1], { startAt: { rotationZ: -350, scaleX: 1.4 }, rotationZ: -360, scaleX: 1 }, '<')
        .addLabel('texts', '<-=0.3');

      charsArray.forEach((charArray, index) => {
        const staggerDirection = index % 2 === 0 ? 1 : -1;
        tl.to(
          charArray,
          {
            startAt: { opacity: 1, scale: 0.2 },
            opacity: 1,
            scale: 1,
            yPercent: staggerDirection * 400,
            stagger: staggerDirection * 0.02,
          },
          'texts'
        );
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
        defaults: { ease: 'back.out(1.5)' },
        onStart: () => {
          if (settings.perspective) gsap.set([imageElement, itemElement], { perspective: settings.perspective });
        },
        scrollTrigger: settings.scrollTrigger,
      })
        .fromTo(
          imageElement,
          { filter: 'brightness(100%)', 'clip-path': settings.clipPaths.step1.initial },
          { ease: 'back.in(1.5)', rotationZ: 90, scale: 0.6, filter: 'brightness(300%)', 'clip-path': settings.clipPaths.step1.final },
          0
        )
        .to(innerElements[0], { ease: 'back.in(1.5)', scaleX: 1.4 }, 0)
        .add(() => {
          innerElements[0].classList.toggle('content__img-inner--hidden');
          innerElements[1].classList.toggle('content__img-inner--hidden');
        })
        .to(imageElement, {
          startAt: { 'clip-path': settings.clipPaths.step1.final, rotationZ: -90 },
          'clip-path': settings.clipPaths.step2.final,
          filter: 'brightness(100%)',
          rotationZ: 0,
          scale: 1,
        })
        .to(innerElements[1], { startAt: { scaleX: 1.4 }, scaleX: 1 }, '<')
        .addLabel('texts', '<-=0.3');

      charsArray.forEach((charArray, index) => {
        const staggerDirection = index % 2 === 0 ? 1 : -1;
        tl.fromTo(
          charArray,
          { opacity: 1, transformOrigin: `50% ${staggerDirection < 0 ? 100 : 0}%`, scaleY: 0 },
          { duration: 0.1, ease: 'none', scaleY: 1, stagger: staggerDirection * 0.02 },
          'texts'
        );
      });
    };

    // â”€â”€ FX 6 â”€â”€
    const fx6 = (itemElement: Element, options: any) => {
      const settings = setupAnimationDefaults(itemElement, options);
      const imageElement = itemElement.querySelector('.content__img') as HTMLElement;
      const inner = imageElement?.querySelector('.content__img-inner');
      if (!imageElement || !inner) return;
      const charsArray = prepareTextForAnimation(itemElement);

      const tl = gsap.timeline({
        defaults: { ease: 'power2.inOut' },
        onStart: () => {
          if (settings.perspective) gsap.set(imageElement, { perspective: settings.perspective });
        },
        scrollTrigger: settings.scrollTrigger,
      })
        .fromTo(
          imageElement,
          { scale: 0.2, filter: 'brightness(50%)', 'clip-path': settings.clipPaths.step1.initial, transformOrigin: '75% 50%' },
          { scale: 1, filter: 'brightness(100%)', 'clip-path': settings.clipPaths.step1.final },
          0
        )
        .fromTo(inner, { rotationY: 40, scale: 2 }, { rotationY: 0, scale: 1 }, 0);

      charsArray.forEach((charArray, index) => {
        const staggerDirection = index % 2 === 0 ? 1 : -1;
        tl.fromTo(
          charArray,
          { opacity: 0, scale: 1.2 },
          { opacity: 1, scale: 1, yPercent: staggerDirection * 100, stagger: staggerDirection * -0.02 },
          0
        );
      });
    };

    // â”€â”€ Apply Scroll Animation Configurations â”€â”€
    const items = [
      { id: '#item-1', animationProfile: fx1, options: { perspective: 1000 } },
      {
        id: '#item-2',
        animationProfile: fx2,
        options: {
          clipPaths: {
            step1: { initial: 'polygon(0% 0%, 100% 0%, 100% 100%, 0% 100%)', final: 'polygon(40% 50%, 60% 50%, 80% 50%, 20% 50%)' },
            step2: { initial: 'polygon(20% 50%, 80% 50%, 60% 50%, 40% 50%)', final: 'polygon(0% 0%, 100% 0%, 100% 100%, 0% 100%)' },
          },
          scrollTrigger: { start: 'center bottom', end: 'top top' },
          perspective: 500,
        },
      },
      {
        id: '#item-3',
        animationProfile: fx3,
        options: {
          clipPaths: {
            step1: { initial: 'polygon(0% 0%, 100% 0%, 100% 100%, 0% 100%)', final: 'polygon(50% 0%, 50% 50%, 50% 50%, 50% 100%)' },
            step2: { initial: 'polygon(50% 50%, 50% 0%, 50% 100%, 50% 50%)', final: 'polygon(0% 0%, 100% 0%, 100% 100%, 0% 100%)' },
          },
          scrollTrigger: { start: 'center center', end: '+=120%', pin: false },
          perspective: 400,
        },
      },
      {
        id: '#item-4',
        animationProfile: fx4,
        options: {
          clipPaths: {
            step1: { initial: 'polygon(0% 0%, 100% 0%, 100% 100%, 0% 100%)', final: 'polygon(40% 50%, 60% 50%, 80% 50%, 20% 50%)' },
            step2: { initial: 'polygon(20% 50%, 80% 50%, 60% 50%, 40% 50%)', final: 'polygon(0% 0%, 100% 0%, 100% 100%, 0% 100%)' },
          },
          scrollTrigger: { start: 'center bottom', end: 'top top-=10%' },
          perspective: 500,
        },
      },
      {
        id: '#item-5',
        animationProfile: fx5,
        options: {
          clipPaths: {
            step1: {
              initial: 'polygon(50% 0%, 80% 10%, 100% 35%, 100% 70%, 80% 90%, 50% 100%, 20% 90%, 0% 70%, 0% 35%, 20% 10%)',
              final: 'polygon(50% 50%, 50% 50%, 50% 50%, 50% 50%, 50% 50%, 50% 50%, 50% 50%, 50% 50%, 50% 50%, 50% 50%)',
            },
            step2: {
              initial: 'polygon(50% 50%, 50% 50%, 50% 50%, 50% 50%, 50% 50%, 50% 50%, 50% 50%, 50% 50%, 50% 50%, 50% 50%)',
              final: 'polygon(50% 0%, 80% 10%, 100% 35%, 100% 70%, 80% 90%, 50% 100%, 20% 90%, 0% 70%, 0% 35%, 20% 10%)',
            },
          },
          scrollTrigger: { start: 'top bottom+=20%', end: 'bottom top' },
          perspective: 500,
        },
      },
      {
        id: '#item-6',
        animationProfile: fx6,
        options: {
          clipPaths: {
            step1: { initial: 'polygon(50% 0%, 50% 50%, 50% 50%, 50% 100%)', final: 'polygon(0% 0%, 100% 0%, 100% 100%, 0% 100%)' },
          },
          scrollTrigger: { start: 'center bottom', end: '+=80%' },
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
              <div className="content__img-inner" style={{ backgroundImage: 'url(https://images.unsplash.com/photo-1618005182384-a83a8bd57fbe?w=1400&q=80)' }} />
              <div className="content__img-inner content__img-inner--hidden" style={{ backgroundImage: 'url(https://images.unsplash.com/photo-1620712943543-bcc4688e7485?w=1400&q=80)' }} />
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
              <div className="content__img-inner" style={{ backgroundImage: 'url(https://images.unsplash.com/photo-1634017839464-5c339ebe3cb4?w=1400&q=80)' }} />
              <div className="content__img-inner content__img-inner--hidden" style={{ backgroundImage: 'url(https://images.unsplash.com/photo-1614741118887-7a4ee193a5fa?w=1400&q=80)' }} />
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
              <div className="content__img-inner" style={{ backgroundImage: 'url(https://images.unsplash.com/photo-1635070041078-e363dbe005cb?w=1400&q=80)' }} />
              <div className="content__img-inner content__img-inner--hidden" style={{ backgroundImage: 'url(https://images.unsplash.com/photo-1618005182384-a83a8bd57fbe?w=1400&q=80)' }} />
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
              <div className="content__img-inner" style={{ backgroundImage: 'url(https://images.unsplash.com/photo-1620712943543-bcc4688e7485?w=1400&q=80)' }} />
              <div className="content__img-inner content__img-inner--hidden" style={{ backgroundImage: 'url(https://images.unsplash.com/photo-1634017839464-5c339ebe3cb4?w=1400&q=80)' }} />
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
              <div className="content__img-inner" style={{ backgroundImage: 'url(https://images.unsplash.com/photo-1614741118887-7a4ee193a5fa?w=1400&q=80)' }} />
              <div className="content__img-inner content__img-inner--hidden" style={{ backgroundImage: 'url(https://images.unsplash.com/photo-1635070041078-e363dbe005cb?w=1400&q=80)' }} />
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
              <div className="content__img-inner" style={{ backgroundImage: 'url(https://images.unsplash.com/photo-1618005182384-a83a8bd57fbe?w=1400&q=80)' }} />
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
